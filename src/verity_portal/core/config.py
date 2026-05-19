from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "Verity Portal"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = Field(..., description="Postgres connection string")
    
    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT signing")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Corporate Domain
    ALLOWED_DOMAINS: str = Field(default="corporate.com,verity.com")

    # CORS Origins whitelisting
    ALLOWED_ORIGINS: str = Field(default="http://localhost:4200")

    # AWS Configuration
    S3_HR_BUCKET_NAME: str = Field(..., description="S3 bucket for HR personnel data")

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
