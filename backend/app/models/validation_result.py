"""
Validation result model for plugin validation tracking
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.content import Content


class ValidationStatus(str, Enum):
    """Validation status enumeration"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class ValidationResult(Base):
    """Validation result model for plugin validation tracking"""

    __tablename__ = "validation_results"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Content and plugin information
    content_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("contents.id"), nullable=False, index=True
    )
    plugin_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    plugin_version: Mapped[str | None] = mapped_column(String(20), default=None)

    # Validation results
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # ValidationStatus enum
    score: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Numerical scores (e.g., readability score)
    results: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Detailed validation results
    suggestions: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # Improvement suggestions

    # Error and diagnostic information
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    execution_time_ms: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Performance metrics

    # Timestamps
    validated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    content: Mapped[Content] = relationship(
        "Content", back_populates="validation_results"
    )

    def __repr__(self) -> str:
        return f"<ValidationResult(id={self.id}, plugin='{self.plugin_name}', status='{self.status}')>"

    @property
    def is_passed(self) -> bool:
        """Check if validation passed"""
        return str(self.status) == ValidationStatus.PASSED.value

    @property
    def is_failed(self) -> bool:
        """Check if validation failed"""
        return str(self.status) == ValidationStatus.FAILED.value

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return str(self.status) == ValidationStatus.WARNING.value

    @property
    def has_suggestions(self) -> bool:
        """Check if validation result has suggestions"""
        suggestions = self.suggestions
        return suggestions is not None and len(suggestions) > 0

    @property
    def suggestion_count(self) -> int:
        """Get number of suggestions"""
        suggestions = self.suggestions
        if not suggestions or not isinstance(suggestions, list):
            return 0
        return len(suggestions)
