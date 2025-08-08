"""
Password reset model for secure password recovery
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class PasswordReset(Base):
    """Password reset model for secure password recovery"""

    __tablename__ = "password_resets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(6), nullable=False, index=True)  # 6-digit reset code
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="password_resets")

    def __init__(self, user_id: uuid.UUID, token: str, expires_minutes: int = 30):
        """Initialize with expiration time (30 minutes default for security)"""
        self.user_id = user_id
        self.token = token
        self.expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

    def __repr__(self):
        return (
            f"<PasswordReset(id={self.id}, user_id={self.user_id}, used={self.used})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if reset token has expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if reset token is valid (not used and not expired)"""
        return not self.used and not self.is_expired

    def mark_as_used(self):
        """Mark reset token as used"""
        self.used = True
