import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, not_, outerjoin
from src.verity_portal.data_hub.inventory.models import InventoryModel, AssetStatus
from src.verity_portal.data_hub.procurement.models import ProcurementModel
from src.verity_portal.data_hub.personnel.models import PersonnelModel
from src.verity_portal.asset_audit.models import AssetViolationModel, AssetViolationType, AssetViolationStatus
from src.verity_portal.core.email import BaseEmailService, get_email_service

logger = logging.getLogger(__name__)

class AssetReconciliationEngine:
    def __init__(self, db: Session, email_service: Optional[BaseEmailService] = None):
        self.db = db
        self.email_service = email_service or get_email_service()

    def run_audit(self):
        """Executes the reconciliation engine to detect financial and compliance anomalies."""
        logger.info("Starting Asset Reconciliation Audit...")
        
        ghost_assets = self._detect_ghost_assets()
        wasted_spend = self._detect_wasted_spend()
        unrecovered_assets = self._detect_unrecovered_assets()
        
        self.db.commit()
        
        if ghost_assets > 0 or unrecovered_assets > 0:
            self._notify_it_department(ghost_assets, unrecovered_assets)
            
        if wasted_spend > 0:
            self._notify_finance_department(wasted_spend)

            
        logger.info(
            f"Audit completed. Found {ghost_assets} Ghost Assets, "
            f"{wasted_spend} Wasted Spend anomalies, and {unrecovered_assets} Unrecovered Assets."
        )
        return {
            "ghost_assets": ghost_assets, 
            "wasted_spend": wasted_spend,
            "unrecovered_assets": unrecovered_assets
        }

    def _detect_ghost_assets(self) -> int:
        """Finds active IT inventory that has no associated financial Procurement record."""
        # Query: Inventory status IN_USE, and either po_number is None or po_number not in Procurement
        subquery = select(ProcurementModel.po_number)
        
        stmt = select(InventoryModel).where(
            InventoryModel.status == AssetStatus.IN_USE,
            not_(InventoryModel.po_number.in_(subquery))
        )
        
        ghosts = self.db.execute(stmt).scalars().all()
        count = 0
        
        for asset in ghosts:
            # Check if violation already exists and is open
            existing = self.db.query(AssetViolationModel).filter_by(
                asset_tag=asset.asset_tag, 
                violation_type=AssetViolationType.GHOST_ASSET,
                status=AssetViolationStatus.OPEN
            ).first()
            
            if not existing:
                violation = AssetViolationModel(
                    violation_type=AssetViolationType.GHOST_ASSET,
                    asset_tag=asset.asset_tag,
                    po_number=asset.po_number
                )
                self.db.add(violation)
                count += 1
                
        return count

    def _detect_wasted_spend(self) -> int:
        """Finds retired/lost IT inventory that still has an active financial Procurement record."""
        # Query: Inventory status is RETIRED/LOST joined with Procurement status ACTIVE
        stmt = (
            select(InventoryModel, ProcurementModel)
            .join(ProcurementModel, InventoryModel.po_number == ProcurementModel.po_number)
            .where(
                InventoryModel.status.in_([AssetStatus.RETIRED, AssetStatus.LOST]),
                ProcurementModel.status.ilike("ACTIVE%")
            )
        )
        
        results = self.db.execute(stmt).all()
        count = 0
        
        for inventory, procurement in results:
            existing = self.db.query(AssetViolationModel).filter_by(
                po_number=procurement.po_number, 
                violation_type=AssetViolationType.WASTED_SPEND,
                status=AssetViolationStatus.OPEN
            ).first()
            
            if not existing:
                violation = AssetViolationModel(
                    violation_type=AssetViolationType.WASTED_SPEND,
                    asset_tag=inventory.asset_tag,
                    po_number=procurement.po_number
                )
                self.db.add(violation)
                count += 1
                
        return count

    def _detect_unrecovered_assets(self) -> int:
        """Finds assets still marked IN_USE but assigned to terminated employees."""
        stmt = (
            select(InventoryModel, PersonnelModel)
            .join(PersonnelModel, InventoryModel.assigned_employee_id == PersonnelModel.employee_id)
            .where(
                InventoryModel.status == AssetStatus.IN_USE,
                PersonnelModel.termination_date.isnot(None)
            )
        )
        
        results = self.db.execute(stmt).all()
        count = 0
        
        for inventory, personnel in results:
            existing = self.db.query(AssetViolationModel).filter_by(
                asset_tag=inventory.asset_tag,
                violation_type=AssetViolationType.UNRECOVERED_ASSET,
                status=AssetViolationStatus.OPEN
            ).first()
            
            if not existing:
                violation = AssetViolationModel(
                    violation_type=AssetViolationType.UNRECOVERED_ASSET,
                    asset_tag=inventory.asset_tag,
                    po_number=inventory.po_number
                )
                self.db.add(violation)
                count += 1
                
        return count

    def _notify_it_department(self, ghost_asset_count: int, unrecovered_asset_count: int):
        subject = "Action Required: Ghost Assets Detected"
        body = f"The Verity Portal Asset Reconciliation Engine detected {ghost_asset_count} new Ghost Asset(s) and {unrecovered_asset_count} active asset(s) assigned to terminated employees.\nPlease review the Audit Dashboard to physically locate these devices and coordinate with Finance for PO creation."
        try:
            if self.email_service:
                self.email_service.send_alert(subject, body)
        except Exception as e:
            logger.error(f"Failed to send IT notification: {e}")

    def _notify_finance_department(self, count: int):
        subject = "Action Required: Wasted Spend Detected"
        body = f"The Verity Portal Asset Reconciliation Engine detected {count} new Wasted Spend anomaly/anomalies.\nPlease review the Audit Dashboard. You may be paying maintenance for assets that IT has marked as RETIRED."
        try:
            if self.email_service:
                self.email_service.send_alert(subject, body)
        except Exception as e:
            logger.error(f"Failed to send Finance notification: {e}")

