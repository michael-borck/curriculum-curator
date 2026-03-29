"""
Pydantic schemas for browser capture and CrossRef DOI lookup.
"""

from pydantic import Field

from app.models.research_source import SourceType
from app.schemas.base import CamelModel

# ==================== CrossRef Lookup ====================


class CrossRefLookupRequest(CamelModel):
    """Request to look up metadata via CrossRef DOI."""

    doi: str = Field(..., description="DOI to look up (with or without URL prefix)")


class CrossRefLookupResponse(CamelModel):
    """Normalized metadata returned from CrossRef."""

    title: str | None = None
    authors: list[str] | None = None
    publisher: str | None = None
    journal_name: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publication_date: str | None = None
    isbn: str | None = None


# ==================== Capture from Browser ====================


class CaptureSourceRequest(CamelModel):
    """Request to save a source captured from the embedded browser."""

    url: str = Field(..., description="URL of the captured page")
    title: str = Field(..., description="Page title")
    description: str | None = Field(None, description="Description or abstract")
    doi: str | None = Field(None, description="DOI if found")
    authors: list[str] | None = Field(
        None, description="Author names (free-form strings)"
    )
    publication_date: str | None = Field(None, description="Publication date")
    publisher: str | None = Field(None, description="Publisher name")
    journal_name: str | None = Field(None, description="Journal name")
    volume: str | None = Field(None, description="Volume number")
    issue: str | None = Field(None, description="Issue number")
    pages: str | None = Field(None, description="Page range")
    isbn: str | None = Field(None, description="ISBN")
    source_type: SourceType = Field(
        default=SourceType.WEBSITE, description="Type of source"
    )
    content_text: str | None = Field(
        None, description="Extracted or manually pasted page content"
    )
    academic_score: float | None = Field(
        None, description="Academic score from extraction"
    )
