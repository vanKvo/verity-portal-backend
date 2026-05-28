import uuid
from sqlalchemy import Column, String, Uuid, DateTime, Integer, Float
from sqlalchemy.sql import func
from src.verity_portal.core.database import Base

class ProcurementModel(Base):
    __tablename__ = "procurement"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    purchase_date = Column(DateTime(timezone=True), nullable=True)
    vendor = Column(String(255), nullable=True)
    asset_category = Column(String(100), nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
