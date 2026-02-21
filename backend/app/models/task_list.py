"""
Task list model for learning design implementation tracking
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.learning_design import LearningDesign
    from app.models.unit import Unit


class TaskStatus(str, Enum):
    """Task list status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class TaskList(Base):
    """Task list generated from a learning design"""

    __tablename__ = "task_lists"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, index=True
    )
    design_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("learning_designs.id"), index=True, default=None
    )
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=False, index=True
    )

    # Task list content
    tasks: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # Structured task data
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.PENDING.value, nullable=False
    )

    # Progress tracking
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Detailed progress information

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # Relationships
    unit: Mapped[Unit] = relationship("Unit", back_populates="task_lists")
    design: Mapped[LearningDesign | None] = relationship(
        "LearningDesign", back_populates="task_lists"
    )

    def __repr__(self) -> str:
        return f"<TaskList(id={self.id}, status='{self.status}', progress={self.completed_tasks}/{self.total_tasks})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate task completion percentage"""
        total = int(self.total_tasks)
        if total == 0:
            return 0.0
        return (int(self.completed_tasks) / total) * 100
