"""
Analytics Snapshot model for persisting quality/UDL scores over time
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.common import GUID


class AnalyticsSnapshot(Base):
    """Point-in-time capture of quality and UDL scores for a unit"""

    __tablename__ = "analytics_snapshots"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Parent unit
    unit_id: Mapped[str] = mapped_column(GUID(), ForeignKey("units.id"), index=True)

    # Snapshot metadata
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)

    # Quality scores
    quality_overall: Mapped[float] = mapped_column(Float, default=0.0)
    quality_star_rating: Mapped[float] = mapped_column(Float, default=0.0)
    quality_grade: Mapped[str] = mapped_column(String(2), default="F")
    quality_sub_scores: Mapped[str] = mapped_column(Text, default="{}")

    # UDL scores
    udl_overall: Mapped[float] = mapped_column(Float, default=0.0)
    udl_star_rating: Mapped[float] = mapped_column(Float, default=0.0)
    udl_grade: Mapped[str] = mapped_column(String(2), default="F")
    udl_sub_scores: Mapped[str] = mapped_column(Text, default="{}")

    # Summary stats for context
    material_count: Mapped[int] = mapped_column(Integer, default=0)
    assessment_count: Mapped[int] = mapped_column(Integer, default=0)
    ulo_count: Mapped[int] = mapped_column(Integer, default=0)
    weeks_with_content: Mapped[int] = mapped_column(Integer, default=0)

    # Who created it
    created_by_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    def __repr__(self) -> str:
        label_str = f"'{self.label}'" if self.label else "auto"
        return f"<AnalyticsSnapshot(id={self.id}, unit={self.unit_id}, {label_str})>"
