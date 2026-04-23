"""CLO Set models — user-scoped Course Learning Outcome library."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.unit import Unit
    from app.models.user import User


class CLOSet(Base):
    """A named collection of Course Learning Outcomes belonging to one user."""

    __tablename__ = "clo_sets"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    program_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="clo_sets")
    items: Mapped[list["CLOItem"]] = relationship(
        back_populates="clo_set",
        cascade="all, delete-orphan",
        order_by="CLOItem.order_index",
    )
    unit_assignments: Mapped[list["UnitCLOSetAssignment"]] = relationship(
        back_populates="clo_set", cascade="all, delete-orphan"
    )


class CLOItem(Base):
    """A single CLO within a CLOSet (e.g. CLO1: 'Apply ethical frameworks...')."""

    __tablename__ = "clo_items"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    clo_set_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("clo_sets.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    clo_set: Mapped["CLOSet"] = relationship(back_populates="items")
    ulo_mappings: Mapped[list["ULOCLOItemMapping"]] = relationship(
        back_populates="clo_item", cascade="all, delete-orphan"
    )


class UnitCLOSetAssignment(Base):
    """Links a unit to a CLO set (many-to-many via explicit table)."""

    __tablename__ = "unit_clo_set_assignments"
    __table_args__ = (UniqueConstraint("unit_id", "clo_set_id"),)

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id", ondelete="CASCADE"), index=True
    )
    clo_set_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("clo_sets.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    unit: Mapped["Unit"] = relationship(back_populates="clo_set_assignments")
    clo_set: Mapped["CLOSet"] = relationship(back_populates="unit_assignments")


class ULOCLOItemMapping(Base):
    """Maps a ULO to a CLO item (AI-suggested or manually set)."""

    __tablename__ = "ulo_clo_item_mappings"
    __table_args__ = (UniqueConstraint("ulo_id", "clo_item_id"),)

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    ulo_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"),
        index=True,
    )
    clo_item_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("clo_items.id", ondelete="CASCADE"), index=True
    )
    is_ai_suggested: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    ulo: Mapped["UnitLearningOutcome"] = relationship(
        back_populates="clo_item_mappings"
    )
    clo_item: Mapped["CLOItem"] = relationship(back_populates="ulo_mappings")
