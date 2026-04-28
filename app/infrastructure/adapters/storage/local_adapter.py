import os
import aiofiles
import uuid
from pathlib import Path
from app.domain.ports.storage_port import StoragePort

class LocalFileSystemAdapter(StoragePort):
    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        # Ensure base directories exist
        (self.base_path / "staging").mkdir(parents=True, exist_ok=True)
        (self.base_path / "archive").mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_content: bytes, job_id: uuid.UUID, filename: str, subfolder: str = "staging") -> str:
        folder = self.base_path / subfolder
        folder.mkdir(parents=True, exist_ok=True)
        
        # We use a UUID-based filename to prevent collisions and directory traversal
        file_ext = Path(filename).suffix
        safe_filename = f"{job_id}{file_ext}"
        file_path = folder / safe_filename
        
        async with aiofiles.open(file_path, mode='wb') as f:
            await f.write(file_content)
        
        return str(file_path)

    async def get_file(self, file_path: str) -> bytes:
        async with aiofiles.open(file_path, mode='rb') as f:
            return await f.read()

    async def delete_file(self, file_path: str) -> bool:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False

    async def move_file(self, source_path: str, target_subfolder: str) -> str:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
            
        target_folder = self.base_path / target_subfolder
        target_folder.mkdir(parents=True, exist_ok=True)
        
        target_path = target_folder / source.name
        os.rename(source, target_path)
        
        return str(target_path)
