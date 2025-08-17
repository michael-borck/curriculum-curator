"""
Email verification model for user registration flow
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class EmailVerification(Base):
    """Email verification model for user registration"""

    __tablename__ = "email_verifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    code = Column(String(6), nullable=False, index=True)  # 6-digit verification code
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="email_verifications")

    def __init__(self, user_id: uuid.UUID, code: str, expires_minutes: int = 60):
        """Initialize with expiration time"""
        self.user_id = user_id
        self.code = code
        self.expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

    def __repr__(self):
        return f"<EmailVerification(id={self.id}, user_id={self.user_id}, used={self.used})>"

    @property
    def is_expired(self) -> bool:
        """Check if verification code has expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if verification code is valid (not used and not expired)"""
        return not self.used and not self.is_expired

    def mark_as_used(self):
        """Mark verification code as used"""
        self.used = True
