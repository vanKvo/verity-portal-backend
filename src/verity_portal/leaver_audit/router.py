"""Presentation router layer for compliance audit endpoints.

Exposes APIs to trigger run audits, export reports, list violations, and log resolutions.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.verity_portal.core.database import get_db
from src.verity_portal.core.security.roles import require_role, require_any_role
from src.verity_portal.leaver_audit.service import audit_leaver_mover
from src.verity_portal.intake.router import get_intake_service
from src.verity_portal.intake.service import IntakeService
from src.verity_portal.leaver_audit.exceptions import ComplianceError
from src.verity_portal.leaver_audit.models import LeaverViolationModel, LeaverViolationStatus
from src.verity_portal.leaver_audit.schemas import LeaverViolationResponseSchema, LeaverViolationResolveSchema

router = APIRouter(prefix="/leaver-audit", tags=["Compliance Audit"])


@router.post("/leaver-mover")
async def run_leaver_mover_audit(
    request: Dict[str, str], 
    intake_service: IntakeService = Depends(get_intake_service)
):
    hr_job_id = request.get("hr_job_id")
    access_job_id = request.get("access_job_id")
    
    if not hr_job_id or not access_job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Both hr_job_id and access_job_id are required."
        )
        
    try:
        hr_data = intake_service.get_records(hr_job_id)
        access_data = intake_service.get_records(access_job_id)
        
        violations = audit_leaver_mover(hr_data, access_data)
        return {"violations": violations}
        
    except ComplianceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get(
    "/leaver-mover/violations",
    response_model=List[LeaverViolationResponseSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_any_role(["ROLE_IT", "ROLE_ECO", "ROLE_HR"]))],
)
async def get_leaver_mover_violations(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[LeaverViolationResponseSchema]:
    """Retrieves access violations, optionally filtered by status.

    Args:
        status_filter: Optional string filter ('OPEN' or 'RESOLVED').
        db: Injected database session.

    Returns:
        A list of validated LeaverViolationResponseSchema DTOs.
    """
    query = db.query(LeaverViolationModel)
    if status_filter:
        query = query.filter(LeaverViolationModel.status == status_filter.upper())
    violations = query.order_by(LeaverViolationModel.created_at.desc()).all()
    return violations


@router.post(
    "/leaver-mover/violations/{id}/resolve",
    response_model=LeaverViolationResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def resolve_leaver_mover_violation(
    id: str,
    payload: LeaverViolationResolveSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_any_role(["ROLE_ECO", "ROLE_HR"])),
) -> LeaverViolationResponseSchema:
    """Resolves an open leaver access violation by providing a reason.

    Enforces ROLE_ECO or ROLE_HR permissions before allowing update.

    Args:
        id: UUID string identifier of the violation.
        payload: Inbound resolution description schema.
        db: Injected database session.
        current_user: Token payload representing the resolving user.

    Returns:
        The updated violation record.
    """
    try:
        violation_uuid = uuid.UUID(id) if isinstance(id, str) else id
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_UUID",
                "message": "The provided violation ID is not a valid UUID.",
            },
        ) from exc

    violation = db.query(LeaverViolationModel).filter(LeaverViolationModel.id == violation_uuid).first()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "RESOURCE_NOT_FOUND",
                "message": "The requested compliance violation could not be located.",
            },
        )
    
    if violation.status == LeaverViolationStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "ALREADY_RESOLVED",
                "message": "This compliance violation has already been resolved.",
            },
        )
    
    violation.status = LeaverViolationStatus.RESOLVED
    violation.resolution_reason = payload.resolution_reason
    violation.resolved_by = current_user.get("sub", "unknown")
    violation.resolved_at = func.now()
    
    db.commit()
    db.refresh(violation)
    return violation
