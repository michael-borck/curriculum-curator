"""
Unit outline model for structured curriculum content
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.assessment_plan import AssessmentPlan
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.unit import Unit
    from app.models.user import User
    from app.models.weekly_topic import WeeklyTopic


class UnitStructureStatus(str, Enum):
    """Course structure status enumeration"""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"


class UnitOutline(Base):
    """Unit outline model for structured curriculum development"""

    __tablename__ = "unit_outlines"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Link to unit
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=False, index=True
    )

    # Course overview
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    rationale: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # Why this course exists

    # Academic details
    duration_weeks: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    credit_points: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    student_workload_hours: Mapped[int | None] = mapped_column(
        Integer, default=None
    )  # Total expected hours

    # Teaching approach
    delivery_mode: Mapped[str | None] = mapped_column(
        String(50), default=None
    )  # face-to-face, online, blended
    teaching_pattern: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # e.g., "2hr lecture + 2hr lab weekly"

    # Prerequisites and requirements
    prerequisites: Mapped[str | None] = mapped_column(Text, default=None)
    corequisites: Mapped[str | None] = mapped_column(Text, default=None)
    assumed_knowledge: Mapped[str | None] = mapped_column(Text, default=None)

    # Graduate attributes
    graduate_attributes: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # List of attributes addressed

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default=UnitStructureStatus.PLANNING.value, nullable=False
    )
    completion_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    # Metadata
    created_by_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    updated_by_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("users.id"), default=None
    )
    approved_by_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("users.id"), default=None
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # Relationships
    unit: Mapped[Unit] = relationship("Unit", back_populates="unit_outline")
    created_by: Mapped[User] = relationship("User", foreign_keys=[created_by_id])
    updated_by: Mapped[User | None] = relationship("User", foreign_keys=[updated_by_id])
    approved_by: Mapped[User | None] = relationship(
        "User", foreign_keys=[approved_by_id]
    )

    learning_outcomes: Mapped[list[UnitLearningOutcome]] = relationship(
        "UnitLearningOutcome",
        back_populates="unit_outline",
        cascade="all, delete-orphan",
        order_by="UnitLearningOutcome.sequence_order",
    )

    weekly_topics: Mapped[list[WeeklyTopic]] = relationship(
        "WeeklyTopic",
        back_populates="unit_outline",
        cascade="all, delete-orphan",
        order_by="WeeklyTopic.week_number",
    )

    assessment_plans: Mapped[list[AssessmentPlan]] = relationship(
        "AssessmentPlan",
        back_populates="unit_outline",
        cascade="all, delete-orphan",
        order_by="AssessmentPlan.due_week",
    )

    def __repr__(self) -> str:
        title = str(self.title)[:50] if self.title else ""
        return (
            f"<UnitOutline(id={self.id}, title='{title}...', status='{self.status}')>"
        )

    @property
    def is_complete(self) -> bool:
        """Check if unit outline is complete"""
        return bool(
            self.learning_outcomes
            and self.weekly_topics
            and self.assessment_plans
            and float(self.completion_percentage) >= 100
        )

    @property
    def total_assessment_weight(self) -> float:
        """Calculate total assessment weight percentage"""
        if not self.assessment_plans:
            return 0.0
        return sum(float(plan.weight_percentage) for plan in self.assessment_plans)

    def update_completion_percentage(self) -> None:
        """Update completion percentage based on components"""
        components = 0
        total = 5  # Total components to check

        if self.description and self.rationale:
            components += 1
        if self.learning_outcomes and len(self.learning_outcomes) >= 3:
            components += 1
        duration = int(self.duration_weeks)
        if self.weekly_topics and len(self.weekly_topics) >= duration:
            components += 1
        if self.assessment_plans and self.total_assessment_weight == 100:
            components += 1
        if self.graduate_attributes:
            components += 1

        self.completion_percentage = (components / total) * 100
