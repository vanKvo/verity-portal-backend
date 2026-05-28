from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from src.verity_portal.asset_audit.models import AssetViolationType, AssetViolationStatus

class AssetViolationSchema(BaseModel):
    """Pydantic schema for returning asset violation anomalies."""
    id: UUID
    violation_type: AssetViolationType
    asset_tag: Optional[str] = None
    po_number: Optional[str] = None
    status: AssetViolationStatus
    resolution_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ResolveViolationRequest(BaseModel):
    """Payload for resolving a financial violation."""
    resolution_reason: str = Field(..., min_length=5, max_length=500, description="Reason for resolving the violation")
