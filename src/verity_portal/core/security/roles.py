import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.verity_portal.core.config import get_settings

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """Decodes and validates the JWT token.
    
    Args:
        token: The raw JWT token from the Authorization header.
        
    Returns:
        The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_role: str):
    """FastAPI dependency that enforces a specific role.
    
    Args:
        required_role: The role string to check for in the token payload.
        
    Returns:
        A function that performs the role check.
    """
    def role_checker(payload: dict = Depends(get_current_token_payload)):
        roles = payload.get("roles", [])
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return payload
    return role_checker


def require_any_role(required_roles: list[str]):
    """FastAPI dependency that enforces a user has at least one of the listed roles.
    
    Args:
        required_roles: A list of allowed role strings.
        
    Returns:
        A function that performs the role check.
    """
    def role_checker(payload: dict = Depends(get_current_token_payload)):
        roles = payload.get("roles", [])
        if not any(r in roles for r in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return payload
    return role_checker

