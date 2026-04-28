import pytest
import uuid
import os
from pathlib import Path
from app.infrastructure.adapters.storage.local_adapter import LocalFileSystemAdapter

@pytest.fixture
def temp_storage(tmp_path):
    return LocalFileSystemAdapter(base_path=str(tmp_path))

@pytest.mark.asyncio
async def test_save_file_writes_to_disk(temp_storage, tmp_path):
    job_id = uuid.uuid4()
    filename = "test.csv"
    content = b"header1,header2\nvalue1,value2"
    
    storage_path = await temp_storage.save_file(content, job_id, filename)
    
    assert storage_path is not None
    assert os.path.exists(storage_path)
    with open(storage_path, "rb") as f:
        assert f.read() == content

@pytest.mark.asyncio
async def test_delete_file_removes_from_disk(temp_storage):
    job_id = uuid.uuid4()
    filename = "delete_me.csv"
    content = b"content"
    
    storage_path = await temp_storage.save_file(content, job_id, filename)
    assert os.path.exists(storage_path)
    
    success = await temp_storage.delete_file(storage_path)
    assert success is True
    assert not os.path.exists(storage_path)

@pytest.mark.asyncio
async def test_move_file_relocates_file(temp_storage, tmp_path):
    job_id = uuid.uuid4()
    filename = "move_me.csv"
    content = b"content"
    
    source_path = await temp_storage.save_file(content, job_id, filename, subfolder="staging")
    assert "staging" in source_path
    
    new_path = await temp_storage.move_file(source_path, target_subfolder="archive")
    
    assert "archive" in new_path
    assert os.path.exists(new_path)
    assert not os.path.exists(source_path)
