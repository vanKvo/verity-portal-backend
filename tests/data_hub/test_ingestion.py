import pytest
import pandas as pd
from io import BytesIO
from src.verity_portal.data_hub.personnel.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.data_hub.personnel.service import PersonnelService
from src.verity_portal.data_hub.projects.models import ProjectModel, ProjectSensitivity
from src.verity_portal.data_hub.projects.service import ProjectService

def test_personnel_ingestion_with_fuzzy_matching(db_session):
    """Test that personnel roster is ingested correctly with fuzzy citizenship mapping."""
    data = {
        "employee_id": ["E001", "E002", "E003"],
        "first_name": ["John", "Jane", "Ivan"],
        "citizenship_status": ["US Citizen", "Green Card", "Non-US"],
        "termination_date": ["2024-01-01", None, "2023-12-31"]
    }
    df = pd.DataFrame(data)
    
    service = PersonnelService(db_session)
    result = service.ingest_personnel_roster(df)
    
    assert result["success_count"] == 3
    
    p1 = db_session.query(PersonnelModel).filter_by(employee_id="E001").first()
    assert p1.citizenship_status == CitizenshipStatus.US_CITIZEN
    assert str(p1.termination_date) == "2024-01-01"
    
    p2 = db_session.query(PersonnelModel).filter_by(employee_id="E002").first()
    assert p2.citizenship_status == CitizenshipStatus.PERMANENT_RESIDENT
    assert p2.termination_date is None
    
    p3 = db_session.query(PersonnelModel).filter_by(employee_id="E003").first()
    assert p3.citizenship_status == CitizenshipStatus.FOREIGN_NATIONAL

def test_project_sensitivity_ingestion(db_session):
    """Test that project sensitivity classifications are ingested correctly."""
    data = {
        "project_id": ["P100", "P200"],
        "name": ["Secret Space", "Internal Tools"],
        "sensitivity": ["ITAR_RESTRICTED", "EAR99"],
        "export_control_status": ["ACTIVE", "ACTIVE"]
    }
    df = pd.DataFrame(data)
    
    service = ProjectService(db_session)
    result = service.ingest_projects(df)
    
    assert result["success_count"] == 2
    
    proj = db_session.query(ProjectModel).filter_by(project_id="P100").first()
    assert proj.sensitivity == ProjectSensitivity.ITAR_RESTRICTED
