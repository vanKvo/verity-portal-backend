from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date
from src.verity_portal.data_hub.personnel.models import CitizenshipStatus

class PersonnelMasterSchema(BaseModel):
    employee_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    citizenship_status: CitizenshipStatus = CitizenshipStatus.UNKNOWN
    termination_date: Optional[date] = None

    @field_validator("citizenship_status", mode="before")
    @classmethod
    def normalize_citizenship(cls, raw_status: str | CitizenshipStatus) -> CitizenshipStatus:
        """Normalizes the citizenship status input before validation.
        
        Args:
            raw_status: The incoming status as a string or Enum member.
            
        Returns:
            A valid CitizenshipStatus member.
        """
        if isinstance(raw_status, CitizenshipStatus):
            return raw_status
            
        # Basic normalization for common string inputs
        if isinstance(raw_status, str):
            status_upper = raw_status.upper().replace(" ", "_")
            try:
                return CitizenshipStatus[status_upper]
            except KeyError:
                return CitizenshipStatus.UNKNOWN
                
        return CitizenshipStatus.UNKNOWN
