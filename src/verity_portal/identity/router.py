from datetime import datetime, timedelta
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.verity_portal.core.config import get_settings
from src.verity_portal.core.database import get_db
from src.verity_portal.identity.models import UserModel
from src.verity_portal.identity.schemas import UserCreate, Token, UserDomain
from src.verity_portal.identity.service import IdentityService
from src.verity_portal.identity.exceptions import InvalidDomainError

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=Token, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    try:
        domain_user = IdentityService.create_user_domain(email=user_data.email, raw_password=user_data.password)
    except InvalidDomainError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    new_db_user = UserModel(
        email=domain_user.email,
        hashed_password=domain_user.hashed_password,
        role=domain_user.role,
        is_active=domain_user.is_active
    )
    db.add(new_db_user)
    db.commit()
    
    access_token = create_access_token(data={"sub": domain_user.email, "roles": [domain_user.role]})
    return {"access_token": access_token, "token_type": "bearer", "roles": [domain_user.role]}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect email")
        
    if not IdentityService.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
        
    access_token = create_access_token(data={"sub": db_user.email, "roles": [db_user.role]})
    return {"access_token": access_token, "token_type": "bearer", "roles": [db_user.role]}

@router.post("/guest-login", response_model=Token)
def guest_login():
    # Injecting ROLE_EXPORT_CONTROL for demo purposes as part of Phase 6 rollout
    roles = ["guest", "ROLE_EXPORT_CONTROL"]
    access_token = create_access_token(data={"sub": "guest@verity.com", "roles": roles})
    return {"access_token": access_token, "token_type": "bearer", "roles": roles}
