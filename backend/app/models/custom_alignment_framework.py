"""
Custom Alignment Framework models for mapping ULOs to user-defined frameworks.

Frameworks are fully custom per unit — lecturers can create N frameworks
(e.g. PLOs, GRIT Mindset, Professional Ethics, Indigenous Perspectives).
Each framework has items, and ULOs are mapped to individual items.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.unit import Unit


class CustomAlignmentFramework(Base):
    """
    A user-defined alignment framework for a specific unit.
    Examples: PLOs, GRIT Mindset, Professional Ethics, etc.
    """

    __tablename__ = "custom_alignment_frameworks"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Foreign key to Unit
    unit_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("units.id", ondelete="CASCADE"),
        index=True,
    )

    # Framework metadata
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional preset type for identification (plo, grit, ethics, indigenous, vision)
    preset_type: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # UI hints
    icon_hint: Mapped[str | None] = mapped_column(String(10), nullable=True)
    color_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Ordering
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="custom_frameworks")
    items: Mapped[list["FrameworkItem"]] = relationship(
        back_populates="framework", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CustomAlignmentFramework(id={self.id}, name='{self.name}', unit_id={self.unit_id})>"


class FrameworkItem(Base):
    """
    An individual item within a framework (e.g. PLO1, G=Global, etc.).
    """

    __tablename__ = "framework_items"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Foreign key to framework
    framework_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("custom_alignment_frameworks.id", ondelete="CASCADE"),
        index=True,
    )

    # Item details
    code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)

    # Whether this was AI-suggested
    is_ai_suggested: Mapped[bool] = mapped_column(default=False)

    # Optional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Ordering
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    framework: Mapped["CustomAlignmentFramework"] = relationship(back_populates="items")
    ulo_mappings: Mapped[list["ULOFrameworkItemMapping"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FrameworkItem(id={self.id}, code='{self.code}', framework_id={self.framework_id})>"


class ULOFrameworkItemMapping(Base):
    """
    Maps Unit Learning Outcomes to Framework Items.
    A ULO can map to multiple items across multiple frameworks.
    """

    __tablename__ = "ulo_framework_item_mappings"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Foreign key to ULO
    ulo_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"),
        index=True,
    )

    # Foreign key to framework item
    item_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("framework_items.id", ondelete="CASCADE"),
        index=True,
    )

    # Whether this was AI-suggested
    is_ai_suggested: Mapped[bool] = mapped_column(default=False)

    # Optional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    ulo: Mapped["UnitLearningOutcome"] = relationship(
        back_populates="framework_item_mappings"
    )
    item: Mapped["FrameworkItem"] = relationship(back_populates="ulo_mappings")

    def __repr__(self) -> str:
        return (
            f"<ULOFrameworkItemMapping(ulo_id={self.ulo_id}, item_id={self.item_id})>"
        )
