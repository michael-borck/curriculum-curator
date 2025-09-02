"""
Quarto preset model for storing user's YAML templates
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.common import GUID


class QuartoPreset(Base):
    """User's saved Quarto YAML presets"""

    __tablename__ = "quarto_presets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    yaml_content = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="quarto_presets")

    def __repr__(self):
        return f"<QuartoPreset(id={self.id}, user_id={self.user_id}, name={self.name})>"
