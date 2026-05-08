import uuid
from sqlalchemy import Column, String, Boolean, Uuid
from src.verity_portal.core.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user", nullable=False)
