from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.verity_portal.core.database import get_db
from src.verity_portal.core.security.roles import require_role
from src.verity_portal.asset_audit.schemas import AssetViolationSchema, ResolveViolationRequest
from src.verity_portal.asset_audit.service import AssetAuditService
from typing import List

router = APIRouter(prefix="/asset-audit", tags=["Asset Audit"])

@router.get("/violations", response_model=List[AssetViolationSchema], status_code=status.HTTP_200_OK)
async def get_asset_violations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # Protect with finance auditor role verification
    _ = Depends(require_role("ROLE_FINANCE")),
):
    """Retrieves paginated audit violations with enriched metadata."""
    return AssetAuditService.get_violations(db, skip=skip, limit=limit)

@router.post("/violations/{violation_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_asset_violation(
    violation_id: str,
    payload: ResolveViolationRequest,
    db: Session = Depends(get_db),
    _ = Depends(require_role("ROLE_FINANCE")),
):
    """Resolves an open financial anomaly. Restricted to ROLE_FINANCE."""
    resolved = AssetAuditService.resolve_violation(
        db, 
        violation_id=violation_id, 
        reason=payload.resolution_reason
    )
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "VIOLATION_NOT_FOUND",
                "message": "The requested compliance anomaly or violation could not be located.",
            },
        )
    return {"message": "Violation resolved successfully"}

