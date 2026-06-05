"""Pydantic verification schemas for IT Activity master records.

Validates column formats and attributes before database persistence.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItActivityMasterSchema(BaseModel):
    """Data transfer object mapping incoming IT Activity columns to system fields.

    Attributes:
        employee_id: The string ID of the employee associated with the login event.
        last_system_login: The timezone-aware timestamp of the system login event.
        ip_address: Optional IP address recorded during login.
        system_name: Optional identity or category of the system accessed.
    """
    employee_id: str
    last_system_login: datetime
    ip_address: Optional[str] = None
    system_name: Optional[str] = None
    user_name: Optional[str] = None
    system_access_level: Optional[str] = None
