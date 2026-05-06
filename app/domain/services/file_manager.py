import uuid
import io
import os
import pandas as pd
from typing import Dict
from sqlalchemy.orm import Session
from app.domain.ports.storage_port import StoragePort
from app.infrastructure.adapters.database.models import FileMetadataModel, IntakeRecordModel

class FileManager:
    def __init__(self, storage_port: StoragePort, db: Session):
        self.storage_port = storage_port
        self.db = db
        self.MAX_SIZE_MB = 50

    async def ingest_file(self, content: bytes, job_id: uuid.UUID, filename: str) -> uuid.UUID:
        if len(content) > self.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File size exceeds {self.MAX_SIZE_MB}MB limit")
            
        # Save to storage
        storage_path = await self.storage_port.save_file(content, job_id, filename, subfolder="staging")
        
        # Save metadata
        file_metadata = FileMetadataModel(
            job_id=job_id,
            original_name=filename,
            storage_path=storage_path,
            status="STAGED"
        )
        self.db.add(file_metadata)
        self.db.commit()
        self.db.refresh(file_metadata)
        
        return file_metadata.file_id

    async def archive_file(self, job_id: uuid.UUID) -> bool:
        file_metadata = self.db.query(FileMetadataModel).filter(FileMetadataModel.job_id == job_id).first()
        if not file_metadata:
            return False
            
        # Move file in storage
        new_path = await self.storage_port.move_file(file_metadata.storage_path, target_subfolder="archive")
        
        # Update metadata
        file_metadata.storage_path = new_path
        file_metadata.status = "ARCHIVED"
        self.db.commit()
        
        return True

    async def confirm_and_ingest(self, job_id: uuid.UUID, mappings: Dict[str, str]) -> int:
        file_metadata = self.db.query(FileMetadataModel).filter(FileMetadataModel.job_id == job_id).first()
        if not file_metadata:
            raise ValueError("No file found for this job ID")
            
        content = await self.storage_port.get_file(file_metadata.storage_path)
        
        _, ext = os.path.splitext(file_metadata.original_name)
        
        if ext.lower() == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
            
        # Filter and rename columns based on mappings
        mapped_df = df[list(mappings.keys())].rename(columns=mappings)
        
        # Standardize dates: Any column ending in '_date' should be converted to ISO format
        for col in mapped_df.columns:
            if col.lower().endswith("_date"):
                try:
                    mapped_df[col] = pd.to_datetime(mapped_df[col]).dt.strftime('%Y-%m-%d')
                except Exception:
                    # If parsing fails, leave as is (or handle as needed)
                    pass

        # Convert to list of dicts for JSON storage
        records_data = mapped_df.to_dict(orient="records")
        
        # Save records
        for record in records_data:
            db_record = IntakeRecordModel(
                job_id=job_id,
                data=record
            )
            self.db.add(db_record)
            
        file_metadata.status = "PROCESSED"
        self.db.commit()
        
        return len(records_data)
