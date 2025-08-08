"""
System settings model for admin-configurable application settings
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import validates

from app.core.database import Base
from app.models.user import GUID


class SystemSettings(Base):
    """System settings model for admin-configurable application settings"""

    __tablename__ = "system_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<SystemSettings(id={self.id}, key='{self.key}', value='{self.value[:50]}...')>"

    @validates("key")
    def validate_key(self, key, value):
        """Validate setting key format"""
        if not value:
            raise ValueError("Setting key cannot be empty")

        # Convert to lowercase and replace spaces with underscores
        value = value.lower().replace(" ", "_").replace("-", "_")

        # Only allow alphanumeric characters and underscores
        if not all(c.isalnum() or c == "_" for c in value):
            raise ValueError(
                "Setting key can only contain alphanumeric characters and underscores"
            )

        return value

    @classmethod
    def get_default_settings(cls):
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
        ]
