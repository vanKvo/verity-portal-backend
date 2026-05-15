import uuid
from sqlalchemy import Column, String, Uuid, Enum as SqlEnum
import enum
from src.verity_portal.core.database import Base

class ProjectSensitivity(str, enum.Enum):
    ITAR_RESTRICTED = "ITAR_RESTRICTED"
    EAR99 = "EAR99"
    UNCLASSIFIED = "UNCLASSIFIED"

class ProjectModel(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    sensitivity = Column(
        SqlEnum(ProjectSensitivity), 
        default=ProjectSensitivity.UNCLASSIFIED, 
        nullable=False
    )
    department = Column(String(255), nullable=True)
    export_control_status = Column(String(255), nullable=False)
