"""
Plugin configuration model — persists plugin enabled/disabled state and priority.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.common import GUID


class PluginConfiguration(Base):
    """Stores per-plugin configuration that survives server restarts."""

    __tablename__ = "plugin_configurations"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PluginConfiguration(name='{self.name}', enabled={self.enabled}, priority={self.priority})>"
