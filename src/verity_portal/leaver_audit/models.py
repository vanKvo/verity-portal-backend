"""Database models for compliance audit violations.

Provides tracking for post-termination access and resolution audits.
"""

import enum
import uuid
from sqlalchemy import Column, String, Enum as SqlEnum, DateTime, Date, Uuid, ForeignKey
from sqlalchemy.sql import func
from src.verity_portal.core.database import Base


class LeaverViolationStatus(str, enum.Enum):
    """Enum representing the resolution state of an access violation."""
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class LeaverViolationModel(Base):
    """Tracks post-termination login events and their resolutions.

    Attributes:
        id: Unique UUID primary key.
        employee_id: Foreign key linking to the personnel master record.
        hr_termination_date: The date the employee was terminated.
        last_system_login: The timestamp of the system login recorded after termination.
        status: Active state of the violation (OPEN or RESOLVED).
        resolution_reason: Descriptive note on how the violation was resolved.
        resolved_by: The user ID/role of the resolver.
        resolved_at: The timestamp of when the resolution was finalized.
        created_at: Timestamp showing when the violation was detected.
        updated_at: Timestamp showing when the violation was last modified.
    """
    __tablename__ = "leaver_violations"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(50), ForeignKey("verity.personnel.employee_id"), nullable=False)
    hr_termination_date = Column(Date, nullable=False)
    last_system_login = Column(DateTime(timezone=True), nullable=False)
    system_name = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    status = Column(
        SqlEnum(LeaverViolationStatus),
        default=LeaverViolationStatus.OPEN,
        nullable=False
    )
    resolution_reason = Column(String(500), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
