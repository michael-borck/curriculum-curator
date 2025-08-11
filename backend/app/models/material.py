"""
Material and content versioning models
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

    # Content storage
    content = Column(JSON, nullable=False)  # Structured content
    raw_content = Column(Text, nullable=True)  # Raw markdown/HTML

    # Version tracking
    version = Column(Integer, default=1, nullable=False)
    parent_version_id = Column(GUID(), ForeignKey("materials.id"), nullable=True)
    is_latest = Column(Boolean, default=True, nullable=False)

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
    parent_version = relationship("Material", remote_side=[id])
    child_versions = relationship("Material", back_populates="parent_version")

    def __repr__(self):
        return f"<Material(id={self.id}, type='{self.type}', title='{self.title}', v{self.version})>"
