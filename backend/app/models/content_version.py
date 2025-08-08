"""
Content versioning model for tracking content history
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class ContentVersion(Base):
    """Content version model for tracking content history"""

    __tablename__ = "content_versions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Version information
    content_id = Column(GUID(), ForeignKey("contents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, index=True)

    # Content snapshot
    content_markdown = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    title = Column(String(500), nullable=False)

    # Change tracking
    change_description = Column(Text, nullable=True)
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    content = relationship("Content", back_populates="versions")
    created_by = relationship("User")

    def __repr__(self):
        return f"<ContentVersion(id={self.id}, content_id={self.content_id}, version={self.version_number})>"
