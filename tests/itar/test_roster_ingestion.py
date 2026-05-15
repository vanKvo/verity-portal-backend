import pytest
import io
from src.verity_portal.data_hub.personnel.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.data_hub.projects.models import ProjectModel, ProjectSensitivity
from src.verity_portal.itar.models import ProjectAssignmentModel
from src.verity_portal.identity.router import create_access_token

def test_ingest_roster_success(client, db_session):
    """Test that a valid roster CSV correctly creates ProjectAssignment records."""
    # 1. Setup baseline data
    personnel = PersonnelModel(
        employee_id="E101", 
        first_name="John", 
        last_name="Doe", 
        citizenship_status=CitizenshipStatus.US_CITIZEN
    )
    project = ProjectModel(
        project_id="P500", 
        name="Project X", 
        sensitivity=ProjectSensitivity.ITAR_RESTRICTED,
        export_control_status="ACTIVE"
    )
    db_session.add(personnel)
    db_session.add(project)
    db_session.commit()

    # 2. Prepare CSV data
    csv_content = "employee_id,project_id\nE101,P500"
    file = ("roster.csv", io.BytesIO(csv_content.encode()))

    # 3. Authenticate
    token = create_access_token(data={"sub": "admin@verity.com", "roles": ["ROLE_PM"]})
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Action
    response = client.post(
        "/api/v1/itar/roster/upload",
        files={"file": file},
        headers=headers
    )

    # 5. Assertions
    assert response.status_code == 200
    assert response.json()["success_count"] == 1
    assert response.json()["error_count"] == 0
    
    # Verify DB state
    assignment = db_session.query(ProjectAssignmentModel).first()
    assert assignment is not None
    assert assignment.personnel_id == personnel.id
    assert assignment.project_id == project.id

def test_ingest_roster_unauthorized(client):
    """Test that the endpoint rejects users without the correct role."""
    csv_content = "employee_id,project_id\nE101,P500"
    file = ("roster.csv", io.BytesIO(csv_content.encode()))

    # Token with wrong role
    token = create_access_token(data={"sub": "user@verity.com", "roles": ["USER"]})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/itar/roster/upload",
        files={"file": file},
        headers=headers
    )
    assert response.status_code == 403
