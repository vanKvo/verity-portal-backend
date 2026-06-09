import io
import os
import asyncio
from abc import ABC, abstractmethod
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile
from src.verity_portal.data_hub.exceptions import DataHubRetrievalError
from src.verity_portal.core.config import get_settings

class BaseRetrievalStrategy(ABC):
    """Abstract base class for all file retrieval strategies."""

    @abstractmethod
    async def retrieve_stream(self) -> io.BytesIO:
        """Retrieves raw file contents as a seekable BytesIO stream."""

    @property
    @abstractmethod
    def filename(self) -> str:
        """Returns the name of the file."""

class ManualUploadStrategy(BaseRetrievalStrategy):
    """Retrieves file stream directly from browser file upload."""

    def __init__(self, file: UploadFile):
        self.file = file

    async def retrieve_stream(self) -> io.BytesIO:
        contents = await self.file.read()
        return io.BytesIO(contents)

    @property
    def filename(self) -> str:
        return self.file.filename

class S3EventStrategy(BaseRetrievalStrategy):
    """Retrieves file stream asynchronously from an S3 bucket key using secure access URL."""

    def __init__(self, bucket_name: str, object_key: str):
        self._bucket_name = bucket_name
        self._object_key = object_key
        
    def _get_s3_client(self):
        settings = get_settings()
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            config=boto3.session.Config(signature_version='s3v4')
        )

    async def retrieve_stream(self) -> io.BytesIO:
        loop = asyncio.get_event_loop()
        s3_client = self._get_s3_client()
        
        try:
            # Native boto3 optimizes this stream transfer
            file_buffer = io.BytesIO()
            
            # Run the synchronous download in an architectural thread pool
            # to avoid synchronous boto to freeze FastAPI event loop
            await loop.run_in_executor(
                None, 
                # Direct, secure, multi-part optimized download from a private bucket
                lambda: s3_client.download_fileobj(
                    Bucket=self._bucket_name, 
                    Key=self._object_key, 
                    Fileobj=file_buffer
                )
            )
            file_buffer.seek(0)
            return file_buffer
        except (BotoCoreError, ClientError) as e:
            raise DataHubRetrievalError(
                source_type="S3",
                source_identifier=f"s3://{self._bucket_name}/{self._object_key}",
                detail=str(e)
            ) from e

    @property
    def filename(self) -> str:
        return os.path.basename(self._object_key)

class RetrievalStrategyFactory:
    """Factory to instantiate data retrieval strategies."""

    @staticmethod
    def get_manual_strategy(file: UploadFile) -> BaseRetrievalStrategy:
        return ManualUploadStrategy(file)

    @staticmethod
    def get_s3_strategy(bucket_name: str, object_key: str) -> BaseRetrievalStrategy:
        return S3EventStrategy(bucket_name, object_key)
