"""
Supporting learning outcome models for materials and assessments
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class LocalLearningOutcome(Base):
    """Material-specific learning outcomes (LLOs)"""

    __tablename__ = "local_learning_outcomes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    material_id = Column(
        GUID(),
        ForeignKey("weekly_materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    material = relationship("WeeklyMaterial", back_populates="local_outcomes")

    def __repr__(self):
        return f"<LocalLearningOutcome(id={self.id}, material_id={self.material_id})>"


class WeeklyLearningOutcome(Base):
    """Weekly learning outcomes (WLOs)"""

    __tablename__ = "weekly_learning_outcomes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    unit_id = Column(
        GUID(), ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_number = Column(Integer, nullable=False, index=True)
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    unit = relationship("Unit", backref="weekly_outcomes")

    # Many-to-many with ULOs through mapping table
    unit_outcomes = relationship(
        "UnitLearningOutcome", secondary="wlo_ulo_mappings", backref="weekly_outcomes"
    )

    def __repr__(self):
        return f"<WeeklyLearningOutcome(id={self.id}, week={self.week_number})>"


class AssessmentLearningOutcome(Base):
    """Assessment-specific learning outcomes (ALOs)"""

    __tablename__ = "assessment_learning_outcomes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    assessment_id = Column(
        GUID(),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    assessment = relationship("Assessment", back_populates="assessment_outcomes")

    def __repr__(self):
        return f"<AssessmentLearningOutcome(id={self.id}, assessment_id={self.assessment_id})>"
