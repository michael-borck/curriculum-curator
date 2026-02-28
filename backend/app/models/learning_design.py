"""
Learning Design model
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.task_list import TaskList
    from app.models.unit import Unit


class DesignStatus(str, Enum):
    """Learning design approval status"""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class LearningDesign(Base):
    """Learning Design for course planning"""

    __tablename__ = "learning_designs"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=False, index=True
    )

    # Metadata
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(
        String(20), default=DesignStatus.DRAFT.value, nullable=False
    )

    # Content (structured JSON)
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # Complete learning design content
    approval_history: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Approval tracking

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    unit: Mapped[Unit] = relationship("Unit", back_populates="designs")
    task_lists: Mapped[list[TaskList]] = relationship(
        "TaskList", back_populates="design", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LearningDesign(id={self.id}, version='{self.version}', status='{self.status}')>"
