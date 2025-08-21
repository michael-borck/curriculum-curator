"""
LLM configuration models for user and system-wide settings
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class LLMConfiguration(Base):
    """LLM configuration for users and system"""

    __tablename__ = "llm_configurations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Provider configuration
    provider = Column(String(50), nullable=False)
    api_key = Column(Text, nullable=True)  # Encrypted in production
    api_url = Column(String(500), nullable=True)
    bearer_token = Column(Text, nullable=True)  # For Ollama auth

    # Model settings
    model_name = Column(String(100), nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, nullable=True)

    # Additional settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)  # For provider-specific settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="llm_configs")

    def __repr__(self):
        return f"<LLMConfiguration(id={self.id}, provider={self.provider}, user_id={self.user_id})>"


class TokenUsageLog(Base):
    """Track token usage for billing and analytics"""

    __tablename__ = "token_usage_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Usage details
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # Model and provider info
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)

    # Cost tracking
    cost_estimate = Column(Float, nullable=True)

    # Context
    feature = Column(String(100), nullable=True)  # Which feature used tokens
    usage_metadata = Column(JSON, default=dict)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="token_usage")

    def __repr__(self):
        return f"<TokenUsageLog(id={self.id}, user_id={self.user_id}, total_tokens={self.total_tokens})>"
