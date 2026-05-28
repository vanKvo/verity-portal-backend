import pytest
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.inventory.models import InventoryModel, AssetStatus
from src.verity_portal.data_hub.procurement.models import ProcurementModel
from src.verity_portal.asset_audit.models import AssetViolationModel, AssetViolationType, AssetViolationStatus
from src.verity_portal.asset_audit.engine import AssetReconciliationEngine

def test_reconciliation_detects_ghost_asset(db_session: Session):
    """Verify the engine identifies active hardware lacking financial procurement records."""
    # Seed IT Asset with no PO
    inventory = InventoryModel(
        asset_tag="MAC-123",
        po_number=None,
        status=AssetStatus.IN_USE
    )
    db_session.add(inventory)
    db_session.commit()

    engine = AssetReconciliationEngine(db_session, email_service=None) # Disabling email in tests
    engine.run_audit()

    violation = db_session.query(AssetViolationModel).filter_by(asset_tag="MAC-123").first()
    assert violation is not None
    assert violation.violation_type == AssetViolationType.GHOST_ASSET
    assert violation.status == AssetViolationStatus.OPEN

def test_reconciliation_detects_wasted_spend(db_session: Session):
    """Verify the engine identifies active financial contracts for retired physical hardware."""
    # Seed retired IT Asset linked to active PO
    procurement = ProcurementModel(
        po_number="PO-ACTIVE-1",
        status="ACTIVE"
    )
    inventory = InventoryModel(
        asset_tag="LAPTOP-OLD",
        po_number="PO-ACTIVE-1",
        status=AssetStatus.RETIRED
    )
    db_session.add(procurement)
    db_session.add(inventory)
    db_session.commit()

    engine = AssetReconciliationEngine(db_session, email_service=None)
    engine.run_audit()

    violation = db_session.query(AssetViolationModel).filter_by(po_number="PO-ACTIVE-1").first()
    assert violation is not None
    assert violation.violation_type == AssetViolationType.WASTED_SPEND
    assert violation.status == AssetViolationStatus.OPEN
