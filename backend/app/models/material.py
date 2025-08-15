"""
Material models with Git-backed content storage
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
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


class MaterialType(str, Enum):
    """Types of course materials"""

    SYLLABUS = "syllabus"
    LECTURE = "lecture"
    WORKSHEET = "worksheet"
    QUIZ = "quiz"
    LAB = "lab"
    CASE_STUDY = "case_study"
    INTERACTIVE_HTML = "interactive_html"
    READING = "reading"
    VIDEO = "video"
    ASSIGNMENT = "assignment"


class Material(Base):
    """Course material with version tracking"""

    __tablename__ = "materials"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(GUID(), ForeignKey("courses.id"), nullable=False, index=True)
    module_id = Column(
        GUID(), ForeignKey("course_modules.id"), nullable=True, index=True
    )

    # Material information
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Git-backed content storage
    git_path = Column(String(500), nullable=False)  # e.g., "courses/cs101/lecture1.md"
    current_commit = Column(String(40), nullable=True)  # Git commit SHA

    # Cached metadata (for quick access without Git)
    content_summary = Column(JSON, nullable=True)  # Quick preview/metadata

    # Validation and quality
    validation_results = Column(JSON, nullable=True)
    quality_score = Column(Integer, nullable=True)  # 0-100

    # Generation context
    generation_context = Column(JSON, nullable=True)  # LLM prompts, settings
    teaching_philosophy = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    course = relationship("Course", back_populates="materials")
    module = relationship("CourseModule", back_populates="materials")

    def __repr__(self):
        return f"<Material(id={self.id}, type='{self.type}', title='{self.title}')>"
