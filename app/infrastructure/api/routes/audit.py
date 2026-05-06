import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import io

from app.infrastructure.adapters.database.setup import get_db
from app.infrastructure.adapters.database.models import IntakeRecordModel
from app.domain.services.auditor import audit_leaver_mover
from app.domain.services.exporter import generate_audit_csv, generate_audit_pdf
from app.domain.exceptions.compliance import ComplianceException

router = APIRouter(prefix="/audit", tags=["Compliance Audit"])

class AuditRequest:
    # Using simple dict for body validation in this MVP slice
    pass

@router.post("/leaver-mover")
async def run_leaver_mover_audit(
    request: Dict[str, str], 
    db: Session = Depends(get_db)
):
    hr_job_id = request.get("hr_job_id")
    access_job_id = request.get("access_job_id")
    
    if not hr_job_id or not access_job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Both hr_job_id and access_job_id are required."
        )
        
    try:
        # Fetch records from IntakeRecordModel
        hr_records = db.query(IntakeRecordModel).filter(IntakeRecordModel.job_id == hr_job_id).all()
        access_records = db.query(IntakeRecordModel).filter(IntakeRecordModel.job_id == access_job_id).all()
        
        # Convert DB models to plain dicts for domain service
        hr_data = [r.data for r in hr_records]
        access_data = [r.data for r in access_records]
        
        violations = audit_leaver_mover(hr_data, access_data)
        
        return {"violations": violations}
        
    except ComplianceException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
