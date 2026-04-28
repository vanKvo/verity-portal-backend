import uuid
from sqlalchemy.orm import Session
from app.domain.ports.storage_port import StoragePort
from app.infrastructure.adapters.database.models import FileMetadataModel

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
