from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from src.verity_portal.data_hub.inventory.models import AssetStatus

class InventorySchema(BaseModel):
    """Pydantic schema for parsing and validating raw IT inventory data."""
    asset_tag: str = Field(..., max_length=100)
    po_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    assigned_employee_id: Optional[str] = Field(None, max_length=50)
    status: AssetStatus = Field(default=AssetStatus.STORAGE)
    physical_location_site: Optional[str] = Field(None, max_length=100)
    physical_location_room: Optional[str] = Field(None, max_length=100)

    model_config = ConfigDict(from_attributes=True)
