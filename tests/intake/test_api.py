import pytest
import uuid
import pandas as pd
from unittest.mock import AsyncMock, patch
from src.verity_portal.main import app
from src.verity_portal.intake.router import get_intake_service
from src.verity_portal.intake.service import IntakeService

@pytest.fixture
def mock_intake_service():
    service = AsyncMock(spec=IntakeService)
    # Store old override to restore it if needed, but conftest clears it
    app.dependency_overrides[get_intake_service] = lambda: service
    yield service
    # app.dependency_overrides.clear() # Don't clear all, just this one? 
    # Actually conftest.py's client fixture clears ALL overrides on exit.

@pytest.mark.asyncio
async def test_upload_file_success(client, mock_intake_service):
    with patch("src.verity_portal.intake.router.suggest_mappings") as mock_suggest:
        mock_suggest.return_value = [{"header": "First Name", "target": "first_name", "confidence": 95}]
        
        job_id = str(uuid.uuid4())
        mock_intake_service.ingest_file.return_value = uuid.uuid4()
        
        csv_content = b"First Name,Last Name\nJohn,Doe"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        response = client.post(f"/intake/upload?job_id={job_id}", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["headers"] == ["First Name", "Last Name"]
        mock_intake_service.ingest_file.assert_called_once()

def test_upload_file_rejected_if_too_large(client):
    job_id = str(uuid.uuid4())
    large_content = b"0" * (51 * 1024 * 1024)
    files = {"file": ("large.csv", large_content, "text/csv")}
    response = client.post(f"/intake/upload?job_id={job_id}", files=files)
    assert response.status_code in [413, 400]

def test_upload_file_rejected_invalid_extension(client):
    job_id = str(uuid.uuid4())
    files = {"file": ("malicious.exe", b"binary", "application/x-msdownload")}
    response = client.post(f"/intake/upload?job_id={job_id}", files=files)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_confirm_mapping_success(client, mock_intake_service):
    job_id = str(uuid.uuid4())
    mappings = {"First Name": "first_name", "Last Name": "last_name"}
    payload = {"mappings": mappings, "schema_type": None}
    
    with patch("src.verity_portal.intake.router.pd.read_csv") as mock_read:
        mock_read.return_value = pd.DataFrame([{"First Name": "John", "Last Name": "Doe"}])
        mock_intake_service.confirm_and_ingest.return_value = 1
        
        response = client.post(f"/intake/confirm/{job_id}", json=payload)
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"

def test_confirm_mapping_fails_if_required_schema_missing(client, mock_intake_service):
    job_id = str(uuid.uuid4())
    mappings = {"First Name": "first_name"}
    payload = {"mappings": mappings, "schema_type": "HR_ROSTER"}
    response = client.post(f"/intake/confirm/{job_id}", json=payload)
    assert response.status_code == 400
