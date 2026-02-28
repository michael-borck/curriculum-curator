"""
Weekly topic model for course schedule management
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
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
    from app.models.content import Content
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.unit import Unit
    from app.models.unit_outline import UnitOutline
    from app.models.user import User


class WeekType(str, Enum):
    """Week type enumeration"""

    REGULAR = "regular"
    REVISION = "revision"
    ASSESSMENT = "assessment"
    BREAK = "break"
    HOLIDAY = "holiday"


class WeeklyTopic(Base):
    """Weekly topic model for course scheduling"""

    __tablename__ = "weekly_topics"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Links
    unit_outline_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("unit_outlines.id"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("units.id"), index=True, default=None
    )

    # Week details
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    week_type: Mapped[str] = mapped_column(
        String(20), default=WeekType.REGULAR.value, nullable=False
    )
    topic_title: Mapped[str] = mapped_column(String(500), nullable=False)
    topic_description: Mapped[str | None] = mapped_column(Text, default=None)

    # Learning focus
    key_concepts: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # List of main concepts
    learning_objectives: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # Week-specific objectives

    # Pre-class components (Flipped classroom)
    pre_class_modules: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # List of module descriptions
    pre_class_duration_minutes: Mapped[int | None] = mapped_column(Integer, default=60)
    pre_class_resources: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # Links, readings, videos

    # In-class components
    in_class_activities: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # List of activities
    in_class_duration_minutes: Mapped[int | None] = mapped_column(Integer, default=120)
    in_class_format: Mapped[str | None] = mapped_column(
        String(50), default=None
    )  # lecture, workshop, lab

    # Post-class components
    post_class_tasks: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # Homework, reflection
    post_class_duration_minutes: Mapped[int | None] = mapped_column(Integer, default=60)

    # Assessment information
    has_assessment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assessment_details: Mapped[str | None] = mapped_column(Text, default=None)

    # Resources and materials
    required_readings: Mapped[list[Any] | None] = mapped_column(JSON, default=None)
    supplementary_resources: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )
    equipment_required: Mapped[str | None] = mapped_column(Text, default=None)

    # Status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    created_by_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # Internal notes for instructors

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    unit_outline: Mapped[UnitOutline] = relationship(
        "UnitOutline", back_populates="weekly_topics"
    )
    unit: Mapped[Unit | None] = relationship("Unit")
    created_by: Mapped[User] = relationship("User", foreign_keys=[created_by_id])

    learning_outcomes: Mapped[list[UnitLearningOutcome]] = relationship(
        "UnitLearningOutcome",
        back_populates="weekly_topic",
        cascade="all, delete-orphan",
    )

    contents: Mapped[list[Content]] = relationship(
        "Content",
        foreign_keys="Content.week_number",
        primaryjoin=(
            "and_(WeeklyTopic.unit_id==Content.unit_id, "
            "WeeklyTopic.week_number==Content.week_number)"
        ),
        viewonly=True,
    )

    def __repr__(self) -> str:
        title = str(self.topic_title)[:50] if self.topic_title else ""
        return f"<WeeklyTopic(id={self.id}, week={self.week_number}, title='{title}...', type='{self.week_type}')>"

    @property
    def total_student_hours(self) -> float:
        """Calculate total student hours for the week"""
        pre = (self.pre_class_duration_minutes or 0) / 60
        during = (self.in_class_duration_minutes or 0) / 60
        post = (self.post_class_duration_minutes or 0) / 60
        return float(pre + during + post)

    @property
    def is_teaching_week(self) -> bool:
        """Check if this is a regular teaching week"""
        return str(self.week_type) == WeekType.REGULAR.value

    @property
    def has_pre_class_content(self) -> bool:
        """Check if pre-class content exists"""
        return bool(self.pre_class_modules or self.pre_class_resources)

    @property
    def has_in_class_content(self) -> bool:
        """Check if in-class content exists"""
        return bool(self.in_class_activities)

    @property
    def has_post_class_content(self) -> bool:
        """Check if post-class content exists"""
        return bool(self.post_class_tasks)

    def get_content_by_category(self, category: str) -> list[Content]:
        """Get content items for a specific category (pre/in/post)"""
        return [c for c in self.contents if c.content_category == category]

    def update_completion_status(self) -> None:
        """Update completion status based on content"""
        self.is_complete = bool(
            self.has_pre_class_content
            and self.has_in_class_content
            and self.learning_outcomes
            and len(self.learning_outcomes) > 0
        )

        self.content_ready = bool(
            self.is_complete
            and len(self.get_content_by_category("pre_class")) > 0
            and len(self.get_content_by_category("in_class")) > 0
        )
