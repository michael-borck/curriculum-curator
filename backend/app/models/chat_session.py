"""
Chat session model for conversational content creation workflow
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.unit import Unit
    from app.models.unit_outline import UnitOutline
    from app.models.user import User


class WorkflowStage(str, Enum):
    """Workflow stage enumeration for content creation"""

    INITIAL = "initial"  # Starting point
    COURSE_OVERVIEW = "course_overview"  # Define course basics
    LEARNING_OUTCOMES = "learning_outcomes"  # Define CLOs
    UNIT_BREAKDOWN = "unit_breakdown"  # Define ULOs
    WEEKLY_PLANNING = "weekly_planning"  # Plan weekly topics
    CONTENT_GENERATION = "content_generation"  # Generate materials
    QUALITY_REVIEW = "quality_review"  # Review and validate
    COMPLETED = "completed"  # Workflow complete


class SessionStatus(str, Enum):
    """Chat session status"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class WorkflowChatSession(Base):
    """Chat session for guided content creation workflow"""

    __tablename__ = "workflow_chat_sessions"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # User and unit association
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=True, index=True
    )
    unit_outline_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("unit_outlines.id"), nullable=True, index=True
    )

    # Session details
    session_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    session_type: Mapped[str] = mapped_column(String(50), default="content_creation")
    status: Mapped[str] = mapped_column(String(20), default=SessionStatus.ACTIVE.value)

    # Workflow tracking
    current_stage: Mapped[str] = mapped_column(
        String(50), default=WorkflowStage.INITIAL.value
    )
    workflow_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Stage-specific data
    context_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Accumulated context

    # Conversation history
    messages: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )  # Array of message objects
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Progress tracking
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    stages_completed: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # List of completed stages

    # Decision tracking
    decisions_made: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Key decisions in workflow
    pending_questions: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # Questions awaiting answers

    # Generated content tracking
    generated_content_ids: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # IDs of created content
    generated_outline_id: Mapped[str | None] = mapped_column(
        GUID(), nullable=True
    )  # Created course outline

    # AI interaction metadata
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Session preferences
    pedagogy_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    complexity_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tone_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(default=func.now())

    # Session duration tracking
    total_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Feedback and quality
    user_satisfaction_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 1-5 rating
    feedback_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    unit: Mapped["Unit | None"] = relationship(back_populates="workflow_chat_sessions")
    unit_outline: Mapped["UnitOutline | None"] = relationship()

    def __repr__(self) -> str:
        return f"<WorkflowChatSession(id={self.id}, user_id={self.user_id}, stage='{self.current_stage}', status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return str(self.status) == SessionStatus.ACTIVE.value

    @property
    def is_completed(self) -> bool:
        """Check if session is completed"""
        return str(self.status) == SessionStatus.COMPLETED.value

    @property
    def stage_index(self) -> int:
        """Get numeric index of current stage"""
        stages = list(WorkflowStage)
        try:
            return stages.index(WorkflowStage(str(self.current_stage)))
        except (ValueError, KeyError):
            return 0

    @property
    def total_stages(self) -> int:
        """Get total number of workflow stages"""
        return len(WorkflowStage) - 1  # Exclude COMPLETED

    def add_message(
        self, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a message to the conversation history"""
        if not self.messages:
            self.messages = []

        message: dict[str, Any] = {
            "role": role,  # user, assistant, system
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        messages_list = list(self.messages) if self.messages else []
        messages_list.append(message)
        self.messages = messages_list
        self.message_count = int(self.message_count) + 1
        self.last_activity_at = datetime.utcnow()

    def advance_stage(self) -> None:
        """Advance to the next workflow stage"""
        stages = list(WorkflowStage)
        current_index = self.stage_index

        if current_index < len(stages) - 1:
            self.current_stage = stages[current_index + 1].value
            self.update_progress()

            stages_list = list(self.stages_completed) if self.stages_completed else []
            stages_list.append(stages[current_index].value)
            self.stages_completed = stages_list

    def update_progress(self) -> None:
        """Update progress percentage based on current stage"""
        self.progress_percentage = (self.stage_index / self.total_stages) * 100

    def add_decision(self, decision_key: str, decision_value: Any) -> None:
        """Record a key decision made during the workflow"""
        decisions = dict(self.decisions_made) if self.decisions_made else {}
        decisions[decision_key] = {
            "value": decision_value,
            "timestamp": datetime.utcnow().isoformat(),
            "stage": str(self.current_stage),
        }
        self.decisions_made = decisions

    def get_context_summary(self) -> dict[str, Any]:
        """Get a summary of the session context"""
        return {
            "stage": str(self.current_stage),
            "progress": float(self.progress_percentage),
            "decisions": dict(self.decisions_made) if self.decisions_made else {},
            "pedagogy": self.pedagogy_preference,
            "unit_id": self.unit_id,
            "message_count": int(self.message_count),
        }

    def can_resume(self) -> bool:
        """Check if session can be resumed"""
        return str(self.status) in [
            SessionStatus.ACTIVE.value,
            SessionStatus.PAUSED.value,
        ]

    def mark_completed(self) -> None:
        """Mark session as completed"""
        self.status = SessionStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
