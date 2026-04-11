"""
Email verification model for user registration flow
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.user import User


class EmailVerification(Base):
    """Email verification model for user registration"""

    __tablename__ = "email_verifications"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(
        String(6), nullable=False, index=True
    )  # 6-digit verification code
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="email_verifications")

    def __init__(
        self,
        user_id: uuid.UUID | str,
        code: str,
        expires_minutes: int = 60,
        **kwargs: object,
    ) -> None:
        """Initialize with expiration time"""
        super().__init__(**kwargs)
        self.user_id = str(user_id) if isinstance(user_id, uuid.UUID) else user_id
        self.code = code
        self.expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)

    def __repr__(self) -> str:
        return f"<EmailVerification(id={self.id}, user_id={self.user_id}, used={self.used})>"

    @property
    def is_expired(self) -> bool:
        """Check if verification code has expired"""
        expires = self.expires_at
        if isinstance(expires, datetime):
            return datetime.now(UTC) > expires
        return False

    @property
    def is_valid(self) -> bool:
        """Check if verification code is valid (not used and not expired)"""
        return not self.used and not self.is_expired

    def mark_as_used(self) -> None:
        """Mark verification code as used"""
        self.used = True
