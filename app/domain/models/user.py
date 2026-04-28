from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

class InvalidDomainError(Exception):
    pass

class User(BaseModel):
    email: EmailStr
    hashed_password: Optional[str] = None
    is_active: bool = True
    role: str = "user"

    @classmethod
    def create(cls, email: str, raw_password: Optional[str] = None, role: str = "user") -> "User":
        domain = email.split("@")[-1]
        
        # Only validate domain for non-guest roles, or maybe all depending on requirements.
        # But wait, guest login skips password. Let's validate domain for everyone except if guest is implemented differently.
        if domain not in settings.allowed_domains_list:
            raise InvalidDomainError(f"Domain {domain} is not authorized.")
            
        hashed_password = pwd_context.hash(raw_password) if raw_password else None
        return cls(email=email, hashed_password=hashed_password, role=role)

    def verify_password(self, raw_password: str) -> bool:
        if not self.hashed_password:
            return False
        return pwd_context.verify(raw_password, self.hashed_password)
