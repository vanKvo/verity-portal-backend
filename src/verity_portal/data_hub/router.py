from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Form, HTTPException
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

def parse_file_to_df(filename: str, contents: bytes) -> pd.DataFrame:
    fn = filename.lower()
    if fn.endswith(('.xlsx', '.xls')):
        return pd.read_excel(io.BytesIO(contents))
    elif fn.endswith('.numbers'):
        from numbers_parser import Document
        doc = Document(io.BytesIO(contents))
        sheets = doc.sheets
        if not sheets or not sheets[0].tables:
            raise ValueError("Invalid Numbers file: no sheets or tables found")
        table = sheets[0].tables[0]
        data = []
        for row in table.rows():
            data.append([cell.value if cell.value is not None else "" for cell in row])
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    else:
        return pd.read_csv(io.BytesIO(contents))

@router.post("/parse-headers")
async def parse_headers(file: UploadFile = File(...)):
    """Extracts column headers from CSV, Excel, or Numbers files for frontend mapping."""
    contents = await file.read()
    filename = file.filename.lower()
    try:
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents), nrows=1)
            headers = list(df.columns)
        elif filename.endswith('.numbers'):
            from numbers_parser import Document
            doc = Document(io.BytesIO(contents))
            sheets = doc.sheets
            if not sheets or not sheets[0].tables:
                raise ValueError("Invalid Numbers file: no sheets or tables found")
            table = sheets[0].tables[0]
            headers = [str(cell.value) if cell.value is not None else "" for cell in table.rows(0)[0]]
        else:
            df = pd.read_csv(io.BytesIO(contents), nrows=1)
            headers = list(df.columns)
        
        headers = [str(h).strip() for h in headers if h is not None]
        return {"headers": headers}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse column headers: {str(e)}")

@router.post("/personnel/upload", dependencies=[Depends(require_role("ROLE_HR"))])
async def upload_hr_data(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Manual upload for HR Master Data (Citizenship, Termination)."""
    contents = await file.read()
    try:
        df = parse_file_to_df(file.filename, contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
    try:
        df = parse_file_to_df(file.filename, contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
    return {"message": "S3 Sync Triggered"}
