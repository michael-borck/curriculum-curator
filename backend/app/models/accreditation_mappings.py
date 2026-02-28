"""
Accreditation mapping models for Graduate Capabilities, Assurance of Learning (AoL),
and UN Sustainable Development Goals (SDGs)

Graduate Capabilities: Curtin University's 6 graduate attributes mapped to ULOs
AoL Competencies: AACSB's 7 program-level competency areas mapped to Units with I/R/M levels
SDGs: UN's 17 Sustainable Development Goals mapped to Units
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.unit import Unit


class GraduateCapabilityCode(str, Enum):
    """Curtin University Graduate Capability codes"""

    GC1 = "GC1"  # Apply knowledge, skills and capabilities
    GC2 = "GC2"  # Innovative, creative and/or entrepreneurial
    GC3 = "GC3"  # Effective communicators with digital competence
    GC4 = "GC4"  # Globally engaged and responsive
    GC5 = "GC5"  # Culturally competent (First Peoples & diverse cultures)
    GC6 = "GC6"  # Industry-connected and career-capable


class AoLCompetencyCode(str, Enum):
    """AACSB Assurance of Learning competency codes"""

    AOL1 = "AOL1"  # Knowledge of Business and Discipline Content
    AOL2 = "AOL2"  # Critical Thinking and Problem-Solving
    AOL3 = "AOL3"  # Communication Skills
    AOL4 = "AOL4"  # Ethical and Social Responsibility
    AOL5 = "AOL5"  # Teamwork and Interpersonal Skills
    AOL6 = "AOL6"  # Global and Cultural Awareness
    AOL7 = "AOL7"  # Quantitative and Technological Skills


class AoLLevel(str, Enum):
    """Assurance of Learning progression levels"""

    INTRODUCE = "I"  # First exposure, basic understanding
    REINFORCE = "R"  # Practice and deepen skills
    MASTER = "M"  # Demonstrate proficiency at graduation level


class SDGCode(str, Enum):
    """UN Sustainable Development Goals codes (SDG1-SDG17)"""

    SDG1 = "SDG1"  # No Poverty
    SDG2 = "SDG2"  # Zero Hunger
    SDG3 = "SDG3"  # Good Health and Well-being
    SDG4 = "SDG4"  # Quality Education
    SDG5 = "SDG5"  # Gender Equality
    SDG6 = "SDG6"  # Clean Water and Sanitation
    SDG7 = "SDG7"  # Affordable and Clean Energy
    SDG8 = "SDG8"  # Decent Work and Economic Growth
    SDG9 = "SDG9"  # Industry, Innovation and Infrastructure
    SDG10 = "SDG10"  # Reduced Inequalities
    SDG11 = "SDG11"  # Sustainable Cities and Communities
    SDG12 = "SDG12"  # Responsible Consumption and Production
    SDG13 = "SDG13"  # Climate Action
    SDG14 = "SDG14"  # Life Below Water
    SDG15 = "SDG15"  # Life on Land
    SDG16 = "SDG16"  # Peace, Justice and Strong Institutions
    SDG17 = "SDG17"  # Partnerships for the Goals


class ULOGraduateCapabilityMapping(Base):
    """
    Maps Unit Learning Outcomes to Graduate Capabilities.
    A ULO can map to multiple Graduate Capabilities.
    """

    __tablename__ = "ulo_graduate_capability_mappings"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Foreign key to ULO
    ulo_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"),
        index=True,
    )

    # Graduate Capability code (GC1-GC6)
    capability_code: Mapped[str] = mapped_column(String(10), index=True)

    # Whether this was AI-suggested or manually set
    is_ai_suggested: Mapped[bool] = mapped_column(default=False)

    # Optional notes/justification for the mapping
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    ulo: Mapped["UnitLearningOutcome"] = relationship(
        back_populates="graduate_capability_mappings"
    )

    def __repr__(self) -> str:
        return f"<ULOGraduateCapabilityMapping(ulo_id={self.ulo_id}, capability={self.capability_code})>"


class UnitAoLMapping(Base):
    """
    Maps Units to AACSB Assurance of Learning competencies with I/R/M levels.
    This is a unit-level mapping (not ULO-level) showing how the unit
    contributes to program-level learning goals.
    """

    __tablename__ = "unit_aol_mappings"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Foreign key to Unit
    unit_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("units.id", ondelete="CASCADE"),
        index=True,
    )

    # AoL Competency code (AOL1-AOL7)
    competency_code: Mapped[str] = mapped_column(String(10), index=True)

    # Level: I (Introduce), R (Reinforce), M (Master)
    level: Mapped[str] = mapped_column(String(1))

    # Whether this was AI-suggested or manually set
    is_ai_suggested: Mapped[bool] = mapped_column(default=False)

    # Optional notes/justification for the mapping
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="aol_mappings")

    def __repr__(self) -> str:
        return f"<UnitAoLMapping(unit_id={self.unit_id}, competency={self.competency_code}, level={self.level})>"


class UnitSDGMapping(Base):
    """
    Maps Units to UN Sustainable Development Goals (SDGs).
    This is a unit-level mapping showing how the unit contributes
    to the Global Goals for sustainable development.
    """

    __tablename__ = "unit_sdg_mappings"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Foreign key to Unit
    unit_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("units.id", ondelete="CASCADE"),
        index=True,
    )

    # SDG code (SDG1-SDG17)
    sdg_code: Mapped[str] = mapped_column(String(10), index=True)

    # Whether this was AI-suggested or manually set
    is_ai_suggested: Mapped[bool] = mapped_column(default=False)

    # Optional notes/justification for the mapping
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="sdg_mappings")

    def __repr__(self) -> str:
        return f"<UnitSDGMapping(unit_id={self.unit_id}, sdg={self.sdg_code})>"
