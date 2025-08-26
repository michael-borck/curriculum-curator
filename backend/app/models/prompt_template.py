"""
Database model for storing customizable prompt templates
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


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

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False, default=TemplateType.CUSTOM)
    template_content = Column(Text, nullable=False)
    variables = Column(Text)  # JSON list of expected variables
    status = Column(String(20), default=TemplateStatus.ACTIVE)

    # Ownership and versioning
    owner_id = Column(
        GUID(), ForeignKey("users.id"), nullable=True
    )  # NULL = system template
    is_system = Column(Boolean, default=False)  # System templates can't be deleted
    is_public = Column(Boolean, default=False)  # Can other users use this template?
    parent_id = Column(
        GUID(), ForeignKey("prompt_templates.id"), nullable=True
    )  # For versioning
    version = Column(Integer, default=1)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)

    # Metadata
    tags = Column(Text)  # JSON array of tags
    model_preferences = Column(Text)  # JSON object with model-specific settings
    example_output = Column(Text)  # Example of expected output

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", backref="prompt_templates")
    children = relationship("PromptTemplate", backref="parent", remote_side=[id])

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "template_content": self.template_content,
            "variables": self.variables,
            "status": self.status,
            "is_system": self.is_system,
            "is_public": self.is_public,
            "version": self.version,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def increment_usage(self):
        """Increment usage counter and update last used timestamp"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()

    def create_version(self, new_content: str, user_id: str) -> "PromptTemplate":
        """Create a new version of this template"""
        return PromptTemplate(
            name=f"{self.name} (v{self.version + 1})",
            description=self.description,
            type=self.type,
            template_content=new_content,
            variables=self.variables,
            owner_id=user_id,
            is_system=False,
            parent_id=self.id,
            version=self.version + 1,
            tags=self.tags,
            model_preferences=self.model_preferences,
        )
