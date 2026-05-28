import pandas as pd
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.procurement.models import ProcurementModel
from src.verity_portal.data_hub.procurement.schemas import ProcurementSchema
from src.verity_portal.data_hub.core.engine import MasterDataIngestor

class ProcurementService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestor = MasterDataIngestor(db, ProcurementModel, ProcurementSchema, unique_key="po_number")

    def ingest_master_data(self, df: pd.DataFrame, column_mapping: dict = None):
        """Pre-processes and ingests Procurement PO master data."""
        if column_mapping:
            rename_map = { v: k for k, v in column_mapping.items() if v }
            df = df.rename(columns=rename_map)
        else:
            # Auto-map columns if not explicitly provided
            df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(r'[\s\-]+', '_', regex=True)
            
            # Semantic mappings
            semantic_mappings = {
                "vendor_name": "vendor"
            }
            df = df.rename(columns=semantic_mappings)
        
        # Handle date conversion
        if "purchase_date" in df.columns:
            df["purchase_date"] = pd.to_datetime(df["purchase_date"])
            df["purchase_date"] = df["purchase_date"].where(df["purchase_date"].notnull(), None)

        return self.ingestor.ingest(df)
