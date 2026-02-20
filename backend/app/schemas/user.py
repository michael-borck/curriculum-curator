"""
User-related Pydantic schemas for authentication and profile management
"""

from datetime import datetime
from typing import Any

from pydantic import EmailStr, field_validator

from app.schemas.base import CamelModel


class UserBase(CamelModel):
    """Base user fields"""

    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(CamelModel):
    """Schema for updating user profile"""

    name: str | None = None
    email: EmailStr | None = None
    institution: str | None = None
    department: str | None = None


class ProfileUpdateRequest(CamelModel):
    """Schema for updating user profile via PATCH /auth/profile"""

    name: str | None = None
    institution: str | None = None
    department: str | None = None
    teaching_philosophy: str | None = None
    language_preference: str | None = None
    teaching_preferences: dict[str, Any] | None = None


class UserResponse(UserBase):
    """Schema for user response (public fields)"""

    id: str
    role: str
    is_verified: bool
    is_active: bool
    institution: str | None = None
    department: str | None = None
    teaching_philosophy: str | None = None
    teaching_preferences: dict[str, Any] | None = None
    created_at: datetime | str


class UserInDB(UserResponse):
    """Schema for user with password hash (internal use)"""

    password_hash: str


class UserLogin(CamelModel):
    """Schema for login request"""

    email: EmailStr
    password: str


class PasswordChange(CamelModel):
    """Schema for password change"""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class PasswordReset(CamelModel):
    """Schema for password reset request"""

    email: EmailStr


class PasswordResetConfirm(CamelModel):
    """Schema for confirming password reset"""

    token: str
    new_password: str
