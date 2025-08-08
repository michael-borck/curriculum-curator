"""
Course search result model for web research functionality
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class CourseSearchResult(Base):
    """Course search result model for web research functionality"""

    __tablename__ = "course_search_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Search information
    unit_id = Column(GUID(), ForeignKey("units.id"), nullable=False, index=True)
    search_query = Column(String(500), nullable=False, index=True)
    search_type = Column(
        String(50), default="web", nullable=False
    )  # web, academic, institutional

    # Search results data
    results = Column(JSON, nullable=True)  # Raw search results
    processed_results = Column(JSON, nullable=True)  # Cleaned/processed results
    summary = Column(Text, nullable=True)  # AI-generated summary
    key_findings = Column(JSON, nullable=True)  # Extracted key information

    # Source tracking
    source_urls = Column(JSON, nullable=True)  # List of source URLs
    source_count = Column(JSON, nullable=True)  # Number of sources per category

    # Usage tracking
    is_used_for_generation = Column(Boolean, default=False, nullable=False)
    generation_context = Column(Text, nullable=True)  # How it was used

    # Quality and relevance
    relevance_score = Column(JSON, nullable=True)  # AI-assessed relevance
    quality_metrics = Column(JSON, nullable=True)  # Source quality indicators

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)

    # Relationships
    unit = relationship("Unit", back_populates="search_results")

    def __repr__(self):
        return f"<CourseSearchResult(id={self.id}, query='{self.search_query}', unit_id={self.unit_id})>"

    @property
    def has_results(self) -> bool:
        """Check if search returned results"""
        results = self.results  # type: ignore[assignment]
        return results is not None and len(results) > 0  # type: ignore[arg-type]

    @property
    def has_summary(self) -> bool:
        """Check if search has generated summary"""
        summary = self.summary  # type: ignore[assignment]
        return summary is not None and len(summary.strip()) > 0  # type: ignore[union-attr]

    @property
    def result_count(self) -> int:
        """Get number of search results"""
        if not self.results or not isinstance(self.results, list):
            return 0
        return len(self.results)

    @property
    def source_count_total(self) -> int:
        """Get total number of unique sources"""
        if not self.source_urls or not isinstance(self.source_urls, list):
            return 0
        return len(set(self.source_urls))  # Remove duplicates
