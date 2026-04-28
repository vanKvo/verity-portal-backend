from abc import ABC, abstractmethod
import uuid

class StoragePort(ABC):
    @abstractmethod
    async def save_file(self, file_content: bytes, job_id: uuid.UUID, filename: str, subfolder: str = "staging") -> str:
        """
        Saves file content to the specified subfolder.
        Returns the storage path/key.
        """
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> bytes:
        """
        Retrieves file content from the specified path.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Deletes the file at the specified path.
        """
        pass

    @abstractmethod
    async def move_file(self, source_path: str, target_subfolder: str) -> str:
        """
        Moves a file from its current path to a different subfolder.
        Returns the new storage path/key.
        """
        pass
