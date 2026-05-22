import pandas as pd
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.projects.models import ProjectModel
from src.verity_portal.data_hub.projects.schemas import ProjectMasterSchema
from src.verity_portal.data_hub.core.engine import MasterDataIngestor

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestor = MasterDataIngestor(db, ProjectModel, ProjectMasterSchema, unique_key="project_id")

    def ingest_projects(self, df: pd.DataFrame, column_mapping: dict = None):
        """Ingests project master data (Sensitivity)."""
        if column_mapping:
            rename_map = { v: k for k, v in column_mapping.items() if v }
            df = df.rename(columns=rename_map)
        else:
            # Auto-map columns if not explicitly provided (e.g. for S3 auto sync)
            # 1. Generic normalization: lowercase, strip, replace spaces/hyphens with underscores
            df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(r'[\s\-]+', '_', regex=True)
            
            # 2. Specific semantic mappings that simple normalization doesn't catch
            semantic_mappings = {
                "project_name": "name",
                "sensitivity_level": "sensitivity"
            }
            df = df.rename(columns=semantic_mappings)
            
        return self.ingestor.ingest(df)
