from datetime import datetime, timedelta
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.verity_portal.core.config import get_settings
from src.verity_portal.core.database import get_db
from src.verity_portal.identity.models import UserModel
from src.verity_portal.identity.schemas import UserCreate, Token
from src.verity_portal.identity.service import UserDomain, InvalidDomainError

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
        domain_user = UserDomain.create(email=user_data.email, raw_password=user_data.password)
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
    
    access_token = create_access_token(data={"sub": domain_user.email, "role": domain_user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": domain_user.role}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    domain_user = UserDomain(email=db_user.email, hashed_password=db_user.hashed_password, role=db_user.role)
    if not domain_user.verify_password(form_data.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": domain_user.email, "role": domain_user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": domain_user.role}

@router.post("/guest-login", response_model=Token)
def guest_login():
    access_token = create_access_token(data={"sub": "guest@verity.com", "role": "guest"})
    return {"access_token": access_token, "token_type": "bearer", "role": "guest"}
