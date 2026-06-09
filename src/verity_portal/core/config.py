import os
import boto3
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "Verity Portal"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost:5432/verity_db", description="Postgres connection string")
    
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", description="Secret key for JWT signing")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Corporate Domain
    ALLOWED_DOMAINS: str = Field(default="corporate.com,verity.com")

    # CORS Origins whitelisting
    ALLOWED_ORIGINS: str = Field(...)

    # AWS Configuration
    S3_HR_BUCKET_NAME: str = Field(..., description="S3 bucket for HR personnel data")
    AWS_ACCESS_KEY_ID: str | None = Field(default=None, description="AWS Access Key ID")
    AWS_SECRET_ACCESS_KEY: str | None = Field(default=None, description="AWS Secret Access Key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS Region")
    S3_ENDPOINT_URL: str | None = Field(default=None, description="S3 Endpoint URL (e.g. MinIO/LocalStack)")
    AWS_SNS_TOPIC_ARN: str | None = Field(default=None, description="AWS SNS Topic ARN for administrator email alerts")

    def __init__(self, **values):
        super().__init__(**values)
        if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
            try:
                # Use standard boto3 discovery. It resolves IAM role credentials automatically.
                ssm = boto3.client("ssm", region_name=self.AWS_REGION)
                env_name = os.environ.get("ENVIRONMENT", "dev")
                
                # Fetch database connection string
                db_param = ssm.get_parameter(
                    Name=f"/verity-portal/{env_name}/database_url",
                    WithDecryption=True
                )
                self.DATABASE_URL = db_param["Parameter"]["Value"]

                # Fetch JWT secret key
                sec_param = ssm.get_parameter(
                    Name=f"/verity-portal/{env_name}/secret_key",
                    WithDecryption=True
                )
                self.SECRET_KEY = sec_param["Parameter"]["Value"]
            except Exception as e:
                # Fall back or print error for diagnostics
                print(f"AWS SSM Parameter Store loading failed: {e}")

    @property
    def allowed_domains_list(self) -> list[str]:
        """Parses the ALLOWED_DOMAINS string into a list."""
        return [domain.strip() for domain in self.ALLOWED_DOMAINS.split(",")]

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parses the ALLOWED_ORIGINS string into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

@lru_cache()
def get_settings():
    """Returns a cached Settings instance."""
    return Settings()
