import uuid
from sqlalchemy import Column, String, Boolean, Uuid
from src.verity_portal.core.database import Base

class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default="user", nullable=False)
