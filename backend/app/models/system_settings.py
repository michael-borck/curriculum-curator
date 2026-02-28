"""
System settings model for admin-configurable application settings
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base
from app.models.common import GUID


class SystemSettings(Base):
    """System settings model for admin-configurable application settings"""

    __tablename__ = "system_settings"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    value: Mapped[str | None] = mapped_column(Text, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        value_str = str(self.value)[:50] if self.value else ""
        return (
            f"<SystemSettings(id={self.id}, key='{self.key}', value='{value_str}...')>"
        )

    @validates("key")
    def validate_key(self, key: str, value: Any) -> str:
        """Validate setting key format"""
        if not value:
            raise ValueError("Setting key cannot be empty")

        # Convert to lowercase and replace spaces with underscores
        value = str(value).lower().replace(" ", "_").replace("-", "_")

        # Only allow alphanumeric characters and underscores
        if not all(c.isalnum() or c == "_" for c in value):
            raise ValueError(
                "Setting key can only contain alphanumeric characters and underscores"
            )

        return value

    @classmethod
    def get_default_settings(cls) -> list[dict[str, str]]:
        """Get default system settings to be seeded"""
        return [
            {
                "key": "registration_enabled",
                "value": "true",
                "description": "Enable user registration",
            },
            {
                "key": "email_verification_required",
                "value": "true",
                "description": "Require email verification for new accounts",
            },
            {
                "key": "admin_notifications_enabled",
                "value": "true",
                "description": "Send notifications to admins for new registrations",
            },
            {
                "key": "max_verification_attempts",
                "value": "5",
                "description": "Maximum verification attempts per code",
            },
            {
                "key": "verification_code_expiry_minutes",
                "value": "15",
                "description": "Verification code expiry time in minutes",
            },
            {
                "key": "password_reset_expiry_minutes",
                "value": "30",
                "description": "Password reset token expiry time in minutes",
            },
            {
                "key": "brevo_from_email",
                "value": "noreply@curriculum-curator.com",
                "description": "Default from email address for Brevo",
            },
            {
                "key": "brevo_from_name",
                "value": "Curriculum Curator",
                "description": "Default from name for Brevo emails",
            },
            # LLM System Settings
            {
                "key": "default_llm_provider",
                "value": "openai",
                "description": "System default LLM provider (openai, anthropic, gemini)",
            },
            {
                "key": "default_llm_model",
                "value": "gpt-4",
                "description": "Default LLM model to use",
            },
            {
                "key": "system_openai_api_key",
                "value": "",
                "description": "System-wide OpenAI API key (encrypted)",
            },
            {
                "key": "system_anthropic_api_key",
                "value": "",
                "description": "System-wide Anthropic API key (encrypted)",
            },
            {
                "key": "system_gemini_api_key",
                "value": "",
                "description": "System-wide Google Gemini API key (encrypted)",
            },
            {
                "key": "allow_user_api_keys",
                "value": "true",
                "description": "Allow users to provide their own API keys (BYOK)",
            },
            {
                "key": "require_user_api_key",
                "value": "false",
                "description": "Require users to provide their own API key if system key not set",
            },
        ]
