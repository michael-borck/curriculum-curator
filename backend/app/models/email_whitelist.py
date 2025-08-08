"""
Email whitelist model for controlling user registration access
"""

import re
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import validates

from app.core.database import Base
from app.models.user import GUID


class EmailWhitelist(Base):
    """Email whitelist model for controlling registration access"""
    __tablename__ = "email_whitelist"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    pattern = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EmailWhitelist(id={self.id}, pattern='{self.pattern}', active={self.is_active})>"

    @validates('pattern')
    def validate_pattern(self, key, value):
        """Validate email pattern format"""
        if not value:
            raise ValueError("Email pattern cannot be empty")

        # Convert to lowercase for consistency
        value = value.lower().strip()

        # Check if it's a valid email pattern (either full email or domain)
        if '@' in value and not value.startswith('@'):
            # Full email address (contains @ but doesn't start with it)
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValueError("Invalid email address format")
        else:
            # Domain pattern (should start with @ or be just domain)
            if not value.startswith('@'):
                value = '@' + value

            # Allow localhost for development, otherwise require standard domain format
            if value == '@localhost':
                pass  # Allow localhost
            elif value.startswith('@'):
                domain_pattern = r'^@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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

        # If pattern is a full email, do exact match
        if '@' in self.pattern and not self.pattern.startswith('@'):
            return email == self.pattern

        # If pattern is a domain (@example.com), check if email ends with it
        if self.pattern.startswith('@'):
            return email.endswith(self.pattern)

        return False

    @classmethod
    def is_email_whitelisted(cls, session, email: str) -> bool:
        """Check if an email is whitelisted (class method for easy usage)"""
        active_patterns = session.query(cls).filter(cls.is_active).all()

        # If no active patterns, allow all emails (open registration)
        if not active_patterns:
            return True

        # Check if email matches any active pattern
        return any(pattern.matches_email(email) for pattern in active_patterns)

    @classmethod
    def get_default_whitelist(cls):
        """Get default whitelist entries to be seeded"""
        return [
            {
                "pattern": "@example.com",
                "description": "Example domain - replace with your organization's domain",
                "is_active": False
            },
            {
                "pattern": "@localhost",
                "description": "Localhost domain for development",
                "is_active": True
            }
        ]
