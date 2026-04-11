"""
Database model for storing customizable prompt templates
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.user import User


class TemplateType(str, Enum):
    """Types of prompt templates"""

    UNIT_STRUCTURE = "unit_structure"
    LEARNING_OUTCOMES = "learning_outcomes"
    LECTURE = "lecture"
    QUIZ = "quiz"
    RUBRIC = "rubric"
    CASE_STUDY = "case_study"
    TUTORIAL = "tutorial"
    LAB = "lab"
    ASSIGNMENT = "assignment"
    CUSTOM = "custom"


class TemplateStatus(str, Enum):
    """Template status"""

    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class PromptTemplate(Base):
    """Stores customizable prompt templates"""

    __tablename__ = "prompt_templates"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=TemplateType.CUSTOM.value
    )
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # JSON list of expected variables
    status: Mapped[str] = mapped_column(String(20), default=TemplateStatus.ACTIVE.value)

    # Ownership and versioning
    owner_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("users.id"), default=None
    )  # NULL = system template
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # System templates can't be deleted
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Can other users use this template?
    parent_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("prompt_templates.id"), default=None
    )  # For versioning
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # Metadata
    tags: Mapped[str | None] = mapped_column(Text, default=None)  # JSON array of tags
    model_preferences: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # JSON object with model-specific settings
    example_output: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # Example of expected output

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner: Mapped[User | None] = relationship("User", backref="prompt_templates")
    children: Mapped[list[PromptTemplate]] = relationship(
        "PromptTemplate", backref="parent", remote_side=[id]
    )

    def to_dict(self) -> dict[str, str | int | bool | None]:
        """Convert to dictionary for API responses"""
        last_used = self.last_used
        created_at = self.created_at
        updated_at = self.updated_at
        return {
            "id": str(self.id),
            "name": str(self.name),
            "description": str(self.description) if self.description else None,
            "type": str(self.type),
            "template_content": str(self.template_content),
            "variables": str(self.variables) if self.variables else None,
            "status": str(self.status),
            "is_system": bool(self.is_system),
            "is_public": bool(self.is_public),
            "version": int(self.version),
            "usage_count": int(self.usage_count),
            "last_used": last_used.isoformat() if last_used else None,
            "created_at": created_at.isoformat() if created_at else "",
            "updated_at": updated_at.isoformat() if updated_at else None,
        }

    def increment_usage(self) -> None:
        """Increment usage counter and update last used timestamp"""
        self.usage_count = int(self.usage_count) + 1
        self.last_used = datetime.now(UTC)

    def create_version(self, new_content: str, user_id: str) -> PromptTemplate:
        """Create a new version of this template"""
        return PromptTemplate(
            name=f"{self.name} (v{int(self.version) + 1})",
            description=self.description,
            type=self.type,
            template_content=new_content,
            variables=self.variables,
            owner_id=user_id,
            is_system=False,
            parent_id=str(self.id),
            version=int(self.version) + 1,
            tags=self.tags,
            model_preferences=self.model_preferences,
        )
