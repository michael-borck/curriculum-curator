"""
Generation history model for tracking LLM content generation
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.unit import Unit
    from app.models.user import User


class GenerationType(str, Enum):
    """Generation type enumeration"""

    CONTENT_CREATION = "content_creation"
    CONTENT_ENHANCEMENT = "content_enhancement"
    ULO_GENERATION = "ulo_generation"
    QUIZ_GENERATION = "quiz_generation"
    SUMMARY_GENERATION = "summary_generation"
    CHAT_RESPONSE = "chat_response"


class GenerationHistory(Base):
    """Generation history model for tracking LLM content generation"""

    __tablename__ = "generation_history"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Content and context information
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=False, index=True
    )
    content_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("contents.id"), index=True, default=None
    )  # Optional for unit-level generation
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )

    # Generation details
    generation_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # GenerationType enum
    llm_provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # openai, anthropic, etc.
    model_used: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # gpt-4, claude-3, etc.

    # Input and output
    prompt_used: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Full prompt sent to LLM
    input_context: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Context data provided
    generated_content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Generated content

    # Generation metadata
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Input/output token counts
    generation_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Temperature, max_tokens, etc.
    execution_time_ms: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Performance metrics

    # Quality and usage tracking
    user_rating: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # User feedback on generated content
    usage_status: Mapped[str] = mapped_column(
        String(20), default="generated", nullable=False
    )  # generated, edited, used, discarded

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    unit: Mapped[Unit] = relationship("Unit")
    content: Mapped[Content | None] = relationship(
        "Content", back_populates="generation_history"
    )
    user: Mapped[User] = relationship("User")

    def __repr__(self) -> str:
        return f"<GenerationHistory(id={self.id}, type='{self.generation_type}', model='{self.model_used}')>"

    @property
    def is_content_generation(self) -> bool:
        """Check if this is content creation or enhancement"""
        return str(self.generation_type) in [
            GenerationType.CONTENT_CREATION.value,
            GenerationType.CONTENT_ENHANCEMENT.value,
        ]

    @property
    def is_quiz_generation(self) -> bool:
        """Check if this is quiz-related generation"""
        return str(self.generation_type) == GenerationType.QUIZ_GENERATION.value

    @property
    def has_token_usage(self) -> bool:
        """Check if token usage information is available"""
        token_usage = self.token_usage
        return token_usage is not None and len(token_usage) > 0

    @property
    def total_tokens(self) -> int:
        """Get total token usage (input + output)"""
        token_usage = self.token_usage
        if not token_usage:
            return 0
        return token_usage.get("input_tokens", 0) + token_usage.get("output_tokens", 0)

    @property
    def was_used(self) -> bool:
        """Check if generated content was actually used"""
        return str(self.usage_status) in ["used", "edited"]
