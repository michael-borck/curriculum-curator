"""
Authentication API schemas
"""

import re

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import CamelModel


class UserRegistrationRequest(CamelModel):
    """Request schema for user registration"""

    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )
    name: str = Field(..., min_length=1, max_length=255, description="Full name")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        # Check for at least one lowercase letter
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        # Check for at least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate name format"""
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Name cannot be empty")

        # Allow letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-\']+$", v):
            raise ValueError(
                "Name can only contain letters, spaces, hyphens, and apostrophes"
            )

        return v


class UserRegistrationResponse(CamelModel):
    """Response schema for user registration"""

    message: str
    verification_required: bool = True
    user_email: str


class EmailVerificationRequest(CamelModel):
    """Request schema for email verification"""

    email: EmailStr
    code: str = Field(
        ..., min_length=6, max_length=6, description="6-digit verification code"
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v):
        """Validate verification code format"""
        if not v.isdigit():
            raise ValueError("Verification code must be 6 digits")
        if len(v) != 6:
            raise ValueError("Verification code must be exactly 6 digits")
        return v


class EmailVerificationResponse(CamelModel):
    """Response schema for email verification"""

    # OAuth2 standard fields - keep as snake_case
    access_token: str = Field(alias="access_token")
    token_type: str = Field(default="bearer", alias="token_type")
    user: "UserResponse"


class ForgotPasswordRequest(CamelModel):
    """Request schema for forgot password"""

    email: EmailStr


class ForgotPasswordResponse(CamelModel):
    """Response schema for forgot password"""

    message: str


class ResetPasswordRequest(CamelModel):
    """Request schema for password reset"""

    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit reset code")
    new_password: str = Field(
        ..., min_length=8, description="New password must be at least 8 characters"
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v):
        """Validate reset code format"""
        if not v.isdigit():
            raise ValueError("Reset code must be 6 digits")
        if len(v) != 6:
            raise ValueError("Reset code must be exactly 6 digits")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength (same as registration)"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        return v


class ResetPasswordResponse(CamelModel):
    """Response schema for password reset"""

    message: str


class UserResponse(CamelModel):
    """Response schema for user information"""

    id: str
    email: str
    name: str
    role: str
    is_verified: bool
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class LoginResponse(CamelModel):
    """Response schema for login"""

    # OAuth2 standard fields - keep as snake_case
    access_token: str = Field(alias="access_token")
    token_type: str = Field(default="bearer", alias="token_type")
    user: UserResponse


class ResendVerificationRequest(CamelModel):
    """Request schema for resending verification email"""

    email: EmailStr


class ResendVerificationResponse(CamelModel):
    """Response schema for resending verification"""

    message: str


# Update forward references
EmailVerificationResponse.model_rebuild()
