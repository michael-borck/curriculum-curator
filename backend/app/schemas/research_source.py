"""
Pydantic schemas for research sources and citations.
"""

from datetime import datetime

from pydantic import Field

from app.models.research_source import CitationStyle, SourceType
from app.schemas.base import CamelModel


class AuthorSchema(CamelModel):
    """Schema for author information."""

    first_name: str = Field(..., description="Author's first name(s)")
    last_name: str = Field(..., description="Author's last name")
    suffix: str | None = Field(None, description="Suffix like PhD, MD, etc.")


# ==================== Research Source Schemas ====================


class ResearchSourceBase(CamelModel):
    """Base schema for research source."""

    url: str = Field(..., description="URL of the source")
    title: str = Field(..., description="Title of the source")
    source_type: SourceType = Field(
        default=SourceType.WEBSITE, description="Type of source"
    )
    authors: list[AuthorSchema] = Field(
        default_factory=list, description="List of authors"
    )
    publication_date: str | None = Field(
        None, description="Publication date (ISO format or year)"
    )
    publisher: str | None = Field(None, description="Publisher name")
    journal_name: str | None = Field(None, description="Journal name for articles")
    volume: str | None = Field(None, description="Volume number")
    issue: str | None = Field(None, description="Issue number")
    pages: str | None = Field(None, description="Page range (e.g., '123-145')")
    doi: str | None = Field(None, description="Digital Object Identifier")
    isbn: str | None = Field(None, description="ISBN for books")
    summary: str | None = Field(None, description="Summary of the source content")
    key_points: list[str] = Field(
        default_factory=list, description="Key points extracted from source"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for organization")
    notes: str | None = Field(None, description="User notes about the source")
    access_date: str | None = Field(None, description="Date the URL was accessed")


class ResearchSourceCreate(ResearchSourceBase):
    """Schema for creating a new research source."""

    unit_id: str | None = Field(
        None, description="Optional unit to associate the source with"
    )
    is_favorite: bool = Field(default=False, description="Mark as favorite")


class ResearchSourceUpdate(CamelModel):
    """Schema for updating a research source."""

    title: str | None = None
    source_type: SourceType | None = None
    authors: list[AuthorSchema] | None = None
    publication_date: str | None = None
    publisher: str | None = None
    journal_name: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    isbn: str | None = None
    summary: str | None = None
    key_points: list[str] | None = None
    tags: list[str] | None = None
    notes: str | None = None
    is_favorite: bool | None = None
    unit_id: str | None = None


class ResearchSourceResponse(ResearchSourceBase):
    """Schema for research source response."""

    id: str
    user_id: str
    unit_id: str | None
    academic_score: float = Field(default=0.0, description="Academic credibility score")
    usage_count: int = Field(default=0, description="Number of times source was used")
    last_used_at: datetime | None = None
    is_favorite: bool = False
    created_at: datetime
    updated_at: datetime | None = None


class ResearchSourceList(CamelModel):
    """Schema for list of research sources with pagination."""

    sources: list[ResearchSourceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ==================== Citation Schemas ====================


class CitationRequest(CamelModel):
    """Request to format a citation."""

    source_id: str = Field(..., description="ID of the research source")
    style: CitationStyle = Field(
        default=CitationStyle.APA7, description="Citation style to use"
    )


class CitationResponse(CamelModel):
    """Response with formatted citation."""

    source_id: str
    style: CitationStyle
    full_citation: str = Field(..., description="Full reference citation")
    in_text_citation: str = Field(..., description="In-text citation")


class BulkCitationRequest(CamelModel):
    """Request to format multiple citations."""

    source_ids: list[str] = Field(..., description="List of source IDs")
    style: CitationStyle = Field(
        default=CitationStyle.APA7, description="Citation style to use"
    )


class ReferenceListResponse(CamelModel):
    """Response with formatted reference list."""

    style: CitationStyle
    reference_list: str = Field(..., description="Formatted reference list (markdown)")
    citations: list[CitationResponse]


# ==================== Search + Save Schemas ====================
# (ContentCitation schemas removed in pre-MVP cleanup along with the
# underlying model — see docs/code-audit-2026-04-11.md.)


class SaveFromSearchRequest(CamelModel):
    """Request to save a source from search results."""

    url: str = Field(..., description="URL of the source")
    title: str = Field(..., description="Title from search results")
    summary: str | None = Field(None, description="Summary from search/AI")
    key_points: list[str] = Field(
        default_factory=list, description="Key points from AI summarization"
    )
    academic_score: float = Field(default=0.0, description="Academic score from search")
    unit_id: str | None = Field(None, description="Optional unit to associate with")
    source_type: SourceType = Field(
        default=SourceType.WEBSITE, description="Type of source"
    )
    tags: list[str] = Field(default_factory=list, description="Initial tags")


# ==================== Synthesis Schemas ====================


class SynthesisRequest(CamelModel):
    """Request to synthesize content from multiple sources."""

    source_ids: list[str] = Field(
        ..., min_length=1, description="IDs of sources to synthesize"
    )
    purpose: str = Field(
        ...,
        description="Purpose of synthesis (e.g., 'lecture content', 'assessment task')",
    )
    topic: str = Field(..., description="Topic/focus for the synthesis")
    word_count: int = Field(
        default=500, ge=100, le=5000, description="Target word count"
    )
    include_citations: bool = Field(
        default=True, description="Include in-text citations"
    )
    citation_style: CitationStyle = Field(
        default=CitationStyle.APA7, description="Citation style for references"
    )


class SynthesisResponse(CamelModel):
    """Response with synthesized content."""

    content: str = Field(..., description="Synthesized content with citations")
    reference_list: str = Field(
        ..., description="Formatted reference list for sources used"
    )
    sources_used: list[str] = Field(
        ..., description="IDs of sources actually referenced"
    )
    word_count: int
