"""Module providing core identity and authentication services for the Verity Portal.

Handles registration, credential verification, and secure cookie-backed token refresh operations.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from src.verity_portal.core.config import get_settings
from src.verity_portal.identity.schemas import UserDomain, UserCreate
from src.verity_portal.identity.models import UserModel
from src.verity_portal.identity.exceptions import (
    InvalidDomainError,
    UserAlreadyExistsError,
    IncorrectCredentialsError,
    InactiveUserError,
    TokenValidationError,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

class IdentityService:
    """Service handling identity, authentication, and token business logic."""

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Generates a short-lived access JWT token.

        Args:
            data: Dictionary of claims to encode in the token.
            expires_delta: Optional timedelta for custom expiration overrides.

        Returns:
            The signed and encoded access token string.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Generates a secure sliding refresh JWT token.

        Args:
            data: Dictionary of claims to encode.

        Returns:
            The signed and encoded refresh token string with type='refresh'.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @classmethod
    def register_user(cls, db: Session, user_data: UserCreate) -> UserModel:
        """Registers a new user after domain verification.

        Args:
            db: Database session.
            user_data: User registration data containing email and password.

        Returns:
            The created UserModel instance.

        Raises:
            UserAlreadyExistsError: If email is already taken.
            InvalidDomainError: If the corporate email domain is invalid.
        """
        db_user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
        if db_user:
            raise UserAlreadyExistsError(user_data.email)

        domain_user = cls.create_user_domain(email=user_data.email, raw_password=user_data.password)
        
        new_db_user = UserModel(
            email=domain_user.email,
            hashed_password=domain_user.hashed_password,
            role=domain_user.role,
            is_active=domain_user.is_active
        )
        db.add(new_db_user)
        db.commit()
        db.refresh(new_db_user)
        return new_db_user

    @classmethod
    def authenticate_user(cls, db: Session, form_data: OAuth2PasswordRequestForm) -> UserModel:
        """Authenticates a user via credentials.

        Args:
            db: Database session.
            form_data: OAuth2 request form containing username and password.

        Returns:
            The authenticated UserModel instance.

        Raises:
            IncorrectCredentialsError: If the username/password combination is incorrect.
        """
        db_user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
        if not db_user:
            raise IncorrectCredentialsError()

        if not cls.verify_password(form_data.password, db_user.hashed_password):
            raise IncorrectCredentialsError()

        return db_user

    @classmethod
    def refresh_user_token(cls, db: Session, refresh_token_cookie: Optional[str]) -> Tuple[str, str, UserModel]:
        """Validates a refresh token cookie and returns a new access token, rotated refresh token, and user.

        Args:
            db: Database session.
            refresh_token_cookie: The refresh token value from browser cookies.

        Returns:
            A tuple of (new_access_token, new_refresh_token, db_user).

        Raises:
            TokenValidationError: If refresh token is missing, invalid, or expired.
            InactiveUserError: If user is inactive.
        """
        if not refresh_token_cookie:
            raise TokenValidationError(
                message="Session expired or invalid. Please log in again.",
                error_code="REFRESH_TOKEN_MISSING"
            )

        try:
            payload = jwt.decode(refresh_token_cookie, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_type = payload.get("type")
            email = payload.get("sub")

            if token_type != "refresh" or not email:
                raise TokenValidationError(
                    message="Invalid session token. Please log in again.",
                    error_code="INVALID_REFRESH_TOKEN"
                )

            db_user = db.query(UserModel).filter(UserModel.email == email).first()
            if not db_user or not db_user.is_active:
                raise InactiveUserError(email or "")

            access_token = cls.create_access_token(data={"sub": db_user.email, "roles": [db_user.role]})
            new_refresh_token = cls.create_refresh_token(data={"sub": db_user.email})
            
            return access_token, new_refresh_token, db_user

        except jwt.ExpiredSignatureError as e:
            raise TokenValidationError(
                message="Your session has expired. Please log in again.",
                error_code="REFRESH_TOKEN_EXPIRED"
            ) from e
        except jwt.InvalidTokenError as e:
            raise TokenValidationError(
                message="Invalid session token. Please log in again.",
                error_code="INVALID_REFRESH_TOKEN"
            ) from e

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
