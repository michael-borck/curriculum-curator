"""
Research Source model for storing and managing academic sources
"""

import json
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID


class SourceType(str, Enum):
    """Type of research source"""

    JOURNAL_ARTICLE = "journal_article"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    CONFERENCE_PAPER = "conference_paper"
    THESIS = "thesis"
    WEBSITE = "website"
    REPORT = "report"
    VIDEO = "video"
    PODCAST = "podcast"
    OTHER = "other"


class CitationStyle(str, Enum):
    """Citation formatting styles"""

    APA7 = "apa7"
    HARVARD = "harvard"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"
    VANCOUVER = "vancouver"


class ResearchSource(Base):
    """
    Model for storing research sources used in content creation.

    Supports various source types and citation styles.
    """

    __tablename__ = "research_sources"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Ownership
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=True, index=True
    )

    # Source identification
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), default=SourceType.WEBSITE.value
    )

    # Authors stored as JSON array of author objects with first_name, last_name, suffix
    authors_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Publication details
    publication_date: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # ISO date or "2024" or "2024-03"
    publisher: Mapped[str | None] = mapped_column(String(500), nullable=True)
    journal_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    volume: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issue: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pages: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "123-145" or "e12345"
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Content analysis
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array of strings
    academic_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Organization
    tags_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array of strings
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)

    # Access tracking
    access_date: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Date URL was accessed

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="research_sources")
    unit = relationship("Unit", back_populates="research_sources")

    def __repr__(self) -> str:
        return f"<ResearchSource {self.title[:50]}...>"

    @property
    def authors(self) -> list[dict[str, str]]:
        """Parse authors from JSON"""
        if not self.authors_json:
            return []
        try:
            return json.loads(self.authors_json)
        except json.JSONDecodeError:
            return []

    @authors.setter
    def authors(self, value: list[dict[str, str]]) -> None:
        """Set authors as JSON"""
        self.authors_json = json.dumps(value) if value else None

    @property
    def key_points(self) -> list[str]:
        """Parse key points from JSON"""
        if not self.key_points_json:
            return []
        try:
            return json.loads(self.key_points_json)
        except json.JSONDecodeError:
            return []

    @key_points.setter
    def key_points(self, value: list[str]) -> None:
        """Set key points as JSON"""
        self.key_points_json = json.dumps(value) if value else None

    @property
    def tags(self) -> list[str]:
        """Parse tags from JSON"""
        if not self.tags_json:
            return []
        try:
            return json.loads(self.tags_json)
        except json.JSONDecodeError:
            return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        """Set tags as JSON"""
        self.tags_json = json.dumps(value) if value else None


class ContentCitation(Base):
    """
    Links research sources to specific content items.

    Tracks where citations are used in generated content.
    """

    __tablename__ = "content_citations"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Foreign keys
    content_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("contents.id"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("research_sources.id"), nullable=False, index=True
    )

    # Citation details
    citation_style: Mapped[str] = mapped_column(
        String(20), default=CitationStyle.APA7.value
    )
    citation_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Formatted citation
    in_text_citation: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # e.g., "(Smith, 2024)"

    # Position in content (optional, for tracking citation location)
    position_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    content = relationship("Content", back_populates="citations")
    source = relationship("ResearchSource")

    def __repr__(self) -> str:
        return f"<ContentCitation {self.in_text_citation}>"
