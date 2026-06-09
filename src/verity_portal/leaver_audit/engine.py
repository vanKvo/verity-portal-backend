"""Audit engine for Leaver/Mover Access reconciliation.

Cross-references HR Personnel terminations and system log activities to detect post-termination login events.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, Date
from src.verity_portal.data_hub.personnel.models import PersonnelModel
from src.verity_portal.data_hub.it_activity.models import ItActivityModel
from src.verity_portal.leaver_audit.models import LeaverViolationModel, LeaverViolationStatus
from src.verity_portal.core.email import BaseEmailService, get_email_service

logger = logging.getLogger(__name__)


class LeaverMoverReconciliationEngine:
    """Reconciles system activity with HR terminations to persist and alert on access violations."""

    def __init__(self, db: Session, email_service: Optional[BaseEmailService] = None) -> None:
        """Initializes the reconciliation engine with database and email service bindings.

        Args:
            db: The active database session.
            email_service: Optional custom email service wrapper.
        """
        self.db: Session = db
        self.email_service: BaseEmailService = email_service or get_email_service()

    def run_audit(self) -> Dict[str, int]:
        """Executes the leaver/mover audit comparison query.

        Detects system access occurring strictly after termination, records
        violations in the database, and publishes email alerts.

        Returns:
            A dictionary summarizing the count of new violations created.
        """
        logger.info("Starting Leaver/Mover Access Reconciliation Audit...")
        new_violations = self._detect_violations()
        self.db.commit()

        if new_violations > 0:
            self._notify_security_office(new_violations)

        logger.info(f"Leaver/Mover audit complete. Created {new_violations} new violations.")
        return {"new_violations": new_violations}

    def _detect_violations(self) -> int:
        """Compares termination dates against system logins to insert open violations.

        Returns:
            The number of newly created violations.
        """
        stmt = (
            select(ItActivityModel, PersonnelModel)
            .join(PersonnelModel, ItActivityModel.employee_id == PersonnelModel.employee_id)
            .where(
                PersonnelModel.termination_date.isnot(None),
                ItActivityModel.last_system_login > PersonnelModel.termination_date
            )
        )

        results = self.db.execute(stmt).all()
        count = 0

        for it_activity, personnel in results:
            # Check if violation already exists and is open
            existing = self.db.query(LeaverViolationModel).filter_by(
                employee_id=personnel.employee_id,
                last_system_login=it_activity.last_system_login,
                status=LeaverViolationStatus.OPEN
            ).first()

            if not existing:
                violation = LeaverViolationModel(
                    employee_id=personnel.employee_id,
                    hr_termination_date=personnel.termination_date,
                    last_system_login=it_activity.last_system_login,
                    status=LeaverViolationStatus.OPEN,
                    system_name=it_activity.system_name,
                    ip_address=it_activity.ip_address
                )
                self.db.add(violation)
                count += 1

        return count

    def _notify_security_office(self, count: int) -> None:
        """Dispatches email notification regarding the detected access violations.

        Args:
            count: Number of violations detected.
        """
        subject = "SECURITY ALERT: Post-Termination Access Detected"
        body = (
            f"The Leaver/Mover Access Reconciliation Engine detected {count} new access violation(s).\n\n"
            f"Please log into the Verity Portal and navigate to the Leaver/Mover Audit Dashboard "
            f"to review the active violations and take remediation action."
        )
        try:
            self.email_service.send_alert(subject, body)
        except Exception as e:
            logger.error(f"Failed to send leaver access notification email: {e}")
