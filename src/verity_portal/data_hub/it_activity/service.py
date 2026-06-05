"""Service layer handling IT Activity ingestion and mapping.

Coordinates log parsing, column translation, date validation, and transactional ingestion.
"""

from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.it_activity.models import ItActivityModel
from src.verity_portal.data_hub.it_activity.schemas import ItActivityMasterSchema
from src.verity_portal.data_hub.core.engine import MasterDataIngestor


class ItActivityService:
    """Provides methods to process, parse, and commit IT Activity logs."""

    def __init__(self, db: Session) -> None:
        """Initializes the IT Activity service with a database session wrapper.

        Args:
            db: The active database session.
        """
        self.db: Session = db
        self.ingestor = MasterDataIngestor(
            db=db,
            model=ItActivityModel,
            schema=ItActivityMasterSchema,
            unique_key="employee_id"
        )

    def ingest_master_data(self, df: pd.DataFrame, column_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Pre-processes and ingests IT Activity logs.

        Args:
            df: Inbound pandas DataFrame representing activity records.
            column_mapping: Optional header translation mapping from frontend.

        Returns:
            Ingestion results containing row counts and failures.
        """
        if column_mapping:
            rename_map = {v: k for k, v in column_mapping.items() if v}
            df = df.rename(columns=rename_map)
        else:
            # Auto-map columns if not explicitly provided
            df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(r'[\s\-]+', '_', regex=True)
            
            semantic_mappings = {
                "login_date": "last_system_login",
                "login_time": "last_system_login",
                "login": "last_system_login",
                "timestamp": "last_system_login",
                "ip": "ip_address",
                "system": "system_name",
                "system/application": "system_name",
                "username": "user_name",
                "user": "user_name",
                "access_level": "system_access_level",
                "access": "system_access_level",
                "level": "system_access_level"
            }
            df = df.rename(columns=semantic_mappings)

        # Handle date conversion for last_system_login
        if "last_system_login" in df.columns:
            df["last_system_login"] = pd.to_datetime(df["last_system_login"])
            # Replace NaT with None
            df["last_system_login"] = df["last_system_login"].where(df["last_system_login"].notnull(), None)

        return self.ingestor.ingest(df)
