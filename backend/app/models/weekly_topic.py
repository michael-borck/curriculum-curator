"""
Weekly topic model for course schedule management
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Links
    unit_outline_id = Column(
        GUID(), ForeignKey("unit_outlines.id"), nullable=False, index=True
    )
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=True, index=True)

    # Week details
    week_number = Column(Integer, nullable=False, index=True)
    week_type = Column(String(20), default=WeekType.REGULAR.value, nullable=False)
    topic_title = Column(String(500), nullable=False)
    topic_description = Column(Text, nullable=True)

    # Learning focus
    key_concepts = Column(JSON, nullable=True)  # List of main concepts
    learning_objectives = Column(Text, nullable=True)  # Week-specific objectives

    # Pre-class components (Flipped classroom)
    pre_class_modules = Column(JSON, nullable=True)  # List of module descriptions
    pre_class_duration_minutes = Column(Integer, default=60, nullable=True)
    pre_class_resources = Column(JSON, nullable=True)  # Links, readings, videos

    # In-class components
    in_class_activities = Column(JSON, nullable=True)  # List of activities
    in_class_duration_minutes = Column(Integer, default=120, nullable=True)
    in_class_format = Column(String(50), nullable=True)  # lecture, workshop, lab

    # Post-class components
    post_class_tasks = Column(JSON, nullable=True)  # Homework, reflection
    post_class_duration_minutes = Column(Integer, default=60, nullable=True)

    # Assessment information
    has_assessment = Column(Boolean, default=False, nullable=False)
    assessment_details = Column(Text, nullable=True)

    # Resources and materials
    required_readings = Column(JSON, nullable=True)
    supplementary_resources = Column(JSON, nullable=True)
    equipment_required = Column(Text, nullable=True)

    # Status
    is_complete = Column(Boolean, default=False, nullable=False)
    content_ready = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)  # Internal notes for instructors

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    unit_outline = relationship("UnitOutline", back_populates="weekly_topics")
    unit = relationship("Unit")
    created_by = relationship("User", foreign_keys=[created_by_id])

    learning_outcomes = relationship(
        "UnitLearningOutcome",
        back_populates="weekly_topic",
        cascade="all, delete-orphan",
    )

    contents = relationship(
        "Content",
        foreign_keys="Content.week_number",
        primaryjoin=("and_(WeeklyTopic.unit_id==Content.unit_id, "
                     "WeeklyTopic.week_number==Content.week_number)"),
        viewonly=True,
    )

    def __repr__(self):
        return f"<WeeklyTopic(id={self.id}, week={self.week_number}, title='{self.topic_title[:50]}...', type='{self.week_type}')>"

    @property
    def total_student_hours(self) -> float:
        """Calculate total student hours for the week"""
        pre = (self.pre_class_duration_minutes or 0) / 60
        during = (self.in_class_duration_minutes or 0) / 60
        post = (self.post_class_duration_minutes or 0) / 60
        return pre + during + post

    @property
    def is_teaching_week(self) -> bool:
        """Check if this is a regular teaching week"""
        return self.week_type == WeekType.REGULAR.value

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

    def get_content_by_category(self, category: str):
        """Get content items for a specific category (pre/in/post)"""
        return [c for c in self.contents if c.content_category == category]

    def update_completion_status(self):
        """Update completion status based on content"""
        self.is_complete = (
            self.has_pre_class_content
            and self.has_in_class_content
            and self.learning_outcomes
            and len(self.learning_outcomes) > 0
        )

        self.content_ready = (
            self.is_complete
            and len(self.get_content_by_category("pre_class")) > 0
            and len(self.get_content_by_category("in_class")) > 0
        )
