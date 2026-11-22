"""One-time email sign-in tokens (magic links)."""

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


class LoginToken(Base):
    """A hashed, single-use magic-link token."""

    __tablename__ = "login_tokens"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(20), default="magic_link")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User")

    def __init__(
        self,
        user_id: uuid.UUID | str,
        token_hash: str,
        expires_minutes: int = 15,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.user_id = str(user_id) if isinstance(user_id, uuid.UUID) else user_id
        self.token_hash = token_hash
        self.expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)

    @property
    def is_valid(self) -> bool:
        return not self.used and datetime.now(UTC) < self.expires_at
