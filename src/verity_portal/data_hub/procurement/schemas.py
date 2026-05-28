from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ProcurementSchema(BaseModel):
    """Pydantic schema for parsing and validating raw procurement data."""
    po_number: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    purchase_date: Optional[datetime] = None
    vendor: Optional[str] = Field(None, max_length=255)
    asset_category: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(default=1)
    unit_price: Optional[float] = None
    total_cost: Optional[float] = None
    status: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)
