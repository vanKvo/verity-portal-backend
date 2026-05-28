import pandas as pd
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.inventory.models import InventoryModel, AssetStatus
from src.verity_portal.data_hub.inventory.schemas import InventorySchema
from src.verity_portal.data_hub.core.engine import MasterDataIngestor

class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestor = MasterDataIngestor(db, InventoryModel, InventorySchema, unique_key="asset_tag")

    def normalize_status_string(self, raw_status: str) -> AssetStatus:
        """Normalizes common string inputs to the formal Enum."""
        if not raw_status or pd.isna(raw_status):
            return AssetStatus.IN_USE
        
        raw_clean = str(raw_status).strip().upper()
        if "RETIRED" in raw_clean or "DISPOSED" in raw_clean:
            return AssetStatus.RETIRED
        elif "LOST" in raw_clean or "MISSING" in raw_clean or "STOLEN" in raw_clean:
            return AssetStatus.LOST
        
        return AssetStatus.IN_USE

    def ingest_master_data(self, df: pd.DataFrame, column_mapping: dict = None):
        """Pre-processes and ingests Inventory master data."""
        if column_mapping:
            rename_map = { v: k for k, v in column_mapping.items() if v }
            df = df.rename(columns=rename_map)
        else:
            # Auto-map columns if not explicitly provided
            df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(r'[\s\-]+', '_', regex=True)
            
            semantic_mappings = {
                "po": "po_number",
                "assigned_to": "assigned_employee_id"
            }
            df = df.rename(columns=semantic_mappings)
        
        # Normalize status
        if "status" in df.columns:
            df["status"] = df["status"].apply(lambda x: self.normalize_status_string(x))

        return self.ingestor.ingest(df)
