"""
User-related Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None


class UserResponse(UserBase):
    id: str
    is_verified: bool
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True