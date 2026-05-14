import uuid
from sqlalchemy import Column, String, Uuid, Enum as SqlEnum
import enum
from src.verity_portal.core.database import Base

class CitizenshipStatus(str, enum.Enum):
    US_CITIZEN = "US_CITIZEN"
    PERMANENT_RESIDENT = "PERMANENT_RESIDENT"
    FOREIGN_NATIONAL = "FOREIGN_NATIONAL"
    UNKNOWN = "UNKNOWN"

class PersonnelModel(Base):
    __tablename__ = "personnel"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    citizenship_status = Column(
        SqlEnum(CitizenshipStatus), 
        default=CitizenshipStatus.UNKNOWN, 
        nullable=False
    )
