"""
Assessment model for course evaluation management
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
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
    """Assessment types (learning vs grading focus)"""

    FORMATIVE = "formative"  # Learning-focused, low/no grade weight
    SUMMATIVE = "summative"  # Grade-focused, significant weight


class AssessmentCategory(str, Enum):
    """Categories of assessments"""

    QUIZ = "quiz"
    EXAM = "exam"
    PROJECT = "project"
    DISCUSSION = "discussion"
    PAPER = "paper"
    PRESENTATION = "presentation"
    LAB = "lab"
    PORTFOLIO = "portfolio"
    PARTICIPATION = "participation"
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


class Assessment(Base):
    """Assessment and evaluation items"""

    __tablename__ = "assessments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Parent relationship
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)

    # Basic information
    title = Column(String(500), nullable=False)
    type = Column(String(20), nullable=False, index=True)  # AssessmentType enum
    category = Column(String(50), nullable=False, index=True)  # AssessmentCategory enum
    weight = Column(Float, nullable=False, default=0.0)  # Percentage of final grade (0-100)

    # Descriptions
    description = Column(Text, nullable=True)  # Brief description
    specification = Column(Text, nullable=True)  # Detailed requirements

    # Timeline
    release_week = Column(Integer, nullable=True)
    release_date = Column(Date, nullable=True)
    due_week = Column(Integer, nullable=True)
    due_date = Column(Date, nullable=True)
    duration = Column(String(100), nullable=True)  # e.g., "2 hours", "3 weeks"

    # Assessment details
    rubric = Column(JSON, nullable=True)  # Rubric structure
    questions = Column(Integer, nullable=True)  # Number of questions (for quizzes/exams)
    word_count = Column(Integer, nullable=True)  # Required word count (for papers)
    group_work = Column(Boolean, nullable=False, default=False)
    submission_type = Column(String(20), nullable=True)  # SubmissionType enum

    # Status
    status = Column(
        String(20), nullable=False, default=AssessmentStatus.DRAFT.value
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    unit = relationship("Unit", back_populates="assessments")

    # Assessment-specific learning outcomes
    assessment_outcomes = relationship(
        "AssessmentLearningOutcome",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )

    # Many-to-many with ULOs through mapping table
    learning_outcomes = relationship(
        "UnitLearningOutcome",
        secondary="assessment_ulo_mappings",
        backref="assessments"
    )

    # Many-to-many with materials through mapping table
    linked_materials = relationship(
        "WeeklyMaterial",
        secondary="assessment_material_links",
        back_populates="assessments"
    )

    def __repr__(self):
        return f"<Assessment(id={self.id}, title='{self.title}', type='{self.type}', weight={self.weight}%)>"

    @property
    def is_formative(self) -> bool:
        """Check if assessment is formative"""
        return self.type == AssessmentType.FORMATIVE.value

    @property
    def is_summative(self) -> bool:
        """Check if assessment is summative"""
        return self.type == AssessmentType.SUMMATIVE.value

    @property
    def is_graded(self) -> bool:
        """Check if assessment has grade weight"""
        return self.weight > 0

    @property
    def is_group_assessment(self) -> bool:
        """Check if this is a group assessment"""
        return self.group_work

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

    def get_rubric_criteria(self) -> list:
        """Get rubric criteria if exists"""
        if self.rubric and isinstance(self.rubric, dict):
            return self.rubric.get("criteria", [])
        return []

    def get_total_rubric_points(self) -> float:
        """Calculate total points from rubric"""
        if self.rubric and isinstance(self.rubric, dict):
            criteria = self.rubric.get("criteria", [])
            return sum(c.get("points", 0) for c in criteria)
        return 0.0
