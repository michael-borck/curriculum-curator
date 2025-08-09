"""
Admin-related Pydantic schemas
"""

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


# Email Whitelist schemas
class EmailWhitelistBase(BaseModel):
    pattern: str = Field(
        ..., description="Email pattern (e.g., @example.com or user@example.com)"
    )
    description: str | None = Field(None, description="Description of the pattern")
    is_active: bool = Field(True, description="Whether this pattern is active")


class EmailWhitelistCreate(EmailWhitelistBase):
    pass


class EmailWhitelistUpdate(BaseModel):
    pattern: str | None = None
    description: str | None = None
    is_active: bool | None = None


class EmailWhitelistResponse(EmailWhitelistBase):
    id: str
    created_at: str
    updated_at: str


# User management schemas
class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    skip: int
    limit: int


class UserStatsResponse(BaseModel):
    total_users: int
    verified_users: int
    active_users: int
    admin_users: int
    users_by_role: dict[str, int]
    recent_registrations: int


# System settings schemas
class SystemSettingsBase(BaseModel):
    # Password policy
    password_min_length: int = Field(8, ge=6, le=32)
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True

    # Security settings
    max_login_attempts: int = Field(5, ge=3, le=10)
    lockout_duration_minutes: int = Field(15, ge=5, le=60)
    session_timeout_minutes: int = Field(30, ge=15, le=480)

    # Feature flags
    enable_user_registration: bool = True
    enable_email_whitelist: bool = True


class SystemSettingsResponse(SystemSettingsBase):
    pass


class SystemSettingsUpdate(BaseModel):
    # All fields optional for partial updates
    password_min_length: int | None = Field(None, ge=6, le=32)
    password_require_uppercase: bool | None = None
    password_require_lowercase: bool | None = None
    password_require_numbers: bool | None = None
    password_require_special: bool | None = None

    max_login_attempts: int | None = Field(None, ge=3, le=10)
    lockout_duration_minutes: int | None = Field(None, ge=5, le=60)
    session_timeout_minutes: int | None = Field(None, ge=15, le=480)

    enable_user_registration: bool | None = None
    enable_email_whitelist: bool | None = None


# Audit log schemas
class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    user_id: str | None
    user_email: str | None
    ip_address: str
    description: str | None
    severity: str
    timestamp: str
    details: dict | None = None


class DatabaseBackupResponse(BaseModel):
    message: str
    backup_path: str | None
    timestamp: str
