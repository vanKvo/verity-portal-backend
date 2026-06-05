"""Email notification service module.

Provides an abstract interface and concrete implementations for sending 
alerts and system notifications to application administrators.
"""

from abc import ABC, abstractmethod
import boto3
import logging
from src.verity_portal.core.config import get_settings

logger = logging.getLogger(__name__)

class BaseEmailService(ABC):
    """Abstract interface defining the contract for email notification services."""

    @abstractmethod
    def send_alert(self, subject: str, body: str) -> None:
        """Sends an urgent system/business alert email."""

class SnsEmailService(BaseEmailService):
    """Implementation of BaseEmailService using AWS Simple Notification Service (SNS)."""

    def __init__(self, sns_client, topic_arn: str | None):
        """Dependencies are injected here when the class is instantiated."""
        self._sns_client = sns_client
        self._topic_arn = topic_arn

    def send_alert(self, subject: str, body: str) -> None:
        """Publishes an alert notification to an AWS SNS Topic."""
        if not self._topic_arn:
            logger.warning("AWS_SNS_TOPIC_ARN is not configured. Skipping AWS SNS email alert.")
            return

        try:
            self._sns_client.publish(
                TopicArn=self._topic_arn,
                Subject=subject,
                Message=body
            )
            logger.info(f"Successfully sent email alert via SNS to topic: {self._topic_arn}")
        except Exception as e:
            logger.error(f"Failed to publish email alert via AWS SNS: {e}")

def get_email_service() -> BaseEmailService:
    """Returns the configured email service instance conforming to BaseEmailService."""
    settings = get_settings()
    topic_arn = getattr(settings, "AWS_SNS_TOPIC_ARN", None)
    
    # Instantiate the client once here
    sns_client = boto3.client(
        "sns",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION,
    )
    
    # Inject the client and the configuration directly into the implementation
    return SnsEmailService(sns_client=sns_client, topic_arn=topic_arn)
