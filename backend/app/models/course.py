"""
Course and module models for curriculum management
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


class CourseStatus(str, Enum):
    """Course development status"""

    PLANNING = "planning"
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class ModuleType(str, Enum):
    """Module delivery type"""

    FLIPPED = "flipped"
    TRADITIONAL = "traditional"
    WORKSHOP = "workshop"
    LAB = "lab"
    SEMINAR = "seminar"
    HYBRID = "hybrid"


class Course(Base):
    """Course model for curriculum management"""

    __tablename__ = "courses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Basic information
    title = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    # Teaching configuration
    teaching_philosophy = Column(String(50), nullable=False)
    language_preference = Column(String(10), default="en-AU", nullable=False)

    # Status and metadata
    status = Column(String(20), default=CourseStatus.PLANNING.value, nullable=False)
    semester = Column(String(50), nullable=True)
    credits = Column(Integer, nullable=True)

    # Course structure (JSON)
    course_metadata = Column(JSON, nullable=True)  # Additional course metadata
    prerequisites = Column(JSON, nullable=True)  # List of prerequisite courses
    learning_objectives = Column(JSON, nullable=True)  # Course-level objectives
    assessment_structure = Column(JSON, nullable=True)  # Grading breakdown

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="courses")
    modules = relationship(
        "CourseModule", back_populates="course", cascade="all, delete-orphan"
    )
    lrds = relationship("LRD", back_populates="course", cascade="all, delete-orphan")
    materials = relationship(
        "Material", back_populates="course", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="course", cascade="all, delete-orphan"
    )
    task_lists = relationship(
        "TaskList", back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Course(id={self.id}, code='{self.code}', title='{self.title}')>"

    @property
    def is_active(self) -> bool:
        """Check if course is active"""
        return self.status == CourseStatus.ACTIVE.value

    @property
    def progress_percentage(self) -> float:
        """Calculate course completion percentage"""
        if not self.modules:
            return 0.0
        completed = sum(1 for m in self.modules if m.is_complete)
        return (completed / len(self.modules)) * 100


class CourseModule(Base):
    """Individual module/week within a course"""

    __tablename__ = "course_modules"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(GUID(), ForeignKey("courses.id"), nullable=False, index=True)

    # Module information
    number = Column(Integer, nullable=False)  # Week/module number
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Module configuration
    type = Column(String(20), default=ModuleType.TRADITIONAL.value, nullable=False)
    duration_minutes = Column(Integer, nullable=True)  # Expected duration

    # Module content structure (JSON)
    pre_class_content = Column(JSON, nullable=True)  # Pre-class modules for flipped
    in_class_content = Column(JSON, nullable=True)  # In-class activities
    post_class_content = Column(JSON, nullable=True)  # Post-class reflection/extension

    # Status tracking
    is_complete = Column(Boolean, default=False, nullable=False)
    materials_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    course = relationship("Course", back_populates="modules")
    materials = relationship(
        "Material", back_populates="module", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<CourseModule(id={self.id}, number={self.number}, title='{self.title}')>"
        )

    @property
    def is_flipped(self) -> bool:
        """Check if module uses flipped classroom approach"""
        return self.type == ModuleType.FLIPPED.value
