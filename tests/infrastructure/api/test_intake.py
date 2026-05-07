import pytest
import uuid
import io
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from app.domain.services.file_manager import FileManager
from app.infrastructure.api.routes.intake import get_file_manager
from unittest.mock import AsyncMock, patch

client = TestClient(app)

@pytest.fixture
def mock_file_manager():
    manager = AsyncMock(spec=FileManager)
    app.dependency_overrides[get_file_manager] = lambda: manager
    yield manager
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_upload_file_success(mock_file_manager):
    # Mocking suggest_mappings which is in the domain layer
    with patch("app.infrastructure.api.routes.intake.suggest_mappings") as mock_suggest:
        mock_suggest.return_value = [{"header": "First Name", "target": "first_name", "confidence": 95}]
        
        job_id = str(uuid.uuid4())
        mock_file_manager.ingest_file.return_value = uuid.uuid4()
        
        csv_content = b"First Name,Last Name\nJohn,Doe"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        response = client.post(f"/intake/upload?job_id={job_id}", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "headers" in data
        assert "suggestions" in data
        assert data["headers"] == ["First Name", "Last Name"]
        mock_file_manager.ingest_file.assert_called_once()

def test_upload_file_rejected_if_too_large():
    job_id = str(uuid.uuid4())
    # Send large file (FastAPI will handle the limit if configured, or our service will)
    large_content = b"0" * (51 * 1024 * 1024)
    files = {"file": ("large.csv", large_content, "text/csv")}
    
    response = client.post(f"/intake/upload?job_id={job_id}", files=files)
    
    # Depending on implementation, could be 413 or 400
    assert response.status_code in [413, 400]

def test_upload_file_rejected_invalid_extension():
    job_id = str(uuid.uuid4())
    files = {"file": ("malicious.exe", b"binary", "application/x-msdownload")}
    
    response = client.post(f"/intake/upload?job_id={job_id}", files=files)
    
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]

@pytest.mark.asyncio
async def test_confirm_mapping_success(mock_file_manager):
    job_id = str(uuid.uuid4())
    mappings = {"First Name": "first_name", "Last Name": "last_name"}
    
    # In a real scenario, we'd need a file staged. 
    # For this test, we might mock the data loading part.
    with patch("app.infrastructure.api.routes.intake.pd.read_csv") as mock_read:
        mock_read.return_value = pd.DataFrame([{"First Name": "John", "Last Name": "Doe"}])
        mock_file_manager.confirm_and_ingest.return_value = 1
        
        response = client.post(f"/intake/confirm/{job_id}", json=mappings)
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["records_ingested"] == 1

def test_confirm_mapping_fails_if_required_schema_missing(mock_file_manager):
    job_id = str(uuid.uuid4())
    # Intentionally missing 'hr_termination_date' for HR_ROSTER
    mappings = {"First Name": "first_name"}
    
    response = client.post(f"/intake/confirm/{job_id}?schema_type=HR_ROSTER", json=mappings)
    
    assert response.status_code == 400
    assert response.json()["error"] == "Validation Failed"
    assert "hr_termination_date" in response.json()["message"]
