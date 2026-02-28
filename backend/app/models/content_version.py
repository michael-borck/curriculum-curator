"""
Content versioning model for tracking content history
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.user import User


class ContentVersion(Base):
    """Content version model for tracking content history"""

    __tablename__ = "content_versions"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Version information
    content_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("contents.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Content snapshot
    content_markdown: Mapped[str | None] = mapped_column(Text, default=None)
    content_html: Mapped[str | None] = mapped_column(Text, default=None)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Change tracking
    change_description: Mapped[str | None] = mapped_column(Text, default=None)
    created_by_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    content: Mapped[Content] = relationship("Content", back_populates="versions")
    created_by: Mapped[User] = relationship("User")

    def __repr__(self) -> str:
        return f"<ContentVersion(id={self.id}, content_id={self.content_id}, version={self.version_number})>"
