"""
Generation history model for tracking LLM content generation
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Content and context information
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)
    content_id = Column(
        GUID(), ForeignKey("contents.id"), nullable=True, index=True
    )  # Optional for unit-level generation
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Generation details
    generation_type = Column(
        String(30), nullable=False, index=True
    )  # GenerationType enum
    llm_provider = Column(String(50), nullable=False)  # openai, anthropic, etc.
    model_used = Column(String(100), nullable=False)  # gpt-4, claude-3, etc.

    # Input and output
    prompt_used = Column(Text, nullable=False)  # Full prompt sent to LLM
    input_context = Column(JSON, nullable=True)  # Context data provided
    generated_content = Column(Text, nullable=False)  # Generated content

    # Generation metadata
    token_usage = Column(JSON, nullable=True)  # Input/output token counts
    generation_settings = Column(JSON, nullable=True)  # Temperature, max_tokens, etc.
    execution_time_ms = Column(JSON, nullable=True)  # Performance metrics

    # Quality and usage tracking
    user_rating = Column(JSON, nullable=True)  # User feedback on generated content
    usage_status = Column(
        String(20), default="generated", nullable=False
    )  # generated, edited, used, discarded

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    unit = relationship("Unit")
    content = relationship("Content", back_populates="generation_history")
    user = relationship("User")

    def __repr__(self):
        return f"<GenerationHistory(id={self.id}, type='{self.generation_type}', model='{self.model_used}')>"

    @property
    def is_content_generation(self) -> bool:
        """Check if this is content creation or enhancement"""
        return self.generation_type in [
            GenerationType.CONTENT_CREATION.value,
            GenerationType.CONTENT_ENHANCEMENT.value,
        ]

    @property
    def is_quiz_generation(self) -> bool:
        """Check if this is quiz-related generation"""
        return self.generation_type == GenerationType.QUIZ_GENERATION.value

    @property
    def has_token_usage(self) -> bool:
        """Check if token usage information is available"""
        return self.token_usage is not None

    @property
    def total_tokens(self) -> int:
        """Get total token usage (input + output)"""
        if not self.token_usage:
            return 0
        return self.token_usage.get("input_tokens", 0) + self.token_usage.get(
            "output_tokens", 0
        )

    @property
    def was_used(self) -> bool:
        """Check if generated content was actually used"""
        return self.usage_status in ["used", "edited"]
