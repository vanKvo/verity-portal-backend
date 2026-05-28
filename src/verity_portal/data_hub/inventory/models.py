import enum
from sqlalchemy import Column, String, Enum as SqlEnum, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.verity_portal.core.database import Base

class AssetStatus(str, enum.Enum):
    IN_USE = "IN_USE"
    RETIRED = "RETIRED"
    LOST = "LOST"

class InventoryModel(Base):
    __tablename__ = "inventory"
    __table_args__ = {"schema": "verity"}

    asset_tag = Column(String(100), primary_key=True)
    po_number = Column(String(100), ForeignKey("verity.procurement.po_number"), nullable=True)
    serial_number = Column(String(100), nullable=True)
    assigned_employee_id = Column(String(50), ForeignKey("verity.personnel.employee_id"), nullable=True)
    status = Column(
        SqlEnum(AssetStatus),
        default=AssetStatus.IN_USE,
        nullable=False
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
