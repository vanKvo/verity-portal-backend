"""Module containing business services for the Asset and PO Reconciliation Audit.

Coordinates database operations, performs outer joins across IT Inventory
and Procurement records, and processes manual audit remediation updates.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.verity_portal.asset_audit.models import AssetViolationModel, AssetViolationStatus
from src.verity_portal.data_hub.inventory.models import InventoryModel
from src.verity_portal.data_hub.procurement.models import ProcurementModel

logger = logging.getLogger(__name__)

class AssetAuditService:
    """Service to handle business logic for reconciling and resolving asset violations."""

    @staticmethod
    def get_violations(db: Session, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves paginated audit violations enriched with inventory and procurement metadata.

        Args:
            db: The current database transaction session.
            skip: The number of initial violations to bypass for pagination.
            limit: The maximum number of violations to retrieve.

        Returns:
            A list of dictionary objects representing enriched asset violations.
        """
        stmt = (
            select(
                AssetViolationModel,
                InventoryModel.assigned_employee_id,
                InventoryModel.status.label("inventory_status"),
                InventoryModel.physical_location_site,
                InventoryModel.physical_location_room,
                ProcurementModel.status.label("procurement_status")
            )
            .outerjoin(InventoryModel, AssetViolationModel.asset_tag == InventoryModel.asset_tag)
            .outerjoin(ProcurementModel, AssetViolationModel.po_number == ProcurementModel.po_number)
            .order_by(AssetViolationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        results = db.execute(stmt).all()
        violations: List[Dict[str, Any]] = []
        for row in results:
            violations.append({
                "id": str(row.AssetViolationModel.id),
                "violation_type": row.AssetViolationModel.violation_type.value,
                "asset_tag": row.AssetViolationModel.asset_tag,
                "po_number": row.AssetViolationModel.po_number,
                "status": row.AssetViolationModel.status.value,
                "resolution_reason": row.AssetViolationModel.resolution_reason,
                "resolved_by": row.AssetViolationModel.resolved_by,
                "resolved_at": row.AssetViolationModel.resolved_at.isoformat() if row.AssetViolationModel.resolved_at else None,
                "created_at": row.AssetViolationModel.created_at.isoformat() if row.AssetViolationModel.created_at else None,
                "updated_at": row.AssetViolationModel.updated_at.isoformat() if row.AssetViolationModel.updated_at else None,
                "assigned_employee_id": row.assigned_employee_id,
                "inventory_status": row.inventory_status.value if row.inventory_status else None,
                "physical_location_site": row.physical_location_site,
                "physical_location_room": row.physical_location_room,
                "procurement_status": row.procurement_status,
            })
        return violations

    @staticmethod
    def resolve_violation(db: Session, violation_id: str, reason: str, resolved_by: str = None) -> bool:
        """Resolves an open financial anomaly with manual auditor justification feedback.

        Args:
            db: The current database transaction session.
            violation_id: The UUID unique identifier of the target violation.
            reason: The manual justification text explaining how the violation was resolved.
            resolved_by: The username/email of the resolver.

        Returns:
            True if the target violation was successfully resolved, otherwise False.
        """
        try:
            target_id = uuid.UUID(violation_id) if isinstance(violation_id, str) else violation_id
        except ValueError:
            logger.error(f"Invalid UUID string provided: {violation_id}")
            return False

        violation = db.query(AssetViolationModel).filter_by(id=target_id).first()
        if not violation:
            return False
            
        violation.status = AssetViolationStatus.RESOLVED
        violation.resolution_reason = reason
        violation.resolved_by = resolved_by
        violation.resolved_at = func.now()
        db.commit()
        return True
