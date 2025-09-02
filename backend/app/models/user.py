"""
User model for authentication and profile management
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.common import GUID


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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.LECTURER.value, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Institution and academic details
    institution = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    position_title = Column(String(255), nullable=True)

    # Teaching preferences
    teaching_philosophy = Column(
        String(50), default=TeachingPhilosophy.MIXED_APPROACH.value, nullable=False
    )
    language_preference = Column(String(10), default="en-AU", nullable=False)

    # Teaching preferences and LLM configuration (JSON fields)
    teaching_preferences = Column(
        JSON, nullable=True
    )  # Additional pedagogy preferences
    llm_config = Column(JSON, nullable=True)  # API keys (encrypted), model preferences
    content_generation_context = Column(Text, nullable=True)  # Default context for LLM

    # Relationships
    llm_configs = relationship(
        "LLMConfiguration", back_populates="user", cascade="all, delete-orphan"
    )
    token_usage = relationship(
        "TokenUsageLog", back_populates="user", cascade="all, delete-orphan"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    email_verifications = relationship(
        "EmailVerification", back_populates="user", cascade="all, delete-orphan"
    )
    password_resets = relationship(
        "PasswordReset", back_populates="user", cascade="all, delete-orphan"
    )
    quarto_presets = relationship("QuartoPreset", back_populates="user", cascade="all, delete-orphan")
    owned_units = relationship(
        "Unit", foreign_keys="Unit.owner_id", back_populates="owner"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN.value

    @property
    def is_lecturer(self) -> bool:
        """Check if user has lecturer role"""
        return self.role == UserRole.LECTURER.value

    @property
    def is_student(self) -> bool:
        """Check if user has student role"""
        return self.role == UserRole.STUDENT.value
