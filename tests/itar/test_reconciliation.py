import pytest
from src.verity_portal.data_hub.personnel.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.data_hub.projects.models import ProjectModel, ProjectSensitivity
from src.verity_portal.itar.models import ProjectAssignmentModel, ComplianceViolationModel
from src.verity_portal.itar.service import ItarService

def test_reconciliation_engine_safe_access(db_session):
    """Test that US Citizens on ITAR projects don't create violations."""
    p = PersonnelModel(employee_id="E001", citizenship_status=CitizenshipStatus.US_CITIZEN)
    proj = ProjectModel(project_id="P1", name="ITAR Proj", sensitivity=ProjectSensitivity.ITAR_RESTRICTED, export_control_status="ACTIVE")
    db_session.add_all([p, proj])
    db_session.commit()
    
    db_session.add(ProjectAssignmentModel(employee_id=p.employee_id, project_id=proj.project_id))
    db_session.commit()

    ItarService.run_reconciliation_audit(db_session)
    
    violations = db_session.query(ComplianceViolationModel).all()
    assert len(violations) == 0

def test_reconciliation_engine_violation_detected(db_session):
    """Test that Foreign Nationals on ITAR projects create OPEN violations."""
    p = PersonnelModel(employee_id="E002", citizenship_status=CitizenshipStatus.FOREIGN_NATIONAL)
    proj = ProjectModel(project_id="P1", name="ITAR Proj", sensitivity=ProjectSensitivity.ITAR_RESTRICTED, export_control_status="ACTIVE")
    db_session.add_all([p, proj])
    db_session.commit()
    
    db_session.add(ProjectAssignmentModel(employee_id=p.employee_id, project_id=proj.project_id))
    db_session.commit()

    ItarService.run_reconciliation_audit(db_session)
    
    violation = db_session.query(ComplianceViolationModel).first()
    assert violation is not None
    assert violation.employee_id == p.employee_id
    assert violation.project_id == proj.project_id
    assert violation.status == "OPEN"

def test_auto_resolution_logic(db_session):
    """Test that violations are auto-resolved when data is updated."""
    # 1. Create a violation
    p = PersonnelModel(employee_id="E003", citizenship_status=CitizenshipStatus.FOREIGN_NATIONAL)
    proj = ProjectModel(project_id="P1", name="ITAR Proj", sensitivity=ProjectSensitivity.ITAR_RESTRICTED, export_control_status="ACTIVE")
    db_session.add_all([p, proj])
    db_session.commit()
    
    db_session.add(ProjectAssignmentModel(employee_id=p.employee_id, project_id=proj.project_id))
    db_session.commit()

    # Detect violation
    ItarService.run_reconciliation_audit(db_session)
    violation = db_session.query(ComplianceViolationModel).filter_by(status="OPEN").first()
    assert violation is not None

    # 2. Fix the underlying data (Personnel becomes US Citizen)
    p.citizenship_status = CitizenshipStatus.US_CITIZEN
    db_session.commit()

    # 3. Run audit again
    result = ItarService.run_reconciliation_audit(db_session)
    
    # 4. Verify auto-resolution
    assert result["auto_resolved"] == 1
    db_session.refresh(violation)
    assert violation.status == "RESOLVED"
    assert violation.resolution_reason == "SYSTEM_AUTO_RESOLVED"
