"""
Chat models for "Chat with Course" functionality
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.unit import Unit
    from app.models.user import User


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

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Session information
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500))

    # Context configuration
    context_scope: Mapped[str] = mapped_column(
        String(20), default=ContextScope.UNIT.value
    )
    context_content_ids: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # Specific content IDs for context
    context_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Additional context information

    # Session settings
    llm_model: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Specific model used
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    last_activity_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="chat_sessions")
    user: Mapped["User"] = relationship()
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ChatSession(id={self.id}, title='{self.title}', unit_id={self.unit_id})>"
        )

    @property
    def message_count(self) -> int:
        """Get total number of messages in session"""
        return len(self.messages) if self.messages else 0

    @property
    def is_unit_context(self) -> bool:
        """Check if session uses full unit context"""
        return str(self.context_scope) == ContextScope.UNIT.value

    @property
    def is_content_specific(self) -> bool:
        """Check if session is content-specific"""
        return str(self.context_scope) == ContextScope.CONTENT.value

    @property
    def has_recent_activity(self) -> bool:
        """Check if session has activity in the last 24 hours"""
        if not self.last_activity_at:
            return False
        time_diff = datetime.now(UTC) - self.last_activity_at
        return time_diff.days == 0


class ChatMessage(Base):
    """Chat message model for conversation history"""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Message information
    session_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), index=True)  # ChatRole enum
    content: Mapped[str] = mapped_column(Text)  # Message content in markdown

    # Message metadata
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Token counts, model info, etc.
    context_used: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Context information used for this message

    # Generation information (for assistant messages)
    generation_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # LLM generation details

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role='{self.role}', session_id={self.session_id})>"

    @property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return str(self.role) == ChatRole.USER.value

    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return str(self.role) == ChatRole.ASSISTANT.value

    @property
    def is_system_message(self) -> bool:
        """Check if message is system message"""
        return str(self.role) == ChatRole.SYSTEM.value

    @property
    def content_preview(self) -> str:
        """Get truncated content for preview"""
        content_str = str(self.content)
        if len(content_str) <= 100:
            return content_str
        return content_str[:97] + "..."
