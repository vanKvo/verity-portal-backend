from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Verity Portal"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/verity_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-for-development"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Corporate Domain
    ALLOWED_DOMAINS: str = Field(default="corporate.com,verity.com")

    @property
    def allowed_domains_list(self) -> list[str]:
        return [domain.strip() for domain in self.ALLOWED_DOMAINS.split(",")]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

@lru_cache()
def get_settings():
    return Settings()
