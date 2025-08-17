"""
Chat session model for conversational content creation workflow
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # User and unit association
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=True, index=True)
    unit_outline_id = Column(
        GUID(), ForeignKey("unit_outlines.id"), nullable=True, index=True
    )

    # Session details
    session_name = Column(String(500), nullable=True)
    session_type = Column(String(50), default="content_creation", nullable=False)
    status = Column(String(20), default=SessionStatus.ACTIVE.value, nullable=False)

    # Workflow tracking
    current_stage = Column(
        String(50), default=WorkflowStage.INITIAL.value, nullable=False
    )
    workflow_data = Column(JSON, nullable=True)  # Stage-specific data
    context_data = Column(JSON, nullable=True)  # Accumulated context

    # Conversation history
    messages = Column(JSON, nullable=True)  # Array of message objects
    message_count = Column(Integer, default=0, nullable=False)

    # Progress tracking
    progress_percentage = Column(Float, default=0.0, nullable=False)
    stages_completed = Column(JSON, nullable=True)  # List of completed stages

    # Decision tracking
    decisions_made = Column(JSON, nullable=True)  # Key decisions in workflow
    pending_questions = Column(JSON, nullable=True)  # Questions awaiting answers

    # Generated content tracking
    generated_content_ids = Column(JSON, nullable=True)  # IDs of created content
    generated_outline_id = Column(GUID(), nullable=True)  # Created course outline

    # AI interaction metadata
    total_tokens_used = Column(Integer, default=0, nullable=False)
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)

    # Session preferences
    pedagogy_preference = Column(String(50), nullable=True)
    complexity_level = Column(String(20), nullable=True)
    tone_preference = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Session duration tracking
    total_duration_minutes = Column(Integer, default=0, nullable=False)

    # Feedback and quality
    user_satisfaction_score = Column(Float, nullable=True)  # 1-5 rating
    feedback_notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    unit = relationship("Unit", back_populates="workflow_chat_sessions")
    unit_outline = relationship("UnitOutline")

    def __repr__(self):
        return f"<WorkflowChatSession(id={self.id}, user_id={self.user_id}, stage='{self.current_stage}', status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == SessionStatus.ACTIVE.value

    @property
    def is_completed(self) -> bool:
        """Check if session is completed"""
        return self.status == SessionStatus.COMPLETED.value

    @property
    def stage_index(self) -> int:
        """Get numeric index of current stage"""
        stages = list(WorkflowStage)
        try:
            return stages.index(WorkflowStage(self.current_stage))
        except (ValueError, KeyError):
            return 0

    @property
    def total_stages(self) -> int:
        """Get total number of workflow stages"""
        return len(WorkflowStage) - 1  # Exclude COMPLETED

    def add_message(self, role: str, content: str, metadata: dict | None = None):
        """Add a message to the conversation history"""
        if not self.messages:
            self.messages = []

        message = {
            "role": role,  # user, assistant, system
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        self.messages.append(message)
        self.message_count += 1
        self.last_activity_at = datetime.utcnow()

    def advance_stage(self):
        """Advance to the next workflow stage"""
        stages = list(WorkflowStage)
        current_index = self.stage_index

        if current_index < len(stages) - 1:
            self.current_stage = stages[current_index + 1].value
            self.update_progress()

            if not self.stages_completed:
                self.stages_completed = []
            self.stages_completed.append(stages[current_index].value)

    def update_progress(self):
        """Update progress percentage based on current stage"""
        self.progress_percentage = (self.stage_index / self.total_stages) * 100

    def add_decision(self, decision_key: str, decision_value: any):
        """Record a key decision made during the workflow"""
        if not self.decisions_made:
            self.decisions_made = {}

        decisions = dict(self.decisions_made or {})
        decisions[decision_key] = {
            "value": decision_value,
            "timestamp": datetime.utcnow().isoformat(),
            "stage": self.current_stage,
        }
        self.decisions_made = decisions
        self.decisions_made = decisions

    def get_context_summary(self) -> dict:
        """Get a summary of the session context"""
        return {
            "stage": self.current_stage,
            "progress": self.progress_percentage,
            "decisions": self.decisions_made or {},
            "pedagogy": self.pedagogy_preference,
            "unit_id": self.unit_id,
            "message_count": self.message_count,
        }

    def can_resume(self) -> bool:
        """Check if session can be resumed"""
        return self.status in [SessionStatus.ACTIVE.value, SessionStatus.PAUSED.value]

    def mark_completed(self):
        """Mark session as completed"""
        self.status = SessionStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
