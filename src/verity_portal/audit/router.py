from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.verity_portal.core.database import get_db
from src.verity_portal.audit.service import audit_leaver_mover
from src.verity_portal.audit.exporter import generate_audit_csv, generate_audit_pdf
from src.verity_portal.intake.router import get_intake_service
from src.verity_portal.intake.service import IntakeService
from src.verity_portal.audit.exceptions import ComplianceError

router = APIRouter(prefix="/audit", tags=["Compliance Audit"])

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

@router.post("/export/csv")
async def export_audit_csv(violations: List[Dict[str, Any]]):
    try:
        csv_bytes = generate_audit_csv(violations)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

@router.post("/export/pdf")
async def export_audit_pdf(violations: List[Dict[str, Any]]):
    try:
        pdf_bytes = generate_audit_pdf(violations)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=audit_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
