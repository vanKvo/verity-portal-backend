"""Unit tests for testing AssetAuditService layer functionality."""

import pytest
import datetime
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.inventory.models import InventoryModel, AssetStatus
from src.verity_portal.data_hub.procurement.models import ProcurementModel
from src.verity_portal.asset_audit.models import AssetViolationModel, AssetViolationType, AssetViolationStatus
from src.verity_portal.asset_audit.service import AssetAuditService

def test_get_violations_enriched_metadata(db_session: Session):
    """Verify that get_violations returns enriched inventory and procurement fields."""
    # 1. Seed Procurement
    proc = ProcurementModel(
        po_number="PO-TEST-123",
        status="ACTIVE"
    )
    # 2. Seed IT Inventory
    inv = InventoryModel(
        asset_tag="TAG-TEST-999",
        po_number="PO-TEST-123",
        status=AssetStatus.IN_USE,
        assigned_employee_id="EMP-ACTIVE-9",
        physical_location_site="Narnia Site",
        physical_location_room="Room 777"
    )
    # 3. Seed Anomaly Violation
    violation = AssetViolationModel(
        violation_type=AssetViolationType.GHOST_ASSET,
        asset_tag="TAG-TEST-999",
        po_number="PO-TEST-123",
        status=AssetViolationStatus.OPEN
    )
    
    db_session.add(proc)
    db_session.add(inv)
    db_session.add(violation)
    db_session.commit()

    # 4. Invoke service
    results = AssetAuditService.get_violations(db_session)
    
    # 5. Assertions
    assert len(results) >= 1
    target = next(v for v in results if v["asset_tag"] == "TAG-TEST-999")
    assert target["assigned_employee_id"] == "EMP-ACTIVE-9"
    assert target["inventory_status"] == "IN_USE"
    assert target["physical_location_site"] == "Narnia Site"
    assert target["physical_location_room"] == "Room 777"
    assert target["procurement_status"] == "ACTIVE"

def test_resolve_violation_updates_database(db_session: Session):
    """Verify that resolve_violation service call transitions status and sets justification."""
    # Seed violation
    violation = AssetViolationModel(
        violation_type=AssetViolationType.WASTED_SPEND,
        asset_tag=None,
        po_number="PO-WASTED-1",
        status=AssetViolationStatus.OPEN
    )
    db_session.add(violation)
    db_session.commit()

    # Invoke resolve
    success = AssetAuditService.resolve_violation(
        db_session, 
        violation_id=str(violation.id), 
        reason="PO was audited and cancelled manually"
    )
    
    # Assertions
    assert success is True
    updated = db_session.query(AssetViolationModel).filter_by(id=violation.id).first()
    assert updated.status == AssetViolationStatus.RESOLVED
    assert updated.resolution_reason == "PO was audited and cancelled manually"
