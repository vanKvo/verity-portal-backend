import uuid
from sqlalchemy import Column, String, Boolean, Uuid, DateTime, JSON
from sqlalchemy.sql import func
from .setup import Base

class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user", nullable=False)

class FileMetadataModel(Base):
    __tablename__ = "file_metadata"
    __table_args__ = {"schema": "verity"}

    file_id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    original_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)
    status = Column(String, default="STAGED", nullable=False) # STAGED, PROCESSED, ARCHIVED, PURGED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IntakeRecordModel(Base):
    __tablename__ = "intake_records"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    data = Column(JSON, nullable=False) # JSONB in Postgres
    created_at = Column(DateTime(timezone=True), server_default=func.now())
