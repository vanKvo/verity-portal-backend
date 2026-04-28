import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from app.domain.services.file_manager import FileManager
from app.domain.ports.storage_port import StoragePort

@pytest.fixture
def mock_storage():
    return AsyncMock(spec=StoragePort)

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def file_manager(mock_storage, mock_db):
    return FileManager(storage_port=mock_storage, db=mock_db)

@pytest.mark.asyncio
async def test_ingest_file_saves_to_storage_and_db(file_manager, mock_storage, mock_db):
    job_id = uuid.uuid4()
    filename = "test.csv"
    content = b"content"
    
    mock_storage.save_file.return_value = "/staging/safe_test.csv"
    
    # Mock db.add to assign an ID to the object
    def mock_add(obj):
        obj.file_id = uuid.uuid4()
    mock_db.add.side_effect = mock_add
    
    file_id = await file_manager.ingest_file(content, job_id, filename)
    
    assert isinstance(file_id, uuid.UUID)
    mock_storage.save_file.assert_called_once_with(content, job_id, filename, subfolder="staging")
    assert mock_db.add.called
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_ingest_file_rejects_large_files(file_manager):
    job_id = uuid.uuid4()
    filename = "large.csv"
    # 50MB = 50 * 1024 * 1024 bytes. Let's send 51MB.
    large_content = b"0" * (51 * 1024 * 1024)
    
    with pytest.raises(ValueError, match="File size exceeds 50MB limit"):
        await file_manager.ingest_file(large_content, job_id, filename)

@pytest.mark.asyncio
async def test_archive_file_coordinates_move_and_update(file_manager, mock_storage, mock_db):
    job_id = uuid.uuid4()
    # Mocking DB query to return a file metadata object
    mock_file = MagicMock()
    mock_file.storage_path = "/staging/test.csv"
    mock_file.status = "STAGED"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_file
    
    mock_storage.move_file.return_value = "/archive/test.csv"
    
    success = await file_manager.archive_file(job_id)
    
    assert success is True
    mock_storage.move_file.assert_called_once_with("/staging/test.csv", target_subfolder="archive")
    assert mock_file.status == "ARCHIVED"
    assert mock_file.storage_path == "/archive/test.csv"
    assert mock_db.commit.called
