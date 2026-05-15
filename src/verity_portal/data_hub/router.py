from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import Optional
import json
import pandas as pd
import io
from src.verity_portal.core.database import get_db
from src.verity_portal.core.security.roles import require_role
from src.verity_portal.data_hub.personnel.service import PersonnelService
from src.verity_portal.data_hub.projects.service import ProjectService

router = APIRouter(prefix="/data-hub", tags=["Data Hub"])

@router.post("/personnel/upload", dependencies=[Depends(require_role("ROLE_HR"))])
async def upload_hr_data(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Manual upload for HR Master Data (Citizenship, Termination)."""
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    column_mapping = json.loads(mapping) if mapping else None
    
    service = PersonnelService(db)
    result = service.ingest_personnel_roster(df, column_mapping=column_mapping)
    
    return result

@router.post("/projects/upload", dependencies=[Depends(require_role("ROLE_ECO"))])
async def upload_project_data(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Manual upload for Project Master Data (Sensitivity)."""
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    column_mapping = json.loads(mapping) if mapping else None
    
    service = ProjectService(db)
    result = service.ingest_projects(df, column_mapping=column_mapping)
    
    return result

@router.post("/webhooks/s3-ingest")
async def s3_webhook_ingest(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook triggered by S3 event to sync HR data."""
    # Logic to fetch from S3 using boto3 would go here.
    # For now, we simulate triggering the PersonnelService.
    return {"message": "S3 Sync Triggered"}
