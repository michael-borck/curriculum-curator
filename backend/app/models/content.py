"""
Content model for unit materials (lectures, worksheets, etc.)
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.content_version import ContentVersion
    from app.models.generation_history import GenerationHistory
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.quiz_question import QuizQuestion
    from app.models.research_source import ContentCitation
    from app.models.unit import Unit
    from app.models.validation_result import ValidationResult


class ContentCategory(str, Enum):
    """Content category for flipped classroom model"""

    PRE_CLASS = "pre_class"  # Before class preparation
    IN_CLASS = "in_class"  # During class activities
    POST_CLASS = "post_class"  # After class reflection/practice
    GENERAL = "general"  # Not categorized


class ContentType(str, Enum):
    """Content type enumeration"""

    SYLLABUS = "syllabus"
    SCHEDULE = "schedule"
    LECTURE = "lecture"
    MODULE = "module"
    WORKSHEET = "worksheet"
    FAQ = "faq"
    QUIZ = "quiz"
    SHORT_ANSWER = "short_answer"
    MATCHING = "matching"
    CASE_STUDY = "case_study"
    INTERACTIVE = "interactive"
    RESOURCE = (
        "resource"  # Renamed from READING - includes articles, videos, websites, etc.
    )
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    ASSESSMENT = "assessment"
    VIDEO = "video"  # Explicit video content
    PODCAST = "podcast"  # Audio content
    TUTORIAL = "tutorial"  # Step-by-step guides


class ContentStatus(str, Enum):
    """Content status enumeration"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Content(Base):
    """Content model for unit materials"""

    __tablename__ = "contents"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, index=True
    )

    # Basic content information
    title: Mapped[str] = mapped_column(String(500), index=True)
    type: Mapped[str] = mapped_column(String(20), index=True)  # ContentType enum
    status: Mapped[str] = mapped_column(
        String(20), default=ContentStatus.DRAFT.value, index=True
    )

    # Content data
    # NOTE: Body is stored in Git for version control. These fields are for caching/legacy:
    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Git storage references (primary storage for body)
    git_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    current_commit: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Hierarchical organization
    unit_id: Mapped[str] = mapped_column(GUID(), ForeignKey("units.id"), index=True)
    parent_content_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("contents.id"), nullable=True, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Weekly schedule mapping
    week_number: Mapped[int | None] = mapped_column(nullable=True, index=True)
    content_category: Mapped[str] = mapped_column(
        String(20), default=ContentCategory.GENERAL.value
    )

    # Educational metadata
    learning_objectives: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    difficulty_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prerequisites: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Generation and validation metadata
    generation_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    validation_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    # Additional metadata and settings
    content_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="contents")
    parent_content: Mapped["Content | None"] = relationship(
        remote_side=[id], back_populates="child_contents"
    )
    child_contents: Mapped[list["Content"]] = relationship(
        back_populates="parent_content", cascade="all, delete-orphan"
    )
    versions: Mapped[list["ContentVersion"]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )
    generation_history: Mapped[list["GenerationHistory"]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )

    # Many-to-many relationship with learning outcomes
    learning_outcomes: Mapped[list["UnitLearningOutcome"]] = relationship(
        secondary="content_outcomes",
        back_populates="contents",
        overlaps="contents",
    )

    # Citations from research sources
    citations: Mapped[list["ContentCitation"]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        title_preview = str(self.title)[:50] if self.title else ""
        return f"<Content(id={self.id}, type='{self.type}', title='{title_preview}...', status='{self.status}')>"

    @property
    def is_draft(self) -> bool:
        """Check if content is in draft status"""
        return str(self.status) == ContentStatus.DRAFT.value

    @property
    def is_active(self) -> bool:
        """Check if content is active/published"""
        return str(self.status) == ContentStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        """Check if content is archived"""
        return str(self.status) == ContentStatus.ARCHIVED.value

    @property
    def is_quiz(self) -> bool:
        """Check if content is a quiz type"""
        return str(self.type) in [
            ContentType.QUIZ.value,
            ContentType.SHORT_ANSWER.value,
            ContentType.MATCHING.value,
        ]

    @property
    def has_children(self) -> bool:
        """Check if content has child contents"""
        return len(self.child_contents) > 0

    @property
    def estimated_duration_formatted(self) -> str:
        """Get formatted duration string"""
        if not self.estimated_duration_minutes:
            return "Not specified"

        hours = self.estimated_duration_minutes // 60
        minutes = self.estimated_duration_minutes % 60

        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        if hours > 0:
            return f"{hours}h"
        return f"{minutes}m"
