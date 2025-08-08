"""
Validation result model for plugin validation tracking
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Content and plugin information
    content_id = Column(GUID(), ForeignKey("contents.id"), nullable=False, index=True)
    plugin_name = Column(String(100), nullable=False, index=True)
    plugin_version = Column(String(20), nullable=True)

    # Validation results
    status = Column(String(20), nullable=False, index=True)  # ValidationStatus enum
    score = Column(JSON, nullable=True)  # Numerical scores (e.g., readability score)
    results = Column(JSON, nullable=True)  # Detailed validation results
    suggestions = Column(JSON, nullable=True)  # Improvement suggestions

    # Error and diagnostic information
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(JSON, nullable=True)  # Performance metrics

    # Timestamps
    validated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    content = relationship("Content", back_populates="validation_results")

    def __repr__(self):
        return f"<ValidationResult(id={self.id}, plugin='{self.plugin_name}', status='{self.status}')>"

    @property
    def is_passed(self) -> bool:
        """Check if validation passed"""
        return self.status == ValidationStatus.PASSED.value

    @property
    def is_failed(self) -> bool:
        """Check if validation failed"""
        return self.status == ValidationStatus.FAILED.value

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return self.status == ValidationStatus.WARNING.value

    @property
    def has_suggestions(self) -> bool:
        """Check if validation result has suggestions"""
        suggestions = self.suggestions  # type: ignore[assignment]
        return suggestions is not None and len(suggestions) > 0  # type: ignore[arg-type]

    @property
    def suggestion_count(self) -> int:
        """Get number of suggestions"""
        if not self.suggestions or not isinstance(self.suggestions, list):
            return 0
        return len(self.suggestions)
