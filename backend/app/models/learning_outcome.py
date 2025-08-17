"""
Learning outcome models for structured curriculum alignment
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


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


# Association table for content-outcome relationships
# This must be defined before the models that reference it
content_outcomes = Table(
    "content_outcomes",
    Base.metadata,
    Column("content_id", GUID(), ForeignKey("contents.id", ondelete="CASCADE")),
    Column(
        "outcome_id", GUID(), ForeignKey("unit_learning_outcomes.id", ondelete="CASCADE")
    ),
)


class UnitLearningOutcome(Base):
    """Learning outcome model for courses and units"""

    __tablename__ = "unit_learning_outcomes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Links
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=True, index=True)
    course_outline_id = Column(
        GUID(), ForeignKey("course_outlines.id"), nullable=True, index=True
    )
    weekly_topic_id = Column(
        GUID(), ForeignKey("weekly_topics.id"), nullable=True, index=True
    )

    # Outcome details
    outcome_type = Column(String(10), nullable=False, index=True)  # CLO, ULO, WLO
    outcome_code = Column(String(20), nullable=True)  # e.g., "CLO1", "ULO2.3"
    outcome_text = Column(Text, nullable=False)

    # Bloom's taxonomy
    bloom_level = Column(String(20), nullable=False)
    cognitive_processes = Column(Text, nullable=True)  # Specific verbs used

    # Sequencing and hierarchy
    sequence_order = Column(Integer, default=0, nullable=False)
    parent_outcome_id = Column(
        GUID(), ForeignKey("unit_learning_outcomes.id"), nullable=True
    )

    # Alignment and mapping
    graduate_attribute_ids = Column(Text, nullable=True)  # Comma-separated IDs
    assessment_methods = Column(Text, nullable=True)  # How it's assessed

    # Measurability
    is_measurable = Column(Boolean, default=True, nullable=False)
    success_criteria = Column(Text, nullable=True)

    # Metadata
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    unit = relationship("Unit", back_populates="learning_outcomes")
    course_outline = relationship("CourseOutline", back_populates="learning_outcomes")
    weekly_topic = relationship("WeeklyTopic", back_populates="learning_outcomes")
    created_by = relationship("User", foreign_keys=[created_by_id])

    # Self-referential relationship for hierarchy
    parent_outcome = relationship(
        "UnitLearningOutcome",
        remote_side=[id],
        backref="child_outcomes",
    )

    # Many-to-many with content
    contents = relationship(
        "Content", secondary=content_outcomes, back_populates="learning_outcomes"
    )

    def __repr__(self):
        return f"<UnitLearningOutcome(id={self.id}, type='{self.outcome_type}', code='{self.outcome_code}', bloom='{self.bloom_level}')>"

    @property
    def full_code(self) -> str:
        """Get full outcome code with type"""
        return f"{self.outcome_code or self.outcome_type.upper()}"

    @property
    def bloom_level_numeric(self) -> int:
        """Get numeric Bloom's level for sorting"""
        levels = {
            BloomLevel.REMEMBER: 1,
            BloomLevel.UNDERSTAND: 2,
            BloomLevel.APPLY: 3,
            BloomLevel.ANALYZE: 4,
            BloomLevel.EVALUATE: 5,
            BloomLevel.CREATE: 6,
        }
        return levels.get(self.bloom_level, 0)

    def is_aligned_with_content(self) -> bool:
        """Check if outcome has aligned content"""
        return bool(self.contents)

    def get_coverage_percentage(self, total_content_items: int) -> float:
        """Calculate coverage percentage of this outcome"""
        if total_content_items == 0:
            return 0.0
        return (len(self.contents) / total_content_items) * 100

    @classmethod
    def create_from_text(cls, text: str, outcome_type: str = OutcomeType.ULO):
        """Create outcome from text with automatic Bloom's level detection"""
        # Common Bloom's taxonomy verbs
        bloom_verbs = {
            BloomLevel.REMEMBER: ["identify", "list", "name", "recall", "recognize", "state"],
            BloomLevel.UNDERSTAND: ["describe", "explain", "summarize", "classify", "discuss"],
            BloomLevel.APPLY: ["apply", "demonstrate", "implement", "solve", "use", "execute"],
            BloomLevel.ANALYZE: ["analyze", "compare", "contrast", "examine", "investigate"],
            BloomLevel.EVALUATE: ["evaluate", "assess", "critique", "judge", "justify", "defend"],
            BloomLevel.CREATE: ["create", "design", "develop", "construct", "produce", "formulate"],
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
            bloom_level=detected_level,
        )
