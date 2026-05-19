from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from src.verity_portal.core.database import get_db
from src.verity_portal.core.security.roles import require_role
import json
from src.verity_portal.itar.service import ItarService

router = APIRouter(prefix="/api/v1/itar", tags=["itar"])

@router.post(
    "/roster/upload", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_PM"))]
)
def upload_roster(
    file: UploadFile = File(...), 
    mapping: str = File(None),
    db: Session = Depends(get_db)
):
    """Securely uploads and processes a Program Management project roster."""
    column_mapping = json.loads(mapping) if mapping else None
    result = ItarService.ingest_roster(db, file, column_mapping=column_mapping)
    return result

@router.post(
    "/audit/run", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_PM"))]
)
def run_audit(db: Session = Depends(get_db)):
    """Triggers the ITAR reconciliation engine."""
    result = ItarService.run_reconciliation_audit(db)
    return {
        "message": "Audit complete", 
        "violations_detected": result["new_violations"],
        "auto_resolved": result["auto_resolved"]
    }

@router.get(
    "/violations", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_PM"))]
)
def get_violations(db: Session = Depends(get_db)):
    """Fetches all active and resolved compliance violations."""
    return ItarService.get_violations(db)

@router.put(
    "/violations/{violation_id}/resolve", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_ECO"))]
)
def resolve_violation(violation_id: str, reason: str = "MANUAL_RESOLUTION", db: Session = Depends(get_db)):
    """Marks a violation as resolved."""
    success = ItarService.resolve_violation(db, violation_id, reason)
    if not success:
        return {"message": "Violation not found or already resolved"}, status.HTTP_404_NOT_FOUND
    return {"message": "Violation resolved"}
