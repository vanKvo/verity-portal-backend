from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List, Dict
import uuid
import io
import pandas as pd
from sqlalchemy.orm import Session
from app.infrastructure.adapters.database.setup import get_db
from app.infrastructure.adapters.storage.local_adapter import LocalFileSystemAdapter
from app.domain.services.file_manager import FileManager
from app.domain.services.mapper import suggest_mappings

router = APIRouter(prefix="/intake", tags=["Data Intake"])

def get_file_manager(db: Session = Depends(get_db)):
    storage_adapter = LocalFileSystemAdapter()
    return FileManager(storage_port=storage_adapter, db=db)

@router.post("/upload")
async def upload_file(
    job_id: uuid.UUID,
    file: UploadFile = File(...),
    file_manager: FileManager = Depends(get_file_manager)
):
    # 1. Validate extension
    allowed_extensions = {".csv", ".xlsx", ".xls"}
    import os
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )

    # 2. Read content
    content = await file.read()
    
    # 3. Save file via FileManager
    try:
        file_id = await file_manager.ingest_file(content, job_id, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))

    # 4. Extract headers
    headers = []
    try:
        if ext.lower() == ".csv":
            df = pd.read_csv(io.BytesIO(content), nrows=0)
            headers = df.columns.tolist()
        else:
            df = pd.read_excel(io.BytesIO(content), nrows=0)
            headers = df.columns.tolist()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse file: {str(e)}")

    # 5. Get suggestions (Task 8 will implement this fully)
    target_schema = ["first_name", "last_name", "email", "citizenship", "role"] # Mock schema
    suggestions = suggest_mappings(headers, target_schema)

    return {
        "file_id": file_id,
        "job_id": job_id,
        "headers": headers,
        "suggestions": suggestions
    }

@router.post("/confirm/{job_id}")
async def confirm_mapping(
    job_id: uuid.UUID,
    mappings: Dict[str, str],
    file_manager: FileManager = Depends(get_file_manager)
):
    try:
        count = await file_manager.confirm_and_ingest(job_id, mappings)
        return {"status": "success", "records_ingested": count}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
