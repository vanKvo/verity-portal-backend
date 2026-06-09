"""Pydantic schemas for Leaver/Mover Access violation tracking.

Validates requests and responses for violation listing and resolution operations.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from src.verity_portal.audit.models import LeaverViolationStatus


class LeaverViolationResponseSchema(BaseModel):
    """Pydantic DTO for representing access violations.

    Attributes:
        id: Unique UUID identifier.
        employee_id: The employee associated with the violation.
        hr_termination_date: The recorded date of employment termination.
        last_system_login: The timestamp of system login.
        status: Current state of the violation (OPEN or RESOLVED).
        resolution_reason: Optional explanation entered during resolution.
        resolved_by: The username/role of the person who resolved it.
        resolved_at: The timestamp of the resolution action.
        created_at: Audit generation timestamp.
        updated_at: Last modification timestamp.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: str
    hr_termination_date: date
    last_system_login: datetime
    system_name: Optional[str] = None
    ip_address: Optional[str] = None
    status: LeaverViolationStatus
    resolution_reason: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LeaverViolationResolveSchema(BaseModel):
    """Payload to resolve an open access violation.

    Attributes:
        resolution_reason: Explanation of remediation action.
    """
    resolution_reason: str
