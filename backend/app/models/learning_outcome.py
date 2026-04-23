"""
Learning outcome models for structured curriculum alignment
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Self

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.accreditation_mappings import ULOGraduateCapabilityMapping
    from app.models.assessment import Assessment
    from app.models.clo_set import ULOCLOItemMapping
    from app.models.custom_alignment_framework import ULOFrameworkItemMapping
    from app.models.unit import Unit
    from app.models.unit_outline import UnitOutline
    from app.models.user import User
    from app.models.weekly_topic import WeeklyTopic


class OutcomeType(str, Enum):
    """Learning outcome type enumeration"""

    CLO = "clo"  # Course Learning Outcome
    ULO = "ulo"  # Unit Learning Outcome
    WLO = "wlo"  # Weekly Learning Outcome


class BloomLevel(str, Enum):
    """Bloom's Taxonomy levels"""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


# The content_outcomes association table was removed in the pre-MVP
# cleanup along with the legacy Content model. Material-outcome mappings
# live on the material_ulo_mappings association table (see app.models.mappings).


class UnitLearningOutcome(Base):
    """Learning outcome model for courses and units"""

    __tablename__ = "unit_learning_outcomes"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Links
    unit_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=True, index=True
    )
    unit_outline_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("unit_outlines.id"), nullable=True, index=True
    )
    weekly_topic_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("weekly_topics.id"), nullable=True, index=True
    )

    # Outcome details
    outcome_type: Mapped[str] = mapped_column(String(10), index=True)  # CLO, ULO, WLO
    outcome_code: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # e.g., "CLO1", "ULO2.3"
    outcome_text: Mapped[str] = mapped_column(Text)

    # Bloom's taxonomy
    bloom_level: Mapped[str] = mapped_column(String(20))
    cognitive_processes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Specific verbs used

    # Sequencing and hierarchy
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    parent_outcome_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("unit_learning_outcomes.id"), nullable=True
    )

    # Alignment and mapping
    graduate_attribute_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Comma-separated IDs
    assessment_methods: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # How it's assessed

    # Measurability
    is_measurable: Mapped[bool] = mapped_column(default=True)
    success_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    created_by_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    unit: Mapped["Unit | None"] = relationship(back_populates="learning_outcomes")
    unit_outline: Mapped["UnitOutline | None"] = relationship(
        back_populates="learning_outcomes"
    )
    weekly_topic: Mapped["WeeklyTopic | None"] = relationship(
        back_populates="learning_outcomes"
    )
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])

    # Self-referential relationship for hierarchy
    parent_outcome: Mapped["UnitLearningOutcome | None"] = relationship(
        remote_side=[id],
        backref="child_outcomes",
    )

    # Graduate Capability mappings
    graduate_capability_mappings: Mapped[list["ULOGraduateCapabilityMapping"]] = (
        relationship(back_populates="ulo", cascade="all, delete-orphan")
    )

    # Custom framework item mappings
    framework_item_mappings: Mapped[list["ULOFrameworkItemMapping"]] = relationship(
        back_populates="ulo", cascade="all, delete-orphan"
    )
    clo_item_mappings: Mapped[list["ULOCLOItemMapping"]] = relationship(
        back_populates="ulo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UnitLearningOutcome(id={self.id}, type='{self.outcome_type}', code='{self.outcome_code}', bloom='{self.bloom_level}')>"

    @property
    def full_code(self) -> str:
        """Get full outcome code with type"""
        code = self.outcome_code or str(self.outcome_type).upper()
        return str(code)

    @property
    def bloom_level_numeric(self) -> int:
        """Get numeric Bloom's level for sorting"""
        levels = {
            BloomLevel.REMEMBER.value: 1,
            BloomLevel.UNDERSTAND.value: 2,
            BloomLevel.APPLY.value: 3,
            BloomLevel.ANALYZE.value: 4,
            BloomLevel.EVALUATE.value: 5,
            BloomLevel.CREATE.value: 6,
        }
        return levels.get(str(self.bloom_level), 0)

    def is_aligned_with_content(self) -> bool:
        """Check if outcome has aligned content"""
        return bool(self.contents)

    def get_coverage_percentage(self, total_content_items: int) -> float:
        """Calculate coverage percentage of this outcome"""
        if total_content_items == 0:
            return 0.0
        return (len(self.contents) / total_content_items) * 100

    @classmethod
    def create_from_text(
        cls, text: str, outcome_type: str = OutcomeType.ULO.value
    ) -> Self:
        """Create outcome from text with automatic Bloom's level detection"""
        # Common Bloom's taxonomy verbs
        bloom_verbs: dict[BloomLevel, list[str]] = {
            BloomLevel.REMEMBER: [
                "identify",
                "list",
                "name",
                "recall",
                "recognize",
                "state",
            ],
            BloomLevel.UNDERSTAND: [
                "describe",
                "explain",
                "summarize",
                "classify",
                "discuss",
            ],
            BloomLevel.APPLY: [
                "apply",
                "demonstrate",
                "implement",
                "solve",
                "use",
                "execute",
            ],
            BloomLevel.ANALYZE: [
                "analyze",
                "compare",
                "contrast",
                "examine",
                "investigate",
            ],
            BloomLevel.EVALUATE: [
                "evaluate",
                "assess",
                "critique",
                "judge",
                "justify",
                "defend",
            ],
            BloomLevel.CREATE: [
                "create",
                "design",
                "develop",
                "construct",
                "produce",
                "formulate",
            ],
        }

        # Detect Bloom's level from text
        text_lower = text.lower()
        detected_level = BloomLevel.UNDERSTAND  # Default

        for level, verbs in bloom_verbs.items():
            if any(verb in text_lower for verb in verbs):
                detected_level = level
                break

        return cls(
            outcome_text=text,
            outcome_type=outcome_type,
            bloom_level=detected_level.value,
        )


# Association table for Assessment-ULO mapping
assessment_ulo_mappings = Table(
    "assessment_ulo_mappings",
    Base.metadata,
    Column("assessment_id", GUID(), ForeignKey("assessments.id", ondelete="CASCADE")),
    Column(
        "ulo_id",
        GUID(),
        ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE"),
    ),
)


class AssessmentLearningOutcome(Base):
    """Assessment-specific learning outcomes (for detailed assessment criteria)"""

    __tablename__ = "assessment_learning_outcomes"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Links
    assessment_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("assessments.id"), nullable=False, index=True
    )

    # Outcome details
    description: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        back_populates="assessment_outcomes"
    )

    def __repr__(self) -> str:
        desc_preview = str(self.description)[:50] if self.description else ""
        return f"<AssessmentLearningOutcome(id={self.id}, assessment_id={self.assessment_id}, desc='{desc_preview}...')>"
