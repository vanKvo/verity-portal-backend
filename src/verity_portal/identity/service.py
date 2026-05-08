from typing import Optional
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from src.verity_portal.core.config import get_settings
from src.verity_portal.core.exceptions import ValidationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

class InvalidDomainError(ValidationError):
    """Raised when a user email domain is not authorized."""
    def __init__(self, domain: str):
        super().__init__(f"Domain {domain} is not authorized.")

class UserDomain(BaseModel):
    email: EmailStr
    hashed_password: Optional[str] = None
    is_active: bool = True
    role: str = "user"

    @classmethod
    def create(cls, email: str, raw_password: Optional[str] = None, role: str = "user") -> "UserDomain":
        domain = email.split("@")[-1]
        
        if domain not in settings.allowed_domains_list:
            raise InvalidDomainError(domain)
            
        hashed_password = pwd_context.hash(raw_password) if raw_password else None
        return cls(email=email, hashed_password=hashed_password, role=role)

    def verify_password(self, raw_password: str) -> bool:
        if not self.hashed_password:
            return False
        return pwd_context.verify(raw_password, self.hashed_password)
