"""
Unit Learning Outcome model with Bloom's taxonomy support
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class BloomLevel(str, Enum):
    """Bloom's taxonomy levels (revised taxonomy)"""

    REMEMBER = "remember"  # Level 1 - Recall facts and basic concepts
    UNDERSTAND = "understand"  # Level 2 - Explain ideas or concepts
    APPLY = "apply"  # Level 3 - Use information in new situations
    ANALYZE = "analyze"  # Level 4 - Draw connections among ideas
    EVALUATE = "evaluate"  # Level 5 - Justify a stand or decision
    CREATE = "create"  # Level 6 - Produce new or original work


class UnitLearningOutcome(Base):
    """Unit Learning Outcome model with Bloom's taxonomy validation"""

    __tablename__ = "unit_learning_outcomes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Basic outcome information
    content = Column(Text, nullable=False)  # The learning outcome text (markdown)
    bloom_level = Column(String(20), nullable=False, index=True)  # BloomLevel enum
    order_index = Column(Integer, default=0, nullable=False)  # Order within unit

    # Generation and validation
    is_auto_generated = Column(Boolean, default=False, nullable=False)
    validation_status = Column(
        String(20), default="pending", nullable=False
    )  # pending/valid/needs_review
    validation_notes = Column(Text, nullable=True)

    # Relationships
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    unit = relationship("Unit", back_populates="learning_outcomes")

    def __repr__(self):
        return f"<UnitLearningOutcome(id={self.id}, bloom_level='{self.bloom_level}', content='{self.content[:50]}...')>"

    @property
    def bloom_level_number(self) -> int:
        """Get numeric representation of Bloom's level"""
        level_map = {
            BloomLevel.REMEMBER.value: 1,
            BloomLevel.UNDERSTAND.value: 2,
            BloomLevel.APPLY.value: 3,
            BloomLevel.ANALYZE.value: 4,
            BloomLevel.EVALUATE.value: 5,
            BloomLevel.CREATE.value: 6,
        }
        return level_map.get(self.bloom_level, 0)

    @property
    def bloom_level_description(self) -> str:
        """Get descriptive text for Bloom's level"""
        descriptions = {
            BloomLevel.REMEMBER.value: "Recall facts and basic concepts",
            BloomLevel.UNDERSTAND.value: "Explain ideas or concepts",
            BloomLevel.APPLY.value: "Use information in new situations",
            BloomLevel.ANALYZE.value: "Draw connections among ideas",
            BloomLevel.EVALUATE.value: "Justify a stand or decision",
            BloomLevel.CREATE.value: "Produce new or original work",
        }
        return descriptions.get(self.bloom_level, "Unknown level")

    @property
    def is_higher_order(self) -> bool:
        """Check if this is a higher-order thinking skill (Analyze, Evaluate, Create)"""
        higher_order = [
            BloomLevel.ANALYZE.value,
            BloomLevel.EVALUATE.value,
            BloomLevel.CREATE.value,
        ]
        return self.bloom_level in higher_order

    @property
    def needs_validation(self) -> bool:
        """Check if outcome needs validation review"""
        return self.validation_status in ["pending", "needs_review"]

    @classmethod
    def get_bloom_level_order(cls) -> list:
        """Get Bloom's levels in ascending order of complexity"""
        return [
            BloomLevel.REMEMBER.value,
            BloomLevel.UNDERSTAND.value,
            BloomLevel.APPLY.value,
            BloomLevel.ANALYZE.value,
            BloomLevel.EVALUATE.value,
            BloomLevel.CREATE.value,
        ]

    @classmethod
    def get_recommended_verbs(cls, bloom_level: str) -> list:
        """Get recommended action verbs for each Bloom's level"""
        verb_map = {
            BloomLevel.REMEMBER.value: [
                "define",
                "list",
                "recall",
                "recognize",
                "state",
                "identify",
                "name",
                "match",
                "select",
            ],
            BloomLevel.UNDERSTAND.value: [
                "explain",
                "describe",
                "summarize",
                "interpret",
                "classify",
                "compare",
                "contrast",
                "discuss",
            ],
            BloomLevel.APPLY.value: [
                "apply",
                "demonstrate",
                "use",
                "implement",
                "solve",
                "execute",
                "operate",
                "practice",
            ],
            BloomLevel.ANALYZE.value: [
                "analyze",
                "examine",
                "compare",
                "differentiate",
                "organize",
                "deconstruct",
                "investigate",
            ],
            BloomLevel.EVALUATE.value: [
                "evaluate",
                "assess",
                "judge",
                "critique",
                "defend",
                "justify",
                "argue",
                "validate",
            ],
            BloomLevel.CREATE.value: [
                "create",
                "design",
                "develop",
                "compose",
                "construct",
                "produce",
                "generate",
                "synthesize",
            ],
        }
        return verb_map.get(bloom_level, [])
