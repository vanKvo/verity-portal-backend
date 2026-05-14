from typing import Optional
from passlib.context import CryptContext
from src.verity_portal.core.config import get_settings
from src.verity_portal.identity.schemas import UserDomain
from src.verity_portal.identity.exceptions import InvalidDomainError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

class IdentityService:
    """Service handling identity and authentication logic."""

    @staticmethod
    def create_user_domain(email: str, raw_password: Optional[str] = None, role: str = "user") -> UserDomain:
        """Validates email domain and creates a UserDomain object with hashed password.
        
        Args:
            email: User email address.
            raw_password: Plain text password.
            role: Assigned user role.
            
        Returns:
            A UserDomain schema object.
            
        Raises:
            InvalidDomainError: If the email domain is not in the allowed list.
        """
        domain = email.split("@")[-1]
        
        if domain not in settings.allowed_domains_list:
            raise InvalidDomainError(domain)
            
        hashed_password = pwd_context.hash(raw_password) if raw_password else None
        return UserDomain(email=email, hashed_password=hashed_password, role=role)

    @staticmethod
    def verify_password(raw_password: str, hashed_password: Optional[str]) -> bool:
        """Verifies a plain text password against a hashed password.
        
        Args:
            raw_password: The plain text password to check.
            hashed_password: The stored hashed password.
            
        Returns:
            True if valid, False otherwise.
        """
        if not hashed_password:
            return False
        return pwd_context.verify(raw_password, hashed_password)
