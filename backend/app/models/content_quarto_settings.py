"""
Content Quarto settings model for storing both simple and advanced settings
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class ContentQuartoSettings(Base):
    """Stores Quarto settings for each content item"""

    __tablename__ = "content_quarto_settings"

    content_id = Column(GUID(), ForeignKey("contents.id"), primary_key=True, index=True)

    # Simple mode settings stored as JSON
    simple_settings = Column(JSON, default={})

    # Advanced mode YAML
    advanced_yaml = Column(Text, nullable=True)

    # Which mode is currently active
    active_mode = Column(String(20), default="simple")  # 'simple' or 'advanced'

    # Currently selected preset name (for advanced mode)
    active_preset = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content = relationship("Content", back_populates="quarto_settings")

    def __repr__(self):
        return f"<ContentQuartoSettings(content_id={self.content_id}, mode={self.active_mode})>"
