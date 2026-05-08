from pydantic import BaseModel
from typing import Dict, Optional, List
import uuid

class ConfirmMappingRequest(BaseModel):
    mappings: Dict[str, str]
    schema_type: Optional[str] = None

class UploadResponse(BaseModel):
    file_id: uuid.UUID
    job_id: uuid.UUID
    headers: List[str]
    suggestions: List[Dict]
