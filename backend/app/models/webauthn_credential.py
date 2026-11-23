"""WebAuthn/passkey credentials."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID


class WebAuthnCredential(Base):
    """A registered passkey (public key only; the private key stays on-device)."""

    __tablename__ = "webauthn_credentials"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    credential_id: Mapped[str] = mapped_column(
        String(512), nullable=False, unique=True, index=True
    )
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transports: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    name: Mapped[str] = mapped_column(String(100), default="Passkey")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[Any] = relationship("User")

    def __repr__(self) -> str:
        return f"<WebAuthnCredential(id={self.id}, user_id={self.user_id})>"
