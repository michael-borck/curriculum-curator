"""
Assessment plan model for course evaluation tracking
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.unit import Unit
    from app.models.unit_outline import UnitOutline
    from app.models.user import User


class AssessmentType(str, Enum):
    """Assessment type enumeration"""

    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    PROJECT = "project"
    PRESENTATION = "presentation"
    PARTICIPATION = "participation"
    LAB_REPORT = "lab_report"
    PORTFOLIO = "portfolio"
    PEER_REVIEW = "peer_review"
    REFLECTION = "reflection"


class AssessmentMode(str, Enum):
    """Assessment mode enumeration"""

    FORMATIVE = "formative"  # For learning
    SUMMATIVE = "summative"  # Of learning


class AssessmentPlan(Base):
    """Assessment plan model for course evaluation structure"""

    __tablename__ = "assessment_plans"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Links
    unit_outline_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("unit_outlines.id"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=True, index=True
    )

    # Assessment details
    assessment_name: Mapped[str] = mapped_column(String(500))
    assessment_type: Mapped[str] = mapped_column(String(30))
    assessment_mode: Mapped[str] = mapped_column(
        String(20), default=AssessmentMode.SUMMATIVE.value
    )
    description: Mapped[str] = mapped_column(Text)

    # Weighting and grading
    weight_percentage: Mapped[float] = mapped_column(Float)  # Percentage of final grade
    pass_mark: Mapped[float | None] = mapped_column(
        Float, default=50.0, nullable=True
    )  # Pass percentage

    # Timing
    release_week: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Week assessment is released
    due_week: Mapped[int] = mapped_column(Integer, index=True)  # Week assessment is due
    duration_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # For exams/quizzes

    # Submission details
    submission_format: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # PDF, code, video, etc.
    submission_method: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # LMS, email, in-person
    group_work: Mapped[bool] = mapped_column(default=False)
    group_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Learning outcomes alignment
    aligned_outcome_ids: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # List of outcome IDs

    # Rubric and criteria
    has_rubric: Mapped[bool] = mapped_column(default=False)
    rubric_criteria: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Structured rubric data
    marking_criteria: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Text description

    # Requirements and instructions
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    resources_provided: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # Templates, datasets, etc.

    # Feedback
    feedback_method: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Written, verbal, peer
    feedback_timeline_days: Mapped[int | None] = mapped_column(
        Integer, default=14, nullable=True
    )

    # Special conditions
    late_penalty: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # e.g., "5% per day"
    extension_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    special_consideration: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_finalized: Mapped[bool] = mapped_column(default=False)
    materials_ready: Mapped[bool] = mapped_column(default=False)

    # Metadata
    created_by_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id"))
    estimated_hours: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Expected student effort

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    unit_outline: Mapped["UnitOutline"] = relationship(
        back_populates="assessment_plans"
    )
    unit: Mapped["Unit | None"] = relationship()
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        name_preview = str(self.assessment_name)[:50] if self.assessment_name else ""
        return f"<AssessmentPlan(id={self.id}, name='{name_preview}...', type='{self.assessment_type}', weight={self.weight_percentage}%)>"

    @property
    def is_group_assessment(self) -> bool:
        """Check if this is a group assessment"""
        return bool(self.group_work)

    @property
    def is_major_assessment(self) -> bool:
        """Check if this is a major assessment (>= 20% weight)"""
        return float(self.weight_percentage) >= 20

    @property
    def submission_window_weeks(self) -> int:
        """Calculate submission window in weeks"""
        if self.release_week:
            return int(self.due_week) - int(self.release_week)
        return 0

    @property
    def aligned_outcomes_count(self) -> int:
        """Count aligned learning outcomes"""
        if not self.aligned_outcome_ids:
            return 0
        return len(self.aligned_outcome_ids)

    def validate_weight(self, total_weight: float) -> bool:
        """Validate assessment weight doesn't exceed 100%"""
        return (total_weight + float(self.weight_percentage)) <= 100

    def get_timeline_description(self) -> str:
        """Get human-readable timeline description"""
        if self.release_week and int(self.release_week) != int(self.due_week):
            return f"Released week {self.release_week}, due week {self.due_week}"
        return f"Due week {self.due_week}"

    def check_readiness(self) -> dict[str, Any]:
        """Check if assessment is ready for release"""
        issues: list[str] = []

        if not self.description:
            issues.append("Missing description")
        if not self.instructions:
            issues.append("Missing instructions")
        if not self.marking_criteria and not self.rubric_criteria:
            issues.append("Missing marking criteria or rubric")
        if self.has_rubric and not self.rubric_criteria:
            issues.append("Rubric flagged but not provided")
        if not self.aligned_outcome_ids:
            issues.append("No aligned learning outcomes")

        return {
            "is_ready": len(issues) == 0,
            "issues": issues,
            "materials_ready": bool(self.materials_ready),
        }
