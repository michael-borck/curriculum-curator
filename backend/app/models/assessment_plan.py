"""
Assessment plan model for course evaluation tracking
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Links
    course_outline_id = Column(
        GUID(), ForeignKey("course_outlines.id"), nullable=False, index=True
    )
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=True, index=True)

    # Assessment details
    assessment_name = Column(String(500), nullable=False)
    assessment_type = Column(String(30), nullable=False)
    assessment_mode = Column(
        String(20), default=AssessmentMode.SUMMATIVE.value, nullable=False
    )
    description = Column(Text, nullable=False)

    # Weighting and grading
    weight_percentage = Column(Float, nullable=False)  # Percentage of final grade
    pass_mark = Column(Float, default=50.0, nullable=True)  # Pass percentage

    # Timing
    release_week = Column(Integer, nullable=True)  # Week assessment is released
    due_week = Column(Integer, nullable=False, index=True)  # Week assessment is due
    duration_minutes = Column(Integer, nullable=True)  # For exams/quizzes

    # Submission details
    submission_format = Column(String(100), nullable=True)  # PDF, code, video, etc.
    submission_method = Column(String(100), nullable=True)  # LMS, email, in-person
    group_work = Column(Boolean, default=False, nullable=False)
    group_size = Column(Integer, nullable=True)

    # Learning outcomes alignment
    aligned_outcome_ids = Column(JSON, nullable=True)  # List of outcome IDs

    # Rubric and criteria
    has_rubric = Column(Boolean, default=False, nullable=False)
    rubric_criteria = Column(JSON, nullable=True)  # Structured rubric data
    marking_criteria = Column(Text, nullable=True)  # Text description

    # Requirements and instructions
    requirements = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    resources_provided = Column(JSON, nullable=True)  # Templates, datasets, etc.

    # Feedback
    feedback_method = Column(String(100), nullable=True)  # Written, verbal, peer
    feedback_timeline_days = Column(Integer, default=14, nullable=True)

    # Special conditions
    late_penalty = Column(String(200), nullable=True)  # e.g., "5% per day"
    extension_policy = Column(Text, nullable=True)
    special_consideration = Column(Text, nullable=True)

    # Status
    is_finalized = Column(Boolean, default=False, nullable=False)
    materials_ready = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    estimated_hours = Column(Float, nullable=True)  # Expected student effort

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    course_outline = relationship("CourseOutline", back_populates="assessment_plans")
    unit = relationship("Unit")
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<AssessmentPlan(id={self.id}, name='{self.assessment_name[:50]}...', type='{self.assessment_type}', weight={self.weight_percentage}%)>"

    @property
    def is_group_assessment(self) -> bool:
        """Check if this is a group assessment"""
        return self.group_work

    @property
    def is_major_assessment(self) -> bool:
        """Check if this is a major assessment (>= 20% weight)"""
        return self.weight_percentage >= 20

    @property
    def submission_window_weeks(self) -> int:
        """Calculate submission window in weeks"""
        if self.release_week:
            return self.due_week - self.release_week
        return 0

    @property
    def aligned_outcomes_count(self) -> int:
        """Count aligned learning outcomes"""
        if not self.aligned_outcome_ids:
            return 0
        return len(self.aligned_outcome_ids)

    def validate_weight(self, total_weight: float) -> bool:
        """Validate assessment weight doesn't exceed 100%"""
        return (total_weight + self.weight_percentage) <= 100

    def get_timeline_description(self) -> str:
        """Get human-readable timeline description"""
        if self.release_week and self.release_week != self.due_week:
            return f"Released week {self.release_week}, due week {self.due_week}"
        return f"Due week {self.due_week}"

    def check_readiness(self) -> dict:
        """Check if assessment is ready for release"""
        issues = []

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
            "materials_ready": self.materials_ready,
        }
