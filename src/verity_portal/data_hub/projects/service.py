import pandas as pd
from sqlalchemy.orm import Session
from src.verity_portal.data_hub.projects.models import ProjectModel
from src.verity_portal.data_hub.projects.schemas import ProjectMasterSchema
from src.verity_portal.data_hub.core.ingestion import MasterDataIngestor

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestor = MasterDataIngestor(db, ProjectModel, ProjectMasterSchema, unique_key="project_id")

    def ingest_projects(self, df: pd.DataFrame, column_mapping: dict = None):
        """Ingests project master data (Sensitivity)."""
        if column_mapping:
            rename_map = { v: k for k, v in column_mapping.items() if v }
            df = df.rename(columns=rename_map)
            
        return self.ingestor.ingest(df)
