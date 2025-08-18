"""
Unit model for Australian university unit management
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


class UnitStatus(str, Enum):
    """Unit status enumeration"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Semester(str, Enum):
    """Australian semester enumeration"""

    SEMESTER_1 = "semester_1"  # Feb-Jun
    SEMESTER_2 = "semester_2"  # Jul-Nov
    SUMMER = "summer"  # Nov-Feb
    WINTER = "winter"  # Jun-Jul


class DifficultyLevel(str, Enum):
    """Unit difficulty levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PedagogyType(str, Enum):
    """Teaching pedagogy types"""

    INQUIRY_BASED = "inquiry-based"
    PROJECT_BASED = "project-based"
    TRADITIONAL = "traditional"
    COLLABORATIVE = "collaborative"
    GAME_BASED = "game-based"
    CONSTRUCTIVIST = "constructivist"
    PROBLEM_BASED = "problem-based"
    EXPERIENTIAL = "experiential"
    COMPETENCY_BASED = "competency-based"


class Unit(Base):
    """Unit model for Australian university unit management"""

    __tablename__ = "units"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Basic unit information
    title = Column(String(500), nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)  # e.g., "COMP1001"
    description = Column(Text, nullable=True)

    # Academic scheduling
    year = Column(Integer, nullable=False, index=True)
    semester = Column(String(20), nullable=False, index=True)  # Semester enum
    status = Column(
        String(20), default=UnitStatus.DRAFT.value, nullable=False, index=True
    )

    # Teaching approach
    pedagogy_type = Column(
        String(30), default=PedagogyType.INQUIRY_BASED.value, nullable=False
    )
    difficulty_level = Column(
        String(20), default=DifficultyLevel.INTERMEDIATE.value, nullable=False
    )
    duration_weeks = Column(Integer, default=12, nullable=False)

    # Ownership and access control
    owner_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    updated_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Additional metadata and context
    unit_metadata = Column(JSON, nullable=True)  # Custom fields, search data, etc.
    generation_context = Column(Text, nullable=True)  # Context for LLM generation

    # Credit points and prerequisites (Australian system)
    credit_points = Column(
        Integer, default=6, nullable=False
    )  # Standard Australian credit points
    prerequisites = Column(Text, nullable=True)
    learning_hours = Column(Integer, nullable=True)  # Total student learning hours

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    published_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_units")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    learning_outcomes = relationship(
        "UnitLearningOutcome", back_populates="unit", cascade="all, delete-orphan"
    )
    contents = relationship(
        "Content", back_populates="unit", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="unit", cascade="all, delete-orphan"
    )
    workflow_chat_sessions = relationship(
        "WorkflowChatSession", back_populates="unit", cascade="all, delete-orphan"
    )
    materials = relationship(
        "Material", back_populates="unit", cascade="all, delete-orphan"
    )
    unit_outline = relationship(
        "UnitOutline", back_populates="unit", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Unit(id={self.id}, code='{self.code}', title='{self.title[:50]}...', status='{self.status}')>"

    @property
    def is_draft(self) -> bool:
        """Check if unit is in draft status"""
        return self.status == UnitStatus.DRAFT.value

    @property
    def is_active(self) -> bool:
        """Check if unit is active/published"""
        return self.status == UnitStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        """Check if unit is archived"""
        return self.status == UnitStatus.ARCHIVED.value

    @property
    def full_code(self) -> str:
        """Get full unit code with year and semester"""
        return f"{self.code}_{self.year}_{self.semester}"
