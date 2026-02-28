"""
Email whitelist model for controlling user registration access
"""

import re
import uuid
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, Session, mapped_column, validates

from app.core.database import Base
from app.models.common import GUID


class EmailWhitelist(Base):
    """Email whitelist model for controlling registration access"""

    __tablename__ = "email_whitelist"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    pattern: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<EmailWhitelist(id={self.id}, pattern='{self.pattern}', active={self.is_active})>"

    @validates("pattern")
    def validate_pattern(self, key: str, value: str) -> str:
        """Validate email pattern format"""
        if not value:
            raise ValueError("Email pattern cannot be empty")

        # Convert to lowercase for consistency
        value = value.lower().strip()

        # Check if it's a valid email pattern (either full email or domain)
        if "@" in value and not value.startswith("@"):
            # Full email address (contains @ but doesn't start with it)
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, value):
                raise ValueError("Invalid email address format")
        else:
            # Domain pattern (should start with @ or be just domain)
            if not value.startswith("@"):
                value = "@" + value

            # Allow localhost for development, otherwise require standard domain format
            if value == "@localhost":
                pass  # Allow localhost
            elif value.startswith("@"):
                domain_pattern = r"^@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(domain_pattern, value):
                    raise ValueError(f"Invalid domain pattern format: {value}")
            else:
                raise ValueError(f"Domain pattern should start with @: {value}")

        return value

    def matches_email(self, email: str) -> bool:
        """Check if email matches this whitelist pattern"""
        if not self.is_active:
            return False

        email = email.lower().strip()
        pattern = str(self.pattern)

        # If pattern is a full email, do exact match
        if "@" in pattern and not pattern.startswith("@"):
            return email == pattern

        # If pattern is a domain (@example.com), check if email ends with it
        if pattern.startswith("@"):
            return email.endswith(pattern)

        return False

    @classmethod
    def is_email_whitelisted(cls, session: Session, email: str) -> bool:
        """Check if an email is whitelisted (class method for easy usage)"""
        active_patterns = (
            session.query(cls).filter(cls.is_active == True).all()  # noqa: E712
        )

        # If no active patterns, allow all emails (open registration)
        if not active_patterns:
            return True

        # Check if email matches any active pattern
        return any(pattern.matches_email(email) for pattern in active_patterns)

    @classmethod
    def get_default_whitelist(cls) -> list[dict[str, str | bool]]:
        """Get default whitelist entries to be seeded"""
        return [
            {
                "pattern": "@example.com",
                "description": "Example domain - replace with your organization's domain",
                "is_active": False,
            },
            {
                "pattern": "@localhost",
                "description": "Localhost domain for development",
                "is_active": True,
            },
        ]
