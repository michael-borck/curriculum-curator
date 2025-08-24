"""
Weekly Material model for course content management
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
    """Types of learning materials"""

    LECTURE = "lecture"
    HANDOUT = "handout"
    QUIZ = "quiz"
    CASE_STUDY = "case_study"
    RESOURCE = "resource"
    NOTES = "notes"
    VIDEO = "video"
    READING = "reading"
    ACTIVITY = "activity"
    DISCUSSION = "discussion"


class MaterialStatus(str, Enum):
    """Material completion status"""

    DRAFT = "draft"
    COMPLETE = "complete"
    NEEDS_REVIEW = "needs_review"
    PUBLISHED = "published"


class WeeklyMaterial(Base):
    """Learning materials organized by week"""

    __tablename__ = "weekly_materials"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Parent relationships
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)
    week_number = Column(Integer, nullable=False, index=True)

    # Material details
    title = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False, index=True)  # MaterialType enum
    description = Column(Text, nullable=True)

    # Content and metadata
    duration_minutes = Column(Integer, nullable=True)  # Estimated time to complete
    file_path = Column(String(500), nullable=True)  # Path to git-stored content
    material_metadata = Column("metadata", JSON, nullable=True)  # Additional data (pages, questions, etc.)

    # Organization
    order_index = Column(Integer, nullable=False, default=0)
    status = Column(
        String(20), nullable=False, default=MaterialStatus.DRAFT.value, index=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    unit = relationship("Unit", back_populates="weekly_materials")

    # Local learning outcomes (material-specific)
    local_outcomes = relationship(
        "LocalLearningOutcome", back_populates="material", cascade="all, delete-orphan"
    )

    # Many-to-many with ULOs through mapping table
    learning_outcomes = relationship(
        "UnitLearningOutcome",
        secondary="material_ulo_mappings",
        backref="materials"
    )

    # Many-to-many with assessments through mapping table
    assessments = relationship(
        "Assessment",
        secondary="assessment_material_links",
        back_populates="linked_materials"
    )

    def __repr__(self):
        return f"<WeeklyMaterial(id={self.id}, title='{self.title}', week={self.week_number}, type='{self.type}')>"

    @property
    def is_complete(self) -> bool:
        """Check if material is complete"""
        return self.status in [MaterialStatus.COMPLETE.value, MaterialStatus.PUBLISHED.value]

    @property
    def estimated_hours(self) -> float:
        """Get estimated time in hours"""
        if self.duration_minutes:
            return self.duration_minutes / 60.0
        return 0.0

    @property
    def metadata_dict(self) -> dict:
        """Get metadata as dictionary"""
        return self.material_metadata or {}

    def get_metadata(self, key: str, default=None):
        """Get specific metadata value"""
        if self.material_metadata:
            return self.material_metadata.get(key, default)
        return default
