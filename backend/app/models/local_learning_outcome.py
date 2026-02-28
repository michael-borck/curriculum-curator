"""
Local Learning Outcome model for material-specific learning outcomes.

These are outcomes specific to individual materials, as opposed to
Unit Learning Outcomes (ULOs) which span the entire unit.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.weekly_material import WeeklyMaterial


class LocalLearningOutcome(Base):
    """Material-specific learning outcomes"""

    __tablename__ = "local_learning_outcomes"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    material_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("weekly_materials.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    material: Mapped[WeeklyMaterial] = relationship(back_populates="local_outcomes")

    def __repr__(self) -> str:
        return f"<LocalLearningOutcome(id={self.id}, description='{self.description[:50]}...')>"
