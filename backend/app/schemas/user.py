"""
User-related Pydantic schemas
"""

from pydantic import EmailStr

from app.schemas.base import CamelModel


class UserBase(CamelModel):
    email: EmailStr
    name: str
    role: str


class UserCreate(UserBase):
    password: str


class UserUpdate(CamelModel):
    name: str | None = None
    email: EmailStr | None = None
    role: str | None = None


class UserResponse(UserBase):
    id: str
    is_verified: bool
    is_active: bool
    created_at: str
