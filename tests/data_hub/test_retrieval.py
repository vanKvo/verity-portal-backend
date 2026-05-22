import pytest
import io
import pandas as pd
from fastapi import UploadFile
from moto import mock_aws
import boto3
from src.verity_portal.data_hub.core.retrieval import RetrievalStrategyFactory
from src.verity_portal.data_hub.personnel.models import PersonnelModel, CitizenshipStatus
from src.verity_portal.data_hub.core.ingestion import parse_file_to_df, DataHubOrchestrationService
from src.verity_portal.data_hub.exceptions import DataHubRetrievalError
from src.verity_portal.identity.router import create_access_token
from src.verity_portal.core.email import BaseEmailService, SnsEmailService, get_email_service
from src.verity_portal.core.config import get_settings
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_manual_upload_strategy():
    """Test that ManualUploadStrategy wraps FastAPI's UploadFile properly."""
    content = b"employee_id,citizenship_status\nE001,US Citizen"
    upload_file = UploadFile(
        file=io.BytesIO(content),
        filename="test_upload.csv"
    )
    strategy = RetrievalStrategyFactory.get_manual_strategy(upload_file)
    
    assert strategy.filename == "test_upload.csv"
    stream = await strategy.retrieve_stream()
    assert stream.read() == content

@pytest.mark.asyncio
async def test_s3_event_strategy():
    """Test that S3EventStrategy downloads objects from mock S3 buckets correctly."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket = "verity-test-bucket"
        key = "hr/personnel_roster.csv"
        content = b"employee_id,first_name,citizenship_status\nE001,John,US Citizen"
        
        s3.create_bucket(Bucket=bucket)
        s3.put_object(Bucket=bucket, Key=key, Body=content)
        
        strategy = RetrievalStrategyFactory.get_s3_strategy(bucket, key)
        assert strategy.filename == "personnel_roster.csv"
        
        stream = await strategy.retrieve_stream()
        assert stream.read() == content

@pytest.mark.asyncio
async def test_parse_file_to_df_csv():
    """Test parse_file_to_df successfully processes CSV streams."""
    content = b"employee_id,first_name\nE001,John"
    stream = io.BytesIO(content)
    df = parse_file_to_df("test.csv", stream)
    
    assert list(df.columns) == ["employee_id", "first_name"]
    assert df.iloc[0]["first_name"] == "John"

@pytest.mark.asyncio
async def test_perform_s3_ingestion_background_task(db_session):
    """Test background task successfully processes S3 file sync in database."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket = "verity-webhook-bucket"
        key = "hr_personnel_nightly.csv"
        content = b"employee_id,first_name,citizenship_status\nE999,Alice,Green Card"
        
        s3.create_bucket(Bucket=bucket)
        s3.put_object(Bucket=bucket, Key=key, Body=content)
        
        # Run the background processor function directly
        orchestration_service = DataHubOrchestrationService(db_session)
        await orchestration_service.perform_s3_ingestion(bucket, key)
        
        # Query database and verify correct ingestion and normalization occurred
        personnel = db_session.query(PersonnelModel).filter_by(employee_id="E999").first()
        assert personnel is not None
        assert personnel.first_name == "Alice"
        assert personnel.citizenship_status == CitizenshipStatus.PERMANENT_RESIDENT

@pytest.mark.asyncio
async def test_s3_event_strategy_raises_custom_error():
    """Test that S3EventStrategy raises DataHubRetrievalError when retrieval fails.""" 
    with mock_aws():
        strategy = RetrievalStrategyFactory.get_s3_strategy("nonexistent-bucket", "missing.csv")
        with pytest.raises(DataHubRetrievalError) as exc_info:
            await strategy.retrieve_stream()
        
        assert "Failed to retrieve data from S3" in str(exc_info.value)
        assert exc_info.value.source_type == "S3"
        assert "nonexistent-bucket" in exc_info.value.source_identifier

def test_sync_status_endpoint(client, db_session):
    """Test that the /data-hub/sync-status endpoint returns ISO format timestamps or None."""
    # 1. Initially both tables are empty in the test database session, so sync status should be None
    response = client.get("/data-hub/sync-status")
    assert response.status_code == 200
    data = response.json()
    assert data["personnel_last_sync"] is None
    assert data["projects_last_sync"] is None

    # 2. Add sample personnel
    p = PersonnelModel(employee_id="E1234", first_name="TestSync", citizenship_status=CitizenshipStatus.US_CITIZEN)
    db_session.add(p)
    db_session.commit()

    # 3. Request again and assert personnel_last_sync is now set
    response = client.get("/data-hub/sync-status")
    assert response.status_code == 200
    data = response.json()
    assert data["personnel_last_sync"] is not None
    assert "T" in data["personnel_last_sync"]
    assert data["projects_last_sync"] is None


def test_upload_hr_data_invalid_mapping_json(client, db_session):
    """Verify that uploading HR data with invalid mapping JSON returns structured 400."""
    token = create_access_token(data={"sub": "hr@verity.com", "roles": ["ROLE_HR"]})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/data-hub/personnel/upload",
        headers=headers,
        files={"file": ("test.csv", b"employee_id,citizenship_status\nE001,US Citizen")},
        data={"mapping": "{invalid-json}"}
    )
    
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_code"] == "INVALID_MAPPING_FORMAT"
    assert "mapping JSON payload is invalid" in detail["message"]


class MockEmailService(BaseEmailService):
    """Mock email service conforming to BaseEmailService for capturing alerts in tests."""

    def __init__(self) -> None:
        self.sent_alerts = []

    def send_alert(self, subject: str, body: str) -> None:
        self.sent_alerts.append((subject, body))


@pytest.mark.asyncio
async def test_s3_ingestion_failure_triggers_sns_alert(db_session):
    """Test S3 ingestion failure publishes an email alert via AWS SNS."""
    mock_email_service = MockEmailService()
    orchestration_service = DataHubOrchestrationService(db_session, email_service=mock_email_service)
    
    with pytest.raises(DataHubRetrievalError):
        await orchestration_service.perform_s3_ingestion("nonexistent-bucket", "missing.csv")
        
    assert len(mock_email_service.sent_alerts) == 1
    subject, body = mock_email_service.sent_alerts[0]
    
    assert "ALERT: Data Hub S3 Ingestion Failure" in subject
    assert "s3://nonexistent-bucket/missing.csv" in body
    assert "Error Details:" in body


@pytest.mark.asyncio
async def test_sns_email_service_publish():
    """Test SnsEmailService publishes correctly using boto3 sns client."""
    with mock_aws():
        # 1. Setup mocked SNS client and create a mock topic
        sns_client = boto3.client("sns", region_name="us-east-1")
        topic = sns_client.create_topic(Name="alerts-topic")
        topic_arn = topic["TopicArn"]
        
        # 2. Spy on the publish method to capture calls
        sns_client.publish = MagicMock(side_effect=sns_client.publish)
        
        # 3. Instantiate SnsEmailService with injected mock dependencies
        email_service = SnsEmailService(sns_client=sns_client, topic_arn=topic_arn)
        
        # 4. Trigger send_alert
        email_service.send_alert(subject="Test Subject", body="Test Body")
        
        # 5. Assert that the underlying client published with exactly the right parameters
        sns_client.publish.assert_called_once_with(
            TopicArn=topic_arn,
            Subject="Test Subject",
            Message="Test Body"
        )

