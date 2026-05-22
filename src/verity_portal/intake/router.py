import uuid
import io
import os
import pandas as pd
import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

from sqlalchemy.orm import Session
from src.verity_portal.core.database import get_db
from src.verity_portal.intake.storage import LocalFileSystemAdapter
from src.verity_portal.intake.service import IntakeService
from src.verity_portal.intake.mapper import suggest_mappings
from src.verity_portal.intake.schemas import ConfirmMappingRequest, UploadResponse
from src.verity_portal.core.exceptions import MappingError
from src.verity_portal.core.utils.file_utils import extract_headers_from_file

router = APIRouter(prefix="/intake", tags=["Data Intake"])
logger = logging.getLogger(__name__)

def get_intake_service(db: Session = Depends(get_db)):
    storage_adapter = LocalFileSystemAdapter()
    return IntakeService(storage_port=storage_adapter, db=db)

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    job_id: uuid.UUID,
    file: UploadFile = File(...),
    intake_service: IntakeService = Depends(get_intake_service)
):
    allowed_extensions = {".csv", ".xlsx", ".xls"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )

    content = await file.read()
    
    try:
        file_id = await intake_service.ingest_file(content, job_id, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    try:
        headers = extract_headers_from_file(file.filename, io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse file: {str(e)}")

    target_schema = ["first_name", "last_name", "email", "citizenship", "role"] 
    suggestions = suggest_mappings(headers, target_schema)

    return {
        "file_id": file_id,
        "job_id": job_id,
        "headers": headers,
        "suggestions": suggestions
    }

REQUIRED_SCHEMAS = {
    "HR_ROSTER": ["employee_id", "hr_termination_date"],
    "IT_ACCESS": ["employee_id", "last_system_login"]
}

@router.post("/confirm/{job_id}")
async def confirm_mapping(
    job_id: uuid.UUID,
    request: ConfirmMappingRequest,
    intake_service: IntakeService = Depends(get_intake_service)
):
    # Filter out empty or null mappings to avoid columns with empty headers
    active_mappings = {k: v for k, v in request.mappings.items() if k and v}
    schema_type = request.schema_type
    
    if schema_type in REQUIRED_SCHEMAS:
        required_fields = REQUIRED_SCHEMAS[schema_type]
        mapped_targets = set(active_mappings.values())
        missing = [f for f in required_fields if f not in mapped_targets]
        if missing:
            raise MappingError(missing)

    try:
        count = await intake_service.confirm_and_ingest(job_id, active_mappings)
        return {"status": "success", "records_ingested": count}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unhandled error in comfirm_mapping: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
