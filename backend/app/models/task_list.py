"""
Task list model for LRD implementation tracking
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class TaskStatus(str, Enum):
    """Task list status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class TaskList(Base):
    """Task list generated from LRD"""

    __tablename__ = "task_lists"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    lrd_id = Column(GUID(), ForeignKey("lrds.id"), nullable=True, index=True)
    course_id = Column(GUID(), ForeignKey("courses.id"), nullable=False, index=True)

    # Task list content
    tasks = Column(JSON, nullable=False)  # Structured task data
    status = Column(String(20), default=TaskStatus.PENDING.value, nullable=False)

    # Progress tracking
    total_tasks = Column(Integer, default=0, nullable=False)
    completed_tasks = Column(Integer, default=0, nullable=False)
    progress = Column(JSON, nullable=True)  # Detailed progress information

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    course = relationship("Course", back_populates="task_lists")
    lrd = relationship("LRD", back_populates="task_lists")

    def __repr__(self):
        return f"<TaskList(id={self.id}, status='{self.status}', progress={self.completed_tasks}/{self.total_tasks})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate task completion percentage"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
