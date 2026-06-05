import enum
import uuid
from sqlalchemy import Column, String, Enum as SqlEnum, DateTime, Uuid, ForeignKey
from sqlalchemy.sql import func
from src.verity_portal.core.database import Base

class AssetViolationType(str, enum.Enum):
    GHOST_ASSET = "GHOST_ASSET"
    WASTED_SPEND = "WASTED_SPEND"
    UNRECOVERED_ASSET = "UNRECOVERED_ASSET"

class AssetViolationStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"

class AssetViolationModel(Base):
    __tablename__ = "asset_violations"
    __table_args__ = {"schema": "verity"}

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    violation_type = Column(SqlEnum(AssetViolationType), nullable=False)
    asset_tag = Column(String(100), ForeignKey("verity.inventory.asset_tag"), nullable=True)
    po_number = Column(String(100), ForeignKey("verity.procurement.po_number"), nullable=True)
    
    status = Column(
        SqlEnum(AssetViolationStatus),
        default=AssetViolationStatus.OPEN,
        nullable=False
    )
    resolution_reason = Column(String(500), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
