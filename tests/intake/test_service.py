import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from src.verity_portal.intake.service import IntakeService
from src.verity_portal.intake.storage import StoragePort

@pytest.fixture
def mock_storage():
    return AsyncMock(spec=StoragePort)

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def intake_service(mock_storage, mock_db):
    return IntakeService(storage_port=mock_storage, db=mock_db)

@pytest.mark.asyncio
async def test_ingest_file_saves_to_storage_and_db(intake_service, mock_storage, mock_db):
    job_id = uuid.uuid4()
    filename = "test.csv"
    content = b"content"
    
    mock_storage.save_file.return_value = "/staging/safe_test.csv"
    
    def mock_add(obj):
        obj.file_id = uuid.uuid4()
    mock_db.add.side_effect = mock_add
    
    file_id = await intake_service.ingest_file(content, job_id, filename)
    
    assert isinstance(file_id, uuid.UUID)
    mock_storage.save_file.assert_called_once_with(content, job_id, filename, subfolder="staging")
    assert mock_db.add.called
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_ingest_file_rejects_large_files(intake_service):
    job_id = uuid.uuid4()
    filename = "large.csv"
    large_content = b"0" * (51 * 1024 * 1024)
    
    with pytest.raises(ValueError, match="File size exceeds 50MB limit"):
        await intake_service.ingest_file(large_content, job_id, filename)

@pytest.mark.asyncio
async def test_archive_file_coordinates_move_and_update(intake_service, mock_storage, mock_db):
    job_id = uuid.uuid4()
    mock_file = MagicMock()
    mock_file.storage_path = "/staging/test.csv"
    mock_file.status = "STAGED"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_file
    
    mock_storage.move_file.return_value = "/archive/test.csv"
    
    success = await intake_service.archive_file(job_id)
    
    assert success is True
    mock_storage.move_file.assert_called_once_with("/staging/test.csv", target_subfolder="archive")
    assert mock_file.status == "ARCHIVED"
    assert mock_file.storage_path == "/archive/test.csv"
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_confirm_and_ingest_standardizes_dates(intake_service, mock_storage, mock_db):
    job_id = uuid.uuid4()
    mock_file = MagicMock()
    mock_file.storage_path = "/staging/test.csv"
    mock_file.original_name = "test.csv"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_file
    
    csv_content = b"emp_id,term_date\n1,12/31/2023"
    mock_storage.get_file.return_value = csv_content
    
    mappings = {"emp_id": "employee_id", "term_date": "hr_termination_date"}
    
    count = await intake_service.confirm_and_ingest(job_id, mappings)
    
    assert count == 1
    added_record = mock_db.add.call_args_list[0][0][0]
    assert added_record.data["hr_termination_date"] == "2023-12-31"
