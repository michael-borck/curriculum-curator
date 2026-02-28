"""
LLM configuration models for user and system-wide settings
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.user import User


class LLMConfiguration(Base):
    """LLM configuration for users and system"""

    __tablename__ = "llm_configurations"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Provider configuration
    provider: Mapped[str] = mapped_column(String(50))
    api_key: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Encrypted in production
    api_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bearer_token: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # For Ollama auth

    # Model settings
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, default=0.7, nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Additional settings
    is_default: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=dict
    )  # For provider-specific settings

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="llm_configs")

    def __repr__(self) -> str:
        return f"<LLMConfiguration(id={self.id}, provider={self.provider}, user_id={self.user_id})>"


class TokenUsageLog(Base):
    """Track token usage for billing and analytics"""

    __tablename__ = "token_usage_logs"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Usage details
    prompt_tokens: Mapped[int] = mapped_column(Integer)
    completion_tokens: Mapped[int] = mapped_column(Integer)
    total_tokens: Mapped[int] = mapped_column(Integer)

    # Model and provider info
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))

    # Cost tracking
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Context
    feature: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Which feature used tokens
    usage_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="token_usage")

    def __repr__(self) -> str:
        return f"<TokenUsageLog(id={self.id}, user_id={self.user_id}, total_tokens={self.total_tokens})>"
