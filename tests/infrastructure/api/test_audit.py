import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.infrastructure.adapters.database.setup import get_db
from app.infrastructure.adapters.database.models import IntakeRecordModel

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db():
    db = MagicMock()
    yield db

def test_run_leaver_mover_audit_success(client, mock_db):
    # Override get_db dependency
    app.dependency_overrides[get_db] = lambda: mock_db
    
    hr_job_id = str(uuid.uuid4())
    access_job_id = str(uuid.uuid4())
    
    # Mock HR records
    hr_record = MagicMock(spec=IntakeRecordModel)
    hr_record.data = {"employee_id": "EMP001", "hr_termination_date": "2023-10-01"}
    
    # Mock Access records
    access_record = MagicMock(spec=IntakeRecordModel)
    access_record.data = {"employee_id": "EMP001", "last_system_login": "2023-10-05"}
    
    # Mock query behavior
    # Filter for hr_job_id returns hr_record
    # Filter for access_job_id returns access_record
    def mock_query(model):
        if model == IntakeRecordModel:
            return mock_db.query_instance
        return MagicMock()
        
    mock_db.query_instance = MagicMock()
    mock_db.query.side_effect = mock_query
    
    # This is a bit complex to mock perfectly with SQLAlchemy chain, 
    # but we'll try to simulate the result set.
    mock_db.query_instance.filter.return_value.all.side_effect = [
        [hr_record], # First call for HR
        [access_record] # Second call for Access
    ]
    
    response = client.post(
        "/audit/leaver-mover",
        json={"hr_job_id": hr_job_id, "access_job_id": access_job_id}
    )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "violations" in data
    assert len(data["violations"]) == 1
    assert data["violations"][0]["employee_id"] == "EMP001"

def test_export_audit_results_csv(client):
    violations = [{"employee_id": "EMP001", "risk_level": "HIGH"}]
    
    response = client.post("/audit/export/csv", json=violations)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "employee_id" in response.text

def test_export_audit_results_pdf(client):
    violations = [{"employee_id": "EMP001", "risk_level": "HIGH"}]
    
    response = client.post("/audit/export/pdf", json=violations)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
