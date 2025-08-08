"""
Chat models for "Chat with Course" functionality
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class ChatRole(str, Enum):
    """Chat message role enumeration"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContextScope(str, Enum):
    """Context scope for chat sessions"""

    UNIT = "unit"  # Entire unit context
    CONTENT = "content"  # Specific content item
    TOPIC = "topic"  # Topic-based context
    CUSTOM = "custom"  # Custom-defined context


class ChatSession(Base):
    """Chat session model for unit conversations"""

    __tablename__ = "chat_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Session information
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)

    # Context configuration
    context_scope = Column(String(20), default=ContextScope.UNIT.value, nullable=False)
    context_content_ids = Column(
        JSON, nullable=True
    )  # Specific content IDs for context
    context_metadata = Column(JSON, nullable=True)  # Additional context information

    # Session settings
    llm_model = Column(String(100), nullable=True)  # Specific model used
    system_prompt = Column(Text, nullable=True)  # Custom system prompt

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    unit = relationship("Unit", back_populates="chat_sessions")
    user = relationship("User")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<ChatSession(id={self.id}, title='{self.title}', unit_id={self.unit_id})>"
        )

    @property
    def message_count(self) -> int:
        """Get total number of messages in session"""
        return len(self.messages)

    @property
    def is_unit_context(self) -> bool:
        """Check if session uses full unit context"""
        return self.context_scope == ContextScope.UNIT.value

    @property
    def is_content_specific(self) -> bool:
        """Check if session is content-specific"""
        return self.context_scope == ContextScope.CONTENT.value

    @property
    def has_recent_activity(self) -> bool:
        """Check if session has activity in the last 24 hours"""
        if not self.last_activity_at:
            return False
        time_diff = datetime.utcnow() - self.last_activity_at
        return time_diff.days == 0


class ChatMessage(Base):
    """Chat message model for conversation history"""

    __tablename__ = "chat_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Message information
    session_id = Column(
        GUID(), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False, index=True)  # ChatRole enum
    content = Column(Text, nullable=False)  # Message content in markdown

    # Message metadata
    message_metadata = Column(JSON, nullable=True)  # Token counts, model info, etc.
    context_used = Column(
        JSON, nullable=True
    )  # Context information used for this message

    # Generation information (for assistant messages)
    generation_metadata = Column(JSON, nullable=True)  # LLM generation details

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', session_id={self.session_id})>"

    @property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.role == ChatRole.USER.value

    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.role == ChatRole.ASSISTANT.value

    @property
    def is_system_message(self) -> bool:
        """Check if message is system message"""
        return self.role == ChatRole.SYSTEM.value

    @property
    def content_preview(self) -> str:
        """Get truncated content for preview"""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."
