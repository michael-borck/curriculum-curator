"""
User model for authentication and profile management
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.email_verification import EmailVerification
    from app.models.llm_config import LLMConfiguration, TokenUsageLog
    from app.models.password_reset import PasswordReset
    from app.models.research_source import ResearchSource
    from app.models.unit import Unit


class UserRole(str, Enum):
    """User role enumeration"""

    ADMIN = "admin"
    LECTURER = "lecturer"
    STUDENT = "student"
    ASSISTANT = "assistant"  # Teaching assistant role


class TeachingPhilosophy(str, Enum):
    """Teaching philosophy styles"""

    TRADITIONAL_LECTURE = "traditional_lecture"
    CONSTRUCTIVIST = "constructivist"
    DIRECT_INSTRUCTION = "direct_instruction"
    INQUIRY_BASED = "inquiry_based"
    FLIPPED_CLASSROOM = "flipped_classroom"
    PROJECT_BASED = "project_based"
    COMPETENCY_BASED = "competency_based"
    CULTURALLY_RESPONSIVE = "culturally_responsive"
    MIXED_APPROACH = "mixed_approach"


class User(Base):
    """User model for authentication and profile management"""

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Core fields
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.LECTURER.value)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Institution and academic details
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Teaching preferences
    teaching_philosophy: Mapped[str] = mapped_column(
        String(50), default=TeachingPhilosophy.MIXED_APPROACH.value
    )
    language_preference: Mapped[str] = mapped_column(String(10), default="en-AU")
    education_sector: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # JSON fields for flexible configuration
    teaching_preferences: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Additional pedagogy preferences
    llm_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # API keys (encrypted), model preferences
    content_generation_context: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Default context for LLM

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    llm_configs: Mapped[list["LLMConfiguration"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    token_usage: Mapped[list["TokenUsageLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    email_verifications: Mapped[list["EmailVerification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_resets: Mapped[list["PasswordReset"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    owned_units: Mapped[list["Unit"]] = relationship(
        foreign_keys="Unit.owner_id", back_populates="owner"
    )
    research_sources: Mapped[list["ResearchSource"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return str(self.role) == UserRole.ADMIN.value

    @property
    def is_lecturer(self) -> bool:
        """Check if user has lecturer role"""
        return str(self.role) == UserRole.LECTURER.value

    @property
    def is_student(self) -> bool:
        """Check if user has student role"""
        return str(self.role) == UserRole.STUDENT.value
