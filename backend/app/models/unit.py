"""
Unit model for Australian university unit management
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.accreditation_mappings import UnitAoLMapping, UnitSDGMapping
    from app.models.assessment import Assessment
    from app.models.chat import ChatSession
    from app.models.custom_alignment_framework import CustomAlignmentFramework
    from app.models.learning_design import LearningDesign
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.research_source import ResearchSource
    from app.models.task_list import TaskList
    from app.models.unit_outline import UnitOutline
    from app.models.user import User
    from app.models.weekly_material import WeeklyMaterial


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

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Basic unit information
    title: Mapped[str] = mapped_column(String(500), index=True)
    code: Mapped[str] = mapped_column(String(20), index=True)  # e.g., "COMP1001"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Academic scheduling
    year: Mapped[int] = mapped_column(Integer, index=True)
    semester: Mapped[str] = mapped_column(String(20), index=True)  # Semester enum
    status: Mapped[str] = mapped_column(
        String(20), default=UnitStatus.DRAFT.value, index=True
    )

    # Teaching approach
    pedagogy_type: Mapped[str] = mapped_column(
        String(30), default=PedagogyType.INQUIRY_BASED.value
    )
    difficulty_level: Mapped[str] = mapped_column(
        String(20), default=DifficultyLevel.INTERMEDIATE.value
    )
    duration_weeks: Mapped[int] = mapped_column(Integer, default=12)
    topic_label: Mapped[str] = mapped_column(String(50), default="Week")
    unit_label: Mapped[str] = mapped_column(String(50), default="Learning Program")

    # Ownership and access control
    owner_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    created_by_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), index=True
    )
    updated_by_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )

    # Additional metadata and context
    unit_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    generation_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    import_provenance: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )

    # Credit points and prerequisites (Australian system)
    credit_points: Mapped[int] = mapped_column(default=6)
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_hours: Mapped[int | None] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship(
        foreign_keys=[owner_id], back_populates="owned_units"
    )
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])
    updated_by: Mapped["User | None"] = relationship(foreign_keys=[updated_by_id])
    learning_outcomes: Mapped[list["UnitLearningOutcome"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    unit_outline: Mapped["UnitOutline | None"] = relationship(
        back_populates="unit",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # New relationships for unit structure
    weekly_materials: Mapped[list["WeeklyMaterial"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    designs: Mapped[list["LearningDesign"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    task_lists: Mapped[list["TaskList"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )

    # Accreditation mappings
    aol_mappings: Mapped[list["UnitAoLMapping"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    sdg_mappings: Mapped[list["UnitSDGMapping"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    custom_frameworks: Mapped[list["CustomAlignmentFramework"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )

    # Research sources
    research_sources: Mapped[list["ResearchSource"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )

    # Add composite unique constraint for code + year + semester per owner
    __table_args__ = (
        UniqueConstraint(
            "code",
            "year",
            "semester",
            "owner_id",
            name="_unit_code_year_semester_owner_uc",
        ),
    )

    def __repr__(self) -> str:
        title_preview = str(self.title)[:50] if self.title else ""
        return f"<Unit(id={self.id}, code='{self.code}', title='{title_preview}...', status='{self.status}')>"

    @property
    def is_draft(self) -> bool:
        """Check if unit is in draft status"""
        return str(self.status) == UnitStatus.DRAFT.value

    @property
    def is_active(self) -> bool:
        """Check if unit is active/published"""
        return str(self.status) == UnitStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        """Check if unit is archived"""
        return str(self.status) == UnitStatus.ARCHIVED.value

    @property
    def full_code(self) -> str:
        """Get full unit code with year and semester"""
        return f"{self.code}_{self.year}_{self.semester}"
