"""Orchestration service for the Data Hub.

This module coordinates master data manual upload workflows, S3 webhook 
synchronization events, column header parsing, and last-synchronized status queries,
acting as the single entrypoint for the business logic layer.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
import tempfile
import os
from contextlib import contextmanager
from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from numbers_parser import Document

from src.verity_portal.core.database import get_db, SessionLocal
from src.verity_portal.core.email import BaseEmailService, get_email_service
from src.verity_portal.core.file_parser import parse_file_to_df, extract_headers_from_file
from src.verity_portal.data_hub.core.retrieval import BaseRetrievalStrategy, RetrievalStrategyFactory
from src.verity_portal.data_hub.exceptions import IngestionRoutingError
from src.verity_portal.data_hub.personnel.models import PersonnelModel
from src.verity_portal.data_hub.personnel.service import PersonnelService
from src.verity_portal.data_hub.projects.models import ProjectModel
from src.verity_portal.data_hub.projects.service import ProjectService
from src.verity_portal.data_hub.procurement.models import ProcurementModel
from src.verity_portal.data_hub.procurement.service import ProcurementService
from src.verity_portal.data_hub.inventory.models import InventoryModel
from src.verity_portal.data_hub.inventory.service import InventoryService
from src.verity_portal.data_hub.it_activity.models import ItActivityModel
from src.verity_portal.data_hub.it_activity.service import ItActivityService
from src.verity_portal.data_hub.exceptions import MappingParseError
from src.verity_portal.data_hub.core.models import IngestionLogModel
from src.verity_portal.data_hub.personnel.models import PersonnelModel
from src.verity_portal.data_hub.it_activity.models import ItActivityModel
from src.verity_portal.leaver_audit.engine import LeaverMoverReconciliationEngine

logger = logging.getLogger(__name__)


class DataHubOrchestrationService:
    """Orchestrates ingestion coordination, data parsing, and dynamic domain routing."""

    def __init__(self, db: Session, email_service: Optional[BaseEmailService] = None) -> None:
        """Initializes the orchestration service with a database session wrapper.

        Args:
            db: The active database session.
            email_service: Optional custom email alerting service conforming to BaseEmailService.
        """
        self.db: Session = db
        self.email_service: BaseEmailService = email_service or get_email_service()

    async def extract_headers(self, strategy: BaseRetrievalStrategy) -> List[str]:
        """Business logic to pull clean column fields out of an inbound file strategy.

        Args:
            strategy: The active manual upload or S3 retrieval strategy.

        Returns:
            A list of clean column header strings.

        Raises:
            ValueError: If a numbers spreadsheet table structure is empty.
        """
        stream: Any = await strategy.retrieve_stream()
        return extract_headers_from_file(strategy.filename, stream)

    async def process_manual_upload(
        self, 
        strategy: BaseRetrievalStrategy, 
        mapping_str: Optional[str], 
        target_service_type: str,
        uploaded_by: str = "unknown"
    ) -> Dict[str, Any]:
        """Parses and executes targeted personnel or project manual data mapping workflows.

        Args:
            strategy: The active manual upload retrieval strategy.
            mapping_str: Optional JSON mapping string supplied by the frontend.
            target_service_type: Either 'personnel' or 'projects' to indicate target.
            uploaded_by: The username/email of the operator uploading the data.

        Returns:
            A results summary dictionary with counts of successful and failed rows.

        Raises:
            ValueError: If an invalid target service type is requested.
        """
        stream: Any = await strategy.retrieve_stream()
        df: pd.DataFrame = parse_file_to_df(strategy.filename, stream)
        try:
            column_mapping: Optional[Dict[str, str]] = json.loads(mapping_str) if mapping_str else None
        except json.JSONDecodeError as exc:
            raise MappingParseError(str(exc)) from exc
        
        if target_service_type == "personnel":
            res = PersonnelService(self.db).ingest_personnel_roster(df, column_mapping=column_mapping)
            self._trigger_leaver_mover_reconciliation_audit()
        elif target_service_type == "projects":
            res = ProjectService(self.db).ingest_projects(df, column_mapping=column_mapping)
        elif target_service_type == "procurement":
            res = ProcurementService(self.db).ingest_master_data(df, column_mapping=column_mapping)
            self._trigger_it_po_reconciliation_audit()
        elif target_service_type == "inventory":
            res = InventoryService(self.db).ingest_master_data(df, column_mapping=column_mapping)
            self._trigger_it_po_reconciliation_audit()
        elif target_service_type == "it_activity":
            res = ItActivityService(self.db).ingest_master_data(df, column_mapping=column_mapping)
            self._trigger_leaver_mover_reconciliation_audit()
        else:
            raise ValueError(f"Invalid target service type: {target_service_type}")

        # Log manual upload
        records_count = res.get("success_count", 0) if isinstance(res, dict) else 0
        log_entry = IngestionLogModel(
            schema_type=target_service_type,
            filename=strategy.filename,
            source="MANUAL",
            uploaded_by=uploaded_by,
            records_count=records_count
        )
        self.db.add(log_entry)
        self.db.commit()

        return res

    async def perform_s3_ingestion(self, bucket_name: str, object_key: str) -> None:
        """Orchestrates file streaming, database routing, and failure notification for S3 webhooks."""
        logger.info(f"Starting background S3 ingestion processing for s3://{bucket_name}/{object_key}")
        
        try:
            # 1. Isolate streaming and parsing
            strategy: BaseRetrievalStrategy = RetrievalStrategyFactory.get_s3_strategy(bucket_name, object_key)
            stream: Any = await strategy.retrieve_stream()
            df: pd.DataFrame = parse_file_to_df(strategy.filename, stream)
            
            # 2. Leverage an isolated session context manager (Refactored logic below)
            with self._get_db_session_ctx() as db_session:
                key_lower = object_key.lower()
                schema_type_str = ""
                
                # 3. Streamlined routing logic
                if any(term in key_lower for term in ["personnel", "hr"]):
                    result = PersonnelService(db_session).ingest_personnel_roster(df)
                    schema_type_str = "personnel"
                    logger.info(f"S3 Ingestion completed for Personnel: {result}")
                    self._trigger_leaver_mover_reconciliation_audit(db_session)
                elif any(term in key_lower for term in ["project", "projects"]):
                    result = ProjectService(db_session).ingest_projects(df)
                    schema_type_str = "projects"
                    logger.info(f"S3 Ingestion completed for Projects: {result}")
                elif any(term in key_lower for term in ["procurement"]):
                    result = ProcurementService(db_session).ingest_master_data(df)
                    schema_type_str = "procurement"
                    logger.info(f"S3 Ingestion completed for Procurement: {result}")
                    self._trigger_it_po_reconciliation_audit(db_session)
                elif any(term in key_lower for term in ["it_inventory", "it_asset", "it_assets"]):
                    result = InventoryService(db_session).ingest_master_data(df)
                    schema_type_str = "inventory"
                    logger.info(f"S3 Ingestion completed for IT Inventory: {result}")
                    self._trigger_it_po_reconciliation_audit(db_session)
                elif any(term in key_lower for term in ["it_activity", "access_log", "active_directory"]):
                    result = ItActivityService(db_session).ingest_master_data(df)
                    schema_type_str = "it_activity"
                    logger.info(f"S3 Ingestion completed for IT Activity: {result}")
                    self._trigger_leaver_mover_reconciliation_audit(db_session)
                else:
                    raise IngestionRoutingError(
                        filename=object_key,
                        detail = "\n".join([
                                "The document title must contain:",
                                "- 'hr' or 'personnel' for HR master record",
                                "- 'project' or 'projects' for Project Assignments",
                                "- 'procurement' for Procurement Data",
                                "- 'it_inventory', 'it_assets' or 'it_asset' for IT Hardware Inventory",
                                "- 'it_activity', 'access_log' or 'active_directory' for IT Activity Logs"])      
                    )

                # Log S3 Ingestion log
                records_count = result.get("success_count", 0) if isinstance(result, dict) else 0
                log_entry = IngestionLogModel(
                    schema_type=schema_type_str,
                    filename=object_key,
                    source="S3",
                    uploaded_by="SYSTEM",
                    records_count=records_count
                )
                db_session.add(log_entry)
                db_session.commit()
                    
        except Exception as exc:
            self._handle_ingestion_failure(bucket_name, object_key, exc)
            raise exc

    # --- Supporting Helper Methods to decompose the class responsibility ---

    @contextmanager
    def _get_db_session_ctx(self):
        """Context manager isolating the test vs. production DB lifecycle logic."""
        use_new_session = True
        try:
            if self.db and self.db.bind and self.db.bind.dialect.name == "sqlite":
                use_new_session = False
        except Exception as e:
            logger.error(f"Failed to check the current session: {e}")

        session = SessionLocal() if use_new_session else self.db
        try:
            yield session
        finally:
            if use_new_session:
                session.close()

    def _handle_ingestion_failure(self, bucket: str, key: str, exc: Exception) -> None:
        """Handles reporting and asynchronous alert notifications for visibility."""
        subject = f"ALERT: Data Hub S3 Ingestion Failure"
        body = (
            f"An error occurred during S3 ingestion processing.\n\n"
            f"S3 URI: s3://{bucket}/{key}\n"
            f"Error Details: {str(exc)}\n\n"
            f"Please review the system logs to diagnose and resolve this issue."
        )
        try:
            self.email_service.send_alert(subject, body)
        except Exception as email_err:
            logger.error(f"Failed to publish ingestion error notification: {email_err}")

    def _trigger_it_po_reconciliation_audit(self, db_session: Session = None) -> None:
        """Triggers the asset audit reconciliation engine if both inventory and procurement data exist."""
        session = db_session or self.db
        try:
            from src.verity_portal.data_hub.inventory.models import InventoryModel
            from src.verity_portal.data_hub.procurement.models import ProcurementModel
            from src.verity_portal.asset_audit.engine import AssetReconciliationEngine
            
            has_inventory = session.query(InventoryModel).first() is not None
            has_procurement = session.query(ProcurementModel).first() is not None
            
            if has_inventory and has_procurement:
                logger.info("Both IT Inventory and Procurement data present. Triggering Reconciliation Audit...")
                engine = AssetReconciliationEngine(session)
                engine.run_audit()
            else:
                logger.info(
                    f"Reconciliation Audit skipped: has_inventory={has_inventory}, "
                    f"has_procurement={has_procurement}. Both datasets must exist."
                )
        except Exception as e:
            logger.error(f"Failed to execute automated reconciliation audit: {e}")

    def _trigger_leaver_mover_reconciliation_audit(self, db_session: Session = None) -> None:
        """Triggers the leaver/mover access reconciliation engine if both personnel and it_activity exist.

        Args:
            db_session: Optional active DB session to utilize inside contextual worker.
        """
        session = db_session or self.db
        try:
            
            has_personnel = session.query(PersonnelModel).first() is not None
            has_it_activity = session.query(ItActivityModel).first() is not None
            
            if has_personnel and has_it_activity:
                logger.info("Both Personnel and IT Activity data present. Triggering Leaver/Mover Reconciliation Audit...")
                engine = LeaverMoverReconciliationEngine(session)
                engine.run_audit()
            else:
                logger.info(
                    f"Leaver/Mover Audit skipped: has_personnel={has_personnel}, "
                    f"has_it_activity={has_it_activity}. Both datasets must exist."
                )
        except Exception as e:
            logger.error(f"Failed to execute automated leaver/mover reconciliation audit: {e}")

    def get_sync_status(self) -> Dict[str, Optional[str]]:
        """Retrieves the last sync/update ISO formatted timestamps for master records.

        Returns:
            A dictionary containing personnel and project last sync markers in ISO string
            format, or None if no synchronization timestamps exist in the database.
        """
        personnel_last: Any = self.db.query(func.max(PersonnelModel.updated_at)).scalar()
        projects_last: Any = self.db.query(func.max(ProjectModel.updated_at)).scalar()
        procurement_last: Any = self.db.query(func.max(ProcurementModel.updated_at)).scalar()
        inventory_last: Any = self.db.query(func.max(InventoryModel.updated_at)).scalar()
        it_activity_last: Any = self.db.query(func.max(ItActivityModel.updated_at)).scalar()

        return {
            "personnel_last_sync": personnel_last.isoformat() if personnel_last else None,
            "projects_last_sync": projects_last.isoformat() if projects_last else None,
            "procurement_last_sync": procurement_last.isoformat() if procurement_last else None,
            "inventory_last_sync": inventory_last.isoformat() if inventory_last else None,
            "it_activity_last_sync": it_activity_last.isoformat() if it_activity_last else None
        }


def get_orchestration_service(db: Session = Depends(get_db)) -> DataHubOrchestrationService:
    """FastAPI Dependency injector that constructs and returns the DataHubOrchestrationService."""
    return DataHubOrchestrationService(db)