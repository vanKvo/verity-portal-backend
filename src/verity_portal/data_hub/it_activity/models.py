"""Database models for IT Activity records.

Provides the schema mapping for Active Directory or log server login exports.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Uuid
from sqlalchemy.sql import func
from src.verity_portal.core.database import Base


class ItActivityModel(Base):
    """Stores IT system login activities for compliance audits.

    Attributes:
        id: Unique UUID primary key.
        employee_id: Unique index column representing the employee identifier.
        last_system_login: The timestamp of the last logged system login.
        ip_address: Optional IP address used for the system access.
        system_name: Optional name of the IT system accessed.
        created_at: Timestamp showing when the row was created.
        updated_at: Timestamp showing when the row was last updated.
    """
    __tablename__ = "it_activity"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    last_system_login = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45), nullable=True)
    system_name = Column(String(100), nullable=True)
    user_name = Column(String(100), nullable=True)
    system_access_level = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
