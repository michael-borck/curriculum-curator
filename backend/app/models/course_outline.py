"""
Course outline model for structured curriculum content
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
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


class CourseStructureStatus(str, Enum):
    """Course structure status enumeration"""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"


class CourseOutline(Base):
    """Course outline model for structured curriculum development"""

    __tablename__ = "course_outlines"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Link to unit
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)

    # Course overview
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)  # Why this course exists

    # Academic details
    duration_weeks = Column(Integer, default=12, nullable=False)
    credit_points = Column(Integer, default=6, nullable=False)
    student_workload_hours = Column(Integer, nullable=True)  # Total expected hours

    # Teaching approach
    delivery_mode = Column(String(50), nullable=True)  # face-to-face, online, blended
    teaching_pattern = Column(Text, nullable=True)  # e.g., "2hr lecture + 2hr lab weekly"

    # Prerequisites and requirements
    prerequisites = Column(Text, nullable=True)
    corequisites = Column(Text, nullable=True)
    assumed_knowledge = Column(Text, nullable=True)

    # Graduate attributes
    graduate_attributes = Column(JSON, nullable=True)  # List of attributes addressed

    # Status tracking
    status = Column(
        String(20), default=CourseStructureStatus.PLANNING.value, nullable=False
    )
    completion_percentage = Column(Float, default=0.0, nullable=False)

    # Metadata
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    updated_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    approved_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    approved_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    unit = relationship("Unit", back_populates="course_outline")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    learning_outcomes = relationship(
        "UnitLearningOutcome",
        back_populates="course_outline",
        cascade="all, delete-orphan",
        order_by="UnitLearningOutcome.sequence_order",
    )

    weekly_topics = relationship(
        "WeeklyTopic",
        back_populates="course_outline",
        cascade="all, delete-orphan",
        order_by="WeeklyTopic.week_number",
    )

    assessment_plans = relationship(
        "AssessmentPlan",
        back_populates="course_outline",
        cascade="all, delete-orphan",
        order_by="AssessmentPlan.due_week",
    )

    def __repr__(self):
        return f"<CourseOutline(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"

    @property
    def is_complete(self) -> bool:
        """Check if course outline is complete"""
        return (
            self.learning_outcomes
            and self.weekly_topics
            and self.assessment_plans
            and self.completion_percentage >= 100
        )

    @property
    def total_assessment_weight(self) -> float:
        """Calculate total assessment weight percentage"""
        if not self.assessment_plans:
            return 0.0
        return sum(plan.weight_percentage for plan in self.assessment_plans)

    def update_completion_percentage(self):
        """Update completion percentage based on components"""
        components = 0
        total = 5  # Total components to check

        if self.description and self.rationale:
            components += 1
        if self.learning_outcomes and len(self.learning_outcomes) >= 3:
            components += 1
        if self.weekly_topics and len(self.weekly_topics) >= self.duration_weeks:
            components += 1
        if self.assessment_plans and self.total_assessment_weight == 100:
            components += 1
        if self.graduate_attributes:
            components += 1

        self.completion_percentage = (components / total) * 100
