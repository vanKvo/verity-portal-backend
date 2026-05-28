"""Identity Router module for Verity Portal.

Acts strictly as a thin presentation/controller layer that delegates core business and token operations
to the IdentityService, mapping custom domain exceptions to structured HTTP responses.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.verity_portal.core.config import get_settings
from src.verity_portal.core.database import get_db
from src.verity_portal.identity.schemas import UserCreate, Token
from src.verity_portal.identity.service import IdentityService
from src.verity_portal.identity.exceptions import (
    InvalidDomainError,
    UserAlreadyExistsError,
    IncorrectCredentialsError,
    InactiveUserError,
    TokenValidationError,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

# Backwards compatibility exports for testing and external modules
create_access_token = IdentityService.create_access_token
create_refresh_token = IdentityService.create_refresh_token

@router.post("/register", response_model=Token, status_code=201)
def register(response: Response, user_data: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user domain account and sets a secure HttpOnly refresh cookie.

    Args:
        response: FastAPI Response instance to attach HttpOnly cookie.
        user_data: User registration details schema.
        db: Database session injection.

    Returns:
        The generated Token schema containing access_token.
    """
    try:
        new_user = IdentityService.register_user(db=db, user_data=user_data)
        
        access_token = IdentityService.create_access_token(data={"sub": new_user.email, "roles": [new_user.role]})
        refresh_token = IdentityService.create_refresh_token(data={"sub": new_user.email})
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {"access_token": access_token, "token_type": "bearer", "roles": [new_user.role]}

    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "USER_ALREADY_EXISTS",
                "message": str(e)
            }
        ) from e
    except InvalidDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_DOMAIN",
                "message": str(e)
            }
        ) from e

@router.post("/login", response_model=Token)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticates a user via credentials and sets a secure HttpOnly refresh cookie.

    Args:
        response: FastAPI Response instance.
        form_data: Standard OAuth2 password request form.
        db: Database session injection.

    Returns:
        The generated Token schema with role context.
    """
    try:
        db_user = IdentityService.authenticate_user(db=db, form_data=form_data)
        
        access_token = IdentityService.create_access_token(data={"sub": db_user.email, "roles": [db_user.role]})
        refresh_token = IdentityService.create_refresh_token(data={"sub": db_user.email})
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {"access_token": access_token, "token_type": "bearer", "roles": [db_user.role]}

    except IncorrectCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INCORRECT_CREDENTIALS",
                "message": str(e)
            }
        ) from e

@router.post("/guest-login", response_model=Token)
def guest_login(response: Response):
    """Provides instant guest session authentication for demo evaluators.

    Args:
        response: FastAPI Response instance.

    Returns:
        The generated Token schema loaded with demo roles.
    """
    roles = ["guest", "ROLE_HR", "ROLE_PM", "ROLE_ECO", "ROLE_FINANCE", "ROLE_IT"]
    
    access_token = IdentityService.create_access_token(data={"sub": "guest@verity.com", "roles": roles})
    refresh_token = IdentityService.create_refresh_token(data={"sub": "guest@verity.com"})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {"access_token": access_token, "token_type": "bearer", "roles": roles}

@router.post("/refresh-token", response_model=Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Validates the refresh token in the HttpOnly cookie and issues a new access token.

    Args:
        request: FastAPI Request instance.
        response: FastAPI Response instance.
        db: Database session injection.

    Returns:
        A new access token and rotated refresh token cookie.
    """
    refresh_token_cookie = request.cookies.get("refresh_token")
    try:
        access_token, new_refresh_token, db_user = IdentityService.refresh_user_token(
            db=db, refresh_token_cookie=refresh_token_cookie
        )
        
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {"access_token": access_token, "token_type": "bearer", "roles": [db_user.role]}

    except TokenValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": e.error_code,
                "message": str(e)
            }
        ) from e
    except InactiveUserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INACTIVE_USER",
                "message": str(e)
            }
        ) from e

@router.post("/logout")
def logout(response: Response):
    """Logs the user out by clearing the refresh token HttpOnly cookie.

    Args:
        response: FastAPI Response instance.

    Returns:
        JSON response showing success.
    """
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    return {"detail": "Logged out successfully"}
