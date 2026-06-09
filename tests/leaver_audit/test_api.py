import pytest
import uuid
from unittest.mock import MagicMock
from src.verity_portal.main import app
from src.verity_portal.intake.router import get_intake_service
from src.verity_portal.intake.service import IntakeService

@pytest.fixture
def mock_intake_service():
    service = MagicMock(spec=IntakeService)
    app.dependency_overrides[get_intake_service] = lambda: service
    yield service

def test_run_leaver_mover_audit_success(client, mock_intake_service):
    hr_job_id = str(uuid.uuid4())
    access_job_id = str(uuid.uuid4())
    
    mock_intake_service.get_records.side_effect = [
        [{"employee_id": "EMP001", "hr_termination_date": "2023-10-01"}],
        [{"employee_id": "EMP001", "last_system_login": "2023-10-05"}]
    ]
    
    response = client.post(
        "/leaver-audit/leaver-mover",
        json={"hr_job_id": hr_job_id, "access_job_id": access_job_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["violations"]) == 1

def test_export_audit_results_csv(client):
    violations = [{"employee_id": "EMP001", "risk_level": "HIGH"}]
    response = client.post("/leaver-audit/export/csv", json=violations)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

def test_export_audit_results_pdf(client):
    violations = [{"employee_id": "EMP001", "risk_level": "HIGH"}]
    response = client.post("/leaver-audit/export/pdf", json=violations)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
