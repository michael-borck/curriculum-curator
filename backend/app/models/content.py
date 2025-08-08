"""
Content model for unit materials (lectures, worksheets, etc.)
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
    READING = "reading"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    ASSESSMENT = "assessment"


class ContentStatus(str, Enum):
    """Content status enumeration"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Content(Base):
    """Content model for unit materials"""

    __tablename__ = "contents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Basic content information
    title = Column(String(500), nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # ContentType enum
    status = Column(
        String(20), default=ContentStatus.DRAFT.value, nullable=False, index=True
    )

    # Content data (stored as Markdown)
    content_markdown = Column(Text, nullable=True)  # Source markdown
    content_html = Column(Text, nullable=True)  # Generated HTML for display
    summary = Column(Text, nullable=True)  # Auto-generated summary

    # Hierarchical organization
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)
    parent_content_id = Column(
        GUID(), ForeignKey("contents.id"), nullable=True, index=True
    )
    order_index = Column(Integer, default=0, nullable=False)

    # Educational metadata
    learning_objectives = Column(JSON, nullable=True)  # List of objectives
    estimated_duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String(20), nullable=True)
    prerequisites = Column(JSON, nullable=True)  # List of prerequisite content IDs

    # Generation and validation metadata
    generation_metadata = Column(JSON, nullable=True)  # LLM generation info
    validation_metadata = Column(JSON, nullable=True)  # Plugin validation results

    # Additional metadata and settings
    content_metadata = Column(JSON, nullable=True)  # Custom fields, settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    published_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    # Relationships
    unit = relationship("Unit", back_populates="contents")
    parent_content = relationship(
        "Content", remote_side=[id], back_populates="child_contents"
    )
    child_contents = relationship(
        "Content", back_populates="parent_content", cascade="all, delete-orphan"
    )
    versions = relationship(
        "ContentVersion", back_populates="content", cascade="all, delete-orphan"
    )
    quiz_questions = relationship(
        "QuizQuestion", back_populates="content", cascade="all, delete-orphan"
    )
    validation_results = relationship(
        "ValidationResult", back_populates="content", cascade="all, delete-orphan"
    )
    generation_history = relationship(
        "GenerationHistory", back_populates="content", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Content(id={self.id}, type='{self.type}', title='{self.title[:50]}...', status='{self.status}')>"

    @property
    def is_draft(self) -> bool:
        """Check if content is in draft status"""
        return self.status == ContentStatus.DRAFT.value

    @property
    def is_active(self) -> bool:
        """Check if content is active/published"""
        return self.status == ContentStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        """Check if content is archived"""
        return self.status == ContentStatus.ARCHIVED.value

    @property
    def is_quiz(self) -> bool:
        """Check if content is a quiz type"""
        return self.type in [
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
