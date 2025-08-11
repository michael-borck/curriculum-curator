"""
Conversation history model for LLM interactions
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class Conversation(Base):
    """Conversation history for course creation sessions"""

    __tablename__ = "conversations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(GUID(), ForeignKey("courses.id"), nullable=False, index=True)
    lrd_id = Column(GUID(), ForeignKey("lrds.id"), nullable=True, index=True)

    # Session information
    session_id = Column(
        GUID(), nullable=False, index=True
    )  # Group related conversations

    # Conversation content
    messages = Column(JSON, nullable=False)  # Array of message objects

    # Context references
    task_references = Column(JSON, nullable=True)  # Referenced task IDs
    material_references = Column(JSON, nullable=True)  # Referenced material IDs

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="conversations")
    lrd = relationship("LRD")

    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id={self.session_id})>"
