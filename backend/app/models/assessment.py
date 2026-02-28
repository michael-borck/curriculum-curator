"""
Assessment model for course evaluation management
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.learning_outcome import (
        AssessmentLearningOutcome,
        UnitLearningOutcome,
    )
    from app.models.unit import Unit
    from app.models.weekly_material import WeeklyMaterial


class AssessmentType(str, Enum):
    """Assessment types (learning vs grading focus)"""

    FORMATIVE = "formative"  # Learning-focused, low/no grade weight
    SUMMATIVE = "summative"  # Grade-focused, significant weight


class AssessmentCategory(str, Enum):
    """Categories of assessments"""

    QUIZ = "quiz"
    EXAM = "exam"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    DISCUSSION = "discussion"
    PAPER = "paper"
    PRESENTATION = "presentation"
    LAB = "lab"
    LAB_REPORT = "lab_report"
    PORTFOLIO = "portfolio"
    PARTICIPATION = "participation"
    VIVA = "viva"
    # Cross-sector
    REFLECTION = "reflection"
    JOURNAL = "journal"
    CASE_STUDY = "case_study"
    PEER_REVIEW = "peer_review"
    # VET
    PRACTICAL_ASSESSMENT = "practical_assessment"
    SKILLS_DEMONSTRATION = "skills_demonstration"
    # K-12
    TEST = "test"
    HOMEWORK = "homework"
    OTHER = "other"


class SubmissionType(str, Enum):
    """How assessments are submitted"""

    ONLINE = "online"
    IN_PERSON = "in_person"
    BOTH = "both"


class AssessmentStatus(str, Enum):
    """Assessment preparation status"""

    DRAFT = "draft"
    COMPLETE = "complete"
    NEEDS_REVIEW = "needs_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Assessment(Base):
    """Assessment and evaluation items"""

    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Parent relationship
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=False, index=True
    )

    # Basic information
    title: Mapped[str] = mapped_column(String(500))
    type: Mapped[str] = mapped_column(String(20), index=True)  # AssessmentType enum
    category: Mapped[str] = mapped_column(
        String(50), index=True
    )  # AssessmentCategory enum
    weight: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Percentage of final grade (0-100)

    # Descriptions
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    specification: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timeline
    release_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    duration: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "2 hours", "3 weeks"

    # Assessment details
    rubric: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Rubric structure
    questions: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Number of questions (for quizzes/exams)
    word_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Required word count (for papers)
    group_work: Mapped[bool] = mapped_column(default=False)
    submission_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # SubmissionType enum

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=AssessmentStatus.DRAFT.value
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    unit: Mapped[Unit] = relationship(back_populates="assessments")

    # Assessment-specific learning outcomes
    assessment_outcomes: Mapped[list[AssessmentLearningOutcome]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    # Many-to-many with ULOs through mapping table
    learning_outcomes: Mapped[list[UnitLearningOutcome]] = relationship(
        secondary="assessment_ulo_mappings",
        backref="assessments",
    )

    # Many-to-many with materials through mapping table
    linked_materials: Mapped[list[WeeklyMaterial]] = relationship(
        secondary="assessment_material_links",
        back_populates="assessments",
    )

    def __repr__(self) -> str:
        return f"<Assessment(id={self.id}, title='{self.title}', type='{self.type}', weight={self.weight}%)>"

    @property
    def is_formative(self) -> bool:
        """Check if assessment is formative"""
        return str(self.type) == AssessmentType.FORMATIVE.value

    @property
    def is_summative(self) -> bool:
        """Check if assessment is summative"""
        return str(self.type) == AssessmentType.SUMMATIVE.value

    @property
    def is_graded(self) -> bool:
        """Check if assessment has grade weight"""
        return float(self.weight) > 0

    @property
    def is_group_assessment(self) -> bool:
        """Check if this is a group assessment"""
        return bool(self.group_work)

    @property
    def timeline_description(self) -> str:
        """Get human-readable timeline description"""
        parts = []
        if self.release_week:
            parts.append(f"Released Week {self.release_week}")
        if self.due_week:
            parts.append(f"Due Week {self.due_week}")
        if self.duration:
            parts.append(f"Duration: {self.duration}")
        return " | ".join(parts) if parts else "No timeline set"

    def get_rubric_criteria(self) -> list[dict[str, Any]]:
        """Get rubric criteria if exists"""
        if self.rubric and isinstance(self.rubric, dict):
            return self.rubric.get("criteria", [])
        return []

    def get_total_rubric_points(self) -> float:
        """Get total points from rubric"""
        if self.rubric and isinstance(self.rubric, dict):
            return float(self.rubric.get("total_points", 0))
        return 0.0

    def get_rubric_type(self) -> str | None:
        """Get rubric type (analytic, single_point, holistic, checklist)"""
        if self.rubric and isinstance(self.rubric, dict):
            return str(self.rubric.get("type", "analytic"))
        return None
