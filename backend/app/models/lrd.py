"""
Learning Requirements Document (LRD) model
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class LRDStatus(str, Enum):
    """LRD approval status"""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class LRD(Base):
    """Learning Requirements Document for course planning"""

    __tablename__ = "lrds"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(GUID(), ForeignKey("courses.id"), nullable=False, index=True)

    # LRD metadata
    version = Column(String(20), nullable=False, default="1.0")
    status = Column(String(20), default=LRDStatus.DRAFT.value, nullable=False)

    # LRD content (structured JSON)
    content = Column(JSON, nullable=False)  # Complete LRD content
    approval_history = Column(JSON, nullable=True)  # Approval tracking

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    course = relationship("Course", back_populates="lrds")
    task_lists = relationship(
        "TaskList", back_populates="lrd", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LRD(id={self.id}, version='{self.version}', status='{self.status}')>"
