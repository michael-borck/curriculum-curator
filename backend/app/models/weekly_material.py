"""
Weekly Material model for course content management
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID
from app.models.enums import SessionFormat

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.learning_outcome import UnitLearningOutcome
    from app.models.local_learning_outcome import LocalLearningOutcome
    from app.models.unit import Unit

# Re-export for backwards compatibility
__all__ = ["MaterialCategory", "MaterialStatus", "SessionFormat", "WeeklyMaterial"]


class MaterialCategory(str, Enum):
    """Content category within a week"""

    PRE_CLASS = "pre_class"
    IN_CLASS = "in_class"
    POST_CLASS = "post_class"
    RESOURCES = "resources"
    GENERAL = "general"


class MaterialStatus(str, Enum):
    """Material completion status"""

    DRAFT = "draft"
    COMPLETE = "complete"
    NEEDS_REVIEW = "needs_review"
    PUBLISHED = "published"


class WeeklyMaterial(Base):
    """Learning materials organized by week"""

    __tablename__ = "weekly_materials"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Parent relationships
    unit_id: Mapped[str] = mapped_column(GUID(), ForeignKey("units.id"), index=True)
    week_number: Mapped[int] = mapped_column(Integer, index=True)

    # Material details
    title: Mapped[str] = mapped_column(String(500))
    type: Mapped[str] = mapped_column(String(50), index=True)  # SessionFormat enum
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured content (ProseMirror JSON from TipTap editor)
    content_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Per-material export format override (e.g. "h5p_question_set", "qti")
    export_format: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Content and metadata
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    material_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    # Organization
    category: Mapped[str] = mapped_column(
        String(20), default=MaterialCategory.GENERAL.value
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(20), default=MaterialStatus.DRAFT.value, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="weekly_materials")

    # Local learning outcomes (material-specific)
    local_outcomes: Mapped[list["LocalLearningOutcome"]] = relationship(
        back_populates="material", cascade="all, delete-orphan"
    )

    # Many-to-many with ULOs through mapping table
    learning_outcomes: Mapped[list["UnitLearningOutcome"]] = relationship(
        secondary="material_ulo_mappings", backref="materials"
    )

    # Many-to-many with assessments through mapping table
    assessments: Mapped[list["Assessment"]] = relationship(
        secondary="assessment_material_links",
        back_populates="linked_materials",
    )

    def __repr__(self) -> str:
        return f"<WeeklyMaterial(id={self.id}, title='{self.title}', week={self.week_number}, type='{self.type}')>"

    @property
    def is_complete(self) -> bool:
        """Check if material is complete"""
        return str(self.status) in [
            MaterialStatus.COMPLETE.value,
            MaterialStatus.PUBLISHED.value,
        ]

    @property
    def estimated_hours(self) -> float:
        """Get estimated time in hours"""
        if self.duration_minutes:
            return self.duration_minutes / 60.0
        return 0.0

    @property
    def metadata_dict(self) -> dict[str, Any]:
        """Get metadata as dictionary"""
        return self.material_metadata or {}

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get specific metadata value"""
        if self.material_metadata:
            return self.material_metadata.get(key, default)
        return default
