from typing import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserDomain(BaseModel):
    email: EmailStr
    hashed_password: Optional[str] = None
    is_active: bool = True
    role: str = "user"

class Token(BaseModel):
    access_token: str
    token_type: str
    roles: list[str]
