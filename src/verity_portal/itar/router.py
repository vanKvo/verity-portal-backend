from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from src.verity_portal.core.database import get_db
from src.verity_portal.core.security.roles import require_role
from src.verity_portal.itar.service import ItarService

router = APIRouter(prefix="/api/v1/itar", tags=["itar"])

@router.post(
    "/roster/upload", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_EXPORT_CONTROL"))]
)
def upload_roster(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    """Securely uploads and processes a Program Management project roster."""
    ItarService.ingest_roster(db, file)
    return {"message": "Ingestion complete"}

@router.post(
    "/audit/run", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_EXPORT_CONTROL"))]
)
def run_audit(db: Session = Depends(get_db)):
    """Triggers the ITAR reconciliation engine."""
    violations_found = ItarService.run_reconciliation_audit(db)
    return {"message": "Audit complete", "violations_detected": violations_found}

@router.get(
    "/violations", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_EXPORT_CONTROL"))]
)
def get_violations(db: Session = Depends(get_db)):
    """Fetches all active compliance violations."""
    from src.verity_portal.itar.models import ComplianceViolationModel
    return db.query(ComplianceViolationModel).filter(ComplianceViolationModel.status == "OPEN").all()

@router.put(
    "/violations/{violation_id}/resolve", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_EXPORT_CONTROL"))]
)
def resolve_violation(violation_id: str, db: Session = Depends(get_db)):
    """Marks a violation as resolved."""
    from src.verity_portal.itar.models import ComplianceViolationModel
    violation = db.query(ComplianceViolationModel).filter(ComplianceViolationModel.id == violation_id).first()
    if violation:
        violation.status = "RESOLVED"
        db.commit()
    return {"message": "Violation resolved"}
