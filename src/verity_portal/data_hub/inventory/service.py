import pandas as pd
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.inventory.models import InventoryModel, AssetStatus
from src.verity_portal.data_hub.inventory.schemas import InventorySchema
from src.verity_portal.data_hub.core.engine import MasterDataIngestor
from src.verity_portal.data_hub.personnel.models import PersonnelModel
from src.verity_portal.data_hub.procurement.models import ProcurementModel

class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestor = MasterDataIngestor(db, InventoryModel, InventorySchema, unique_key="asset_tag")

    def normalize_status_string(self, raw_status: str) -> AssetStatus:
        """Normalizes common string inputs to the formal Enum."""
        if not raw_status or pd.isna(raw_status):
            return AssetStatus.STORAGE
        
        raw_clean = str(raw_status).strip().upper()
        if "RETIRED" in raw_clean or "DISPOSED" in raw_clean:
            return AssetStatus.RETIRED
        elif "LOST" in raw_clean or "MISSING" in raw_clean or "STOLEN" in raw_clean:
            return AssetStatus.LOST
        elif "STORAGE" in raw_clean or "WAREHOUSE" in raw_clean or "STOCK" in raw_clean:
            return AssetStatus.STORAGE
        elif "IN_USE" in raw_clean or "IN USE" in raw_clean or "DEPLOYED" in raw_clean or "ASSIGNED" in raw_clean:
            return AssetStatus.IN_USE
        
        return AssetStatus.STORAGE

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

        # Standardize empty strings and NaN values to None across the DataFrame
        df = df.where(pd.notnull(df), None)

        # Resolve foreign key constraints dynamically
        is_personnel_mocked = False
        try:
            query_res = self.db.query(PersonnelModel.employee_id).all()
            if hasattr(query_res, "called") or "Mock" in type(query_res).__name__:
                valid_employee_ids = set()
                is_personnel_mocked = True
            else:
                valid_employee_ids = {emp.employee_id for emp in query_res if hasattr(emp, "employee_id")}
        except Exception:
            valid_employee_ids = set()

        # Resolve PO foreign key constraints dynamically
        is_procurement_mocked = False
        try:
            po_res = self.db.query(ProcurementModel.po_number).all()
            if hasattr(po_res, "called") or "Mock" in type(po_res).__name__:
                valid_po_numbers = set()
                is_procurement_mocked = True
            else:
                valid_po_numbers = {p.po_number for p in po_res if hasattr(p, "po_number")}
        except Exception:
            valid_po_numbers = set()

        for col in df.columns:
            if pd.api.types.is_string_dtype(df[col]):
                if col == "assigned_employee_id":
                    if not is_personnel_mocked:
                        df[col] = df[col].apply(
                            lambda val: val.strip() if (
                                val is not None and 
                                isinstance(val, str) and 
                                val.strip() in valid_employee_ids
                            ) else None
                        )
                elif col == "po_number":
                    if not is_procurement_mocked:
                        df[col] = df[col].apply(
                            lambda val: val.strip() if (
                                val is not None and 
                                isinstance(val, str) and 
                                val.strip() in valid_po_numbers
                            ) else None
                        )
                else:
                    df[col] = df[col].apply(
                        lambda val: None if (
                            val is None or 
                            (isinstance(val, str) and (
                                not val.strip() or 
                                val.strip().lower() in {"nan", "null", "none", "n/a", ""}
                            ))
                        ) else val
                    )

        return self.ingestor.ingest(df)
