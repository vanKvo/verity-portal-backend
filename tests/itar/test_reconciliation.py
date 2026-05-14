import pytest
from src.verity_portal.shared.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.itar.models import ProjectModel, ProjectAssignmentModel, ProjectSensitivity, ComplianceViolationModel
from src.verity_portal.itar.service import ItarService

def test_reconciliation_engine_safe_access(db_session):
    """Test that US Citizens on ITAR projects don't create violations."""
    p = PersonnelModel(employee_id="E001", citizenship_status=CitizenshipStatus.US_CITIZEN)
    proj = ProjectModel(project_id="P1", name="ITAR Proj", sensitivity=ProjectSensitivity.ITAR_RESTRICTED)
    db_session.add_all([p, proj])
    db_session.commit()
    
    db_session.add(ProjectAssignmentModel(personnel_id=p.id, project_id=proj.id))
    db_session.commit()

    ItarService.run_reconciliation_audit(db_session)
    
    violations = db_session.query(ComplianceViolationModel).all()
    assert len(violations) == 0

def test_reconciliation_engine_violation_detected(db_session):
    """Test that Foreign Nationals on ITAR projects create OPEN violations."""
    p = PersonnelModel(employee_id="E002", citizenship_status=CitizenshipStatus.FOREIGN_NATIONAL)
    proj = ProjectModel(project_id="P1", name="ITAR Proj", sensitivity=ProjectSensitivity.ITAR_RESTRICTED)
    db_session.add_all([p, proj])
    db_session.commit()
    
    db_session.add(ProjectAssignmentModel(personnel_id=p.id, project_id=proj.id))
    db_session.commit()

    ItarService.run_reconciliation_audit(db_session)
    
    violation = db_session.query(ComplianceViolationModel).first()
    assert violation is not None
    assert violation.personnel_id == p.id
    assert violation.project_id == proj.id
    assert violation.status == "OPEN"
