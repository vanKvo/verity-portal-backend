from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.verity_portal.core.database import get_db
from src.verity_portal.core.security.roles import require_role
from src.verity_portal.asset_audit.models import AssetViolationModel, AssetViolationStatus

router = APIRouter(prefix="/asset-audit", tags=["Asset Audit"])

@router.get("/violations", status_code=status.HTTP_200_OK)
async def get_asset_violations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # Temporarily skipping complex RBAC OR logic by allowing anyone who reaches this endpoint 
    # (assuming it's protected at a higher level or just using ROLE_FINANCE for now to get it working)
    _ = Depends(require_role("ROLE_FINANCE")),
):
    """Retrieves paginated audit violations."""
    violations = db.query(AssetViolationModel).order_by(AssetViolationModel.created_at.desc()).offset(skip).limit(limit).all()
    return violations

@router.post("/violations/{violation_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_asset_violation(
    violation_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    _ = Depends(require_role("ROLE_FINANCE")),
):
    """Resolves an open financial anomaly. Restricted to ROLE_FINANCE."""
    violation = db.query(AssetViolationModel).filter_by(id=violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
        
    reason = payload.get("resolution_reason")
    if not reason:
        raise HTTPException(status_code=400, detail="resolution_reason is required")
        
    violation.status = AssetViolationStatus.RESOLVED
    violation.resolution_reason = reason
    db.commit()
    
    return {"message": "Violation resolved successfully"}
