import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from src.verity_portal.core.security.roles import require_role
from src.verity_portal.identity.router import create_access_token

# Mock app for testing dependencies
test_app = FastAPI()

@test_app.get("/protected")
def protected_route(_ = Depends(require_role("ROLE_EXPORT_CONTROL"))):
    return {"message": "success"}

def test_require_role_denied_when_missing():
    """Test that 403 is returned if the user lacks the required role."""
    client = TestClient(test_app)
    # Token with wrong role
    token = create_access_token(data={"sub": "test@verity.com", "roles": ["USER"]})
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"

def test_require_role_allowed_when_present():
    """Test that access is granted if the user has the required role."""
    client = TestClient(test_app)
    # Token with correct role
    token = create_access_token(data={"sub": "test@verity.com", "roles": ["ROLE_EXPORT_CONTROL"]})
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "success"
