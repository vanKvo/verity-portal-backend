"""Database models for Data Hub core auditing logs.

Tracks the metadata and history of files uploaded manually or synchronized via S3.
"""

import uuid
from sqlalchemy import Column, String, Integer, DateTime, Uuid
from sqlalchemy.sql import func
from src.verity_portal.core.database import Base


class IngestionLogModel(Base):
    """Logs the ingestion of files and datasets into the Data Hub.

    Attributes:
        id: Unique UUID primary key.
        schema_type: Category of schema being ingested (e.g. personnel, projects, procurement, inventory, it_activity).
        filename: Name of the imported file.
        source: Trigger source (e.g. MANUAL or S3).
        uploaded_by: User email address or SYSTEM context.
        records_count: Total count of records processed successfully.
        created_at: Audit generation timestamp.
    """
    __tablename__ = "ingestion_logs"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schema_type = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    uploaded_by = Column(String(255), nullable=False)
    records_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
