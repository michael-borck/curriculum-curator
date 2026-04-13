"""
Research schemas for academic search, URL extraction, and outline synthesis.
"""

from pydantic import Field

from app.schemas.ai import ScaffoldUnitResponse
from app.schemas.base import CamelModel

# =============================================================================
# Phase 1: Academic Search
# =============================================================================


class AcademicSearchRequest(CamelModel):
    """Request to search academic databases."""

    query: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(default=20, ge=1, le=100)
    academic_only: bool = Field(default=True)
    preferred_tier: int | None = Field(
        default=None, description="Preferred search tier (1-4)"
    )
    unit_id: str | None = Field(
        default=None, description="Unit ID for context-aware search"
    )


class AcademicSearchResultItem(CamelModel):
    """A single academic search result."""

    title: str
    url: str
    doi: str | None = None
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    publication_year: int | None = None
    source_name: str | None = None
    citation_count: int | None = None
    academic_score: float = Field(default=0.0, ge=0.0, le=1.0)
    provider: str = ""


class AcademicSearchResponse(CamelModel):
    """Response from academic search."""

    query: str
    results: list[AcademicSearchResultItem] = Field(default_factory=list)
    total_results: int = 0
    tier_used: int = 1
    tier_name: str = "Academic"


class TierInfo(CamelModel):
    """Information about a search tier."""

    tier: int
    name: str
    available: bool
    reason: str | None = None


class AvailableTiersResponse(CamelModel):
    """List of available search tiers."""

    tiers: list[TierInfo] = Field(default_factory=list)


# =============================================================================
# Phase 2: URL Extraction
# =============================================================================


class UrlExtractRequest(CamelModel):
    """Request to extract content from URLs."""

    urls: list[str] = Field(..., min_length=1, max_length=20)
    summarize: bool = Field(default=True)
    purpose: str = Field(default="general")


class ExtractedUrlItem(CamelModel):
    """Extracted content from a single URL."""

    url: str
    title: str | None = None
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    academic_score: float = Field(default=0.0, ge=0.0, le=1.0)
    content_type: str = "unknown"
    error: str | None = None


class UrlExtractResponse(CamelModel):
    """Response from URL extraction."""

    results: list[ExtractedUrlItem] = Field(default_factory=list)
    total: int = 0
    successful: int = 0
    failed: int = 0


# =============================================================================
# Phase 3: Outline Synthesis (Propose/Apply)
# =============================================================================


class SourceInput(CamelModel):
    """Lightweight source data for synthesis prompts."""

    title: str
    url: str
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)


class ScaffoldFromSourcesRequest(CamelModel):
    """Request to scaffold a unit from research sources."""

    source_data: list[SourceInput] = Field(..., min_length=1)
    unit_title: str = Field(..., min_length=1, max_length=500)
    unit_description: str = Field(default="", max_length=5000)
    duration_weeks: int = Field(default=12, ge=1, le=52)
    pedagogy_style: str = Field(default="mixed_approach")
    unit_id: str | None = Field(
        default=None, description="Unit ID for Learning Design lookup"
    )
    design_id: str | None = Field(
        default=None, description="Specific Learning Design ID"
    )


class CompareRequest(CamelModel):
    """Request to compare sources against an existing unit."""

    source_data: list[SourceInput] = Field(..., min_length=1)
    unit_id: str = Field(..., description="Unit to compare against")


class ComparisonWeek(CamelModel):
    """Coverage analysis for a single week."""

    week_number: int
    topic: str
    coverage: str = Field(
        ..., description="well_covered | partially_covered | not_covered"
    )
    matching_sources: list[str] = Field(
        default_factory=list, description="Titles of matching sources"
    )


class ComparisonProposal(CamelModel):
    """AI-generated comparison of sources vs existing unit."""

    unit_id: str
    weeks: list[ComparisonWeek] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    overlaps: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class MatchReadingListRequest(CamelModel):
    """Request to match sources to unit weeks."""

    source_data: list[SourceInput] = Field(..., min_length=1)
    unit_id: str = Field(..., description="Unit to match resources to")


class UnitWeekInfo(CamelModel):
    """Minimal week info for the reading list UI."""

    week_number: int
    topic: str


class ResourceMatch(CamelModel):
    """AI-suggested mapping of a source to a week."""

    url: str
    title: str
    suggested_week: int | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    assigned_week: int | None = Field(
        default=None, description="User-corrected week assignment"
    )
    skipped: bool = Field(default=False, description="User chose to skip this resource")


class ReadingListProposal(CamelModel):
    """AI-generated reading list mapping."""

    unit_id: str
    unit_weeks: list[UnitWeekInfo] = Field(default_factory=list)
    matches: list[ResourceMatch] = Field(default_factory=list)
    unmatched_count: int = 0
    avg_confidence: float = 0.0


class ApplyScaffoldRequest(CamelModel):
    """Request to apply a scaffold proposal."""

    proposal: ScaffoldUnitResponse
    unit_id: str | None = Field(
        default=None, description="Existing unit to overwrite, or None to create new"
    )


class ApplyComparisonRequest(CamelModel):
    """Request to apply selected comparison suggestions."""

    proposal: ComparisonProposal
    selected_suggestions: list[str] = Field(
        default_factory=list, description="Suggestion texts to adopt"
    )


class ApplyReadingListRequest(CamelModel):
    """Request to apply a reading list proposal."""

    proposal: ReadingListProposal
    save_as_sources: bool = Field(
        default=True, description="Save matched resources as ResearchSource entries"
    )


# =============================================================================
# Phase 4: Research Settings
# =============================================================================


class SearchApiKeys(CamelModel):
    """User's search API keys."""

    google_cse_api_key: str | None = None
    google_cse_engine_id: str | None = None
    serper_api_key: str | None = None
    brave_search_api_key: str | None = None
    tavily_api_key: str | None = None
    core_api_key: str | None = None


class ResearchSettings(CamelModel):
    """User's research preferences."""

    preferred_tier: int = Field(default=1, ge=1, le=4)
    search_api_keys: SearchApiKeys = Field(default_factory=SearchApiKeys)
    searxng_url: str | None = None
    excluded_domains: list[str] = Field(
        default_factory=list,
        description="Domains to drop from every tier's results (e.g. youtube.com)",
    )
