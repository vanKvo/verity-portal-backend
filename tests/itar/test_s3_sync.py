import pytest
import boto3
from moto import mock_aws
from src.verity_portal.shared.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.itar.s3_worker import S3WorkerService

@pytest.fixture
def s3_setup():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket_name = "verity-hr-data"
        s3.create_bucket(Bucket=bucket_name)
        yield s3, bucket_name

def test_s3_worker_normalizes_citizenship(s3_setup, db_session):
    """Test that the worker correctly pulls from S3 and normalizes strings."""
    s3, bucket_name = s3_setup
    
    # 1. Setup DB with existing personnel
    p1 = PersonnelModel(employee_id="E001", citizenship_status=CitizenshipStatus.UNKNOWN)
    p2 = PersonnelModel(employee_id="E002", citizenship_status=CitizenshipStatus.UNKNOWN)
    db_session.add(p1)
    db_session.add(p2)
    db_session.commit()

    # 2. Upload mock CSV to S3
    csv_content = "employee_id,citizenship\nE001,USA\nE002,Permanent Resident"
    s3.put_object(Bucket=bucket_name, Key="hr_sync.csv", Body=csv_content)

    # 3. Action
    worker = S3WorkerService(db_session)
    # Mocking settings or passing bucket name
    processed = worker.sync_hr_data(bucket=bucket_name, key="hr_sync.csv")

    # 4. Assertions
    assert processed == 2
    
    # Verify normalization
    db_session.refresh(p1)
    db_session.refresh(p2)
    assert p1.citizenship_status == CitizenshipStatus.US_CITIZEN
    assert p2.citizenship_status == CitizenshipStatus.PERMANENT_RESIDENT

def test_s3_worker_unknown_status(s3_setup, db_session):
    """Test that unknown strings remain UNKNOWN."""
    s3, bucket_name = s3_setup
    p1 = PersonnelModel(employee_id="E999", citizenship_status=CitizenshipStatus.UNKNOWN)
    db_session.add(p1)
    db_session.commit()

    csv_content = "employee_id,citizenship\nE999,Martian"
    s3.put_object(Bucket=bucket_name, Key="hr_sync.csv", Body=csv_content)

    worker = S3WorkerService(db_session)
    worker.sync_hr_data(bucket=bucket_name, key="hr_sync.csv")

    db_session.refresh(p1)
    assert p1.citizenship_status == CitizenshipStatus.UNKNOWN
