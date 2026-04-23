"""UDL Audit response model — per-unit, per-profile, per-checkpoint self-assessment."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.unit import Unit


class UDLAuditResponse(Base):
    """One self-assessment response for a single UDL checkpoint within a unit audit.

    assessment_id = "" means the response is unit-level (from the Quality tab panel).
    assessment_id = <uuid> means the response is scoped to a specific assessment.
    """

    __tablename__ = "udl_audit_responses"
    __table_args__ = (
        UniqueConstraint("unit_id", "profile_id", "checkpoint_id", "assessment_id"),
    )

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    unit_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("units.id", ondelete="CASCADE"), index=True
    )
    profile_id: Mapped[str] = mapped_column(String(100), index=True)
    checkpoint_id: Mapped[str] = mapped_column(String(10))
    # "" = unit-level scope; assessment UUID = assessment-scoped
    assessment_id: Mapped[str] = mapped_column(String(36), default="")
    # "doing_well" | "needs_work" | "not_applicable" | "skipped"
    response: Mapped[str] = mapped_column(String(20), default="skipped")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    unit: Mapped["Unit"] = relationship(back_populates="udl_audit_responses")
