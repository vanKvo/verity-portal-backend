import uuid
from sqlalchemy import Column, String, Uuid, ForeignKey, Enum as SqlEnum, DateTime
from sqlalchemy.sql import func
import enum
from src.verity_portal.core.database import Base

class ProjectSensitivity(str, enum.Enum):
    ITAR_RESTRICTED = "ITAR_RESTRICTED"
    EAR99 = "EAR99"
    UNCLASSIFIED = "UNCLASSIFIED"

# ProjectModel and ProjectSensitivity moved to data_hub.projects.models

class ProjectAssignmentModel(Base):
    __tablename__ = "project_assignments"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("verity.projects.id"), nullable=False)
    personnel_id = Column(Uuid(as_uuid=True), ForeignKey("verity.personnel.id"), nullable=False)
    last_verified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ComplianceViolationModel(Base):
    __tablename__ = "compliance_violations"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    personnel_id = Column(Uuid(as_uuid=True), ForeignKey("verity.personnel.id"), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("verity.projects.id"), nullable=False)
    status = Column(String(50), default="OPEN", nullable=False) # OPEN, RESOLVED
    resolution_reason = Column(String(255), nullable=True) # SYSTEM_AUTO_RESOLVED, MANUAL_DSP5, etc.
    notes = Column(String, nullable=True) # Unlimited text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
