import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domain.exceptions.compliance import MappingError

client = TestClient(app)

def test_mapping_error_is_wrapped_in_json():
    # We'll create a temporary route to trigger the error
    @app.get("/test-mapping-error")
    async def trigger_mapping_error():
        raise MappingError(["employee_id", "hr_termination_date"])

    response = client.get("/test-mapping-error")
    
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["error"] == "Validation Failed"
    assert "employee_id" in json_data["message"]
    assert "hr_termination_date" in json_data["message"]
