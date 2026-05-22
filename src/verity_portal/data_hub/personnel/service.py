import pandas as pd
from sqlalchemy.orm import Session
from thefuzz import process
from src.verity_portal.data_hub.personnel.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.data_hub.personnel.schemas import PersonnelMasterSchema
from src.verity_portal.data_hub.core.engine import MasterDataIngestor

class PersonnelService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestor = MasterDataIngestor(db, PersonnelModel, PersonnelMasterSchema, unique_key="employee_id")

    def normalize_citizenship_string(self, raw_status: str) -> CitizenshipStatus:
        """Uses fuzzy matching to map raw strings to the CitizenshipStatus ENUM."""
        if not raw_status or pd.isna(raw_status):
            return CitizenshipStatus.UNKNOWN
            
        choices = {
            "US Citizen": CitizenshipStatus.US_CITIZEN,
            "USA": CitizenshipStatus.US_CITIZEN,
            "United States": CitizenshipStatus.US_CITIZEN,
            "Permanent Resident": CitizenshipStatus.PERMANENT_RESIDENT,
            "Green Card": CitizenshipStatus.PERMANENT_RESIDENT,
            "Foreign National": CitizenshipStatus.FOREIGN_NATIONAL,
            "Non-US": CitizenshipStatus.FOREIGN_NATIONAL,
        }
        
        # Exact match check first
        for key, enum_val in choices.items():
            if raw_status.lower() == key.lower():
                return enum_val
                
        # Fuzzy match
        match, score = process.extractOne(raw_status, choices.keys())
        if score > 80:
            return choices[match]
            
        return CitizenshipStatus.UNKNOWN

    def ingest_personnel_roster(self, df: pd.DataFrame, column_mapping: dict = None):
        """Pre-processes and ingests HR master data."""
        if column_mapping:
            # Reverse the mapping to use for renaming: { "file_column": "system_column" }
            # Actually, the mapper usually gives { "system_column": "file_column" }
            # So we rename file_column to system_column
            rename_map = { v: k for k, v in column_mapping.items() if v }
            df = df.rename(columns=rename_map)
        else:
            # Auto-map columns if not explicitly provided (e.g. for S3 auto sync)
            # 1. Generic normalization: lowercase, strip, replace spaces/hyphens with underscores
            df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(r'[\s\-]+', '_', regex=True)
            
            # 2. Specific semantic mappings that simple normalization doesn't catch
            semantic_mappings = {
                "citizenship": "citizenship_status"
            }
            df = df.rename(columns=semantic_mappings)

        # Normalize citizenship column if it exists
        if "citizenship_status" in df.columns:
            df["citizenship_status"] = df["citizenship_status"].apply(
                lambda x: self.normalize_citizenship_string(str(x))
            )
        
        # Handle date conversion for termination_date
        if "termination_date" in df.columns:
            df["termination_date"] = pd.to_datetime(df["termination_date"]).dt.date
            # Replace NaT with None
            df["termination_date"] = df["termination_date"].where(df["termination_date"].notnull(), None)

        return self.ingestor.ingest(df)
