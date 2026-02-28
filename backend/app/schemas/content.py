"""
Content schemas for unit materials (lectures, worksheets, etc.)

Content body (markdown) is stored in Git, not the database.
These schemas handle metadata and API request/response formats.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.models.enums import ContentType
from app.schemas.base import CamelModel


class ContentStatus(str, Enum):
    """Content status"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


# =============================================================================
# API Request/Response Schemas
# =============================================================================


class ContentCreate(CamelModel):
    """Schema for creating new content"""

    title: str = Field(..., min_length=1, max_length=500)
    content_type: ContentType
    body: str = Field(default="", description="Markdown content body")
    content_json: dict[str, Any] | None = Field(
        None, description="Structured content (ProseMirror/TipTap JSON)"
    )
    summary: str | None = None
    order_index: int = Field(default=0, ge=0)
    week_number: int | None = Field(None, ge=1, le=52)
    estimated_duration_minutes: int | None = Field(None, ge=0, le=600)


class ContentUpdate(CamelModel):
    """Schema for updating content"""

    title: str | None = Field(None, min_length=1, max_length=500)
    body: str | None = Field(None, description="Markdown content body")
    content_json: dict[str, Any] | None = None
    summary: str | None = None
    order_index: int | None = Field(None, ge=0)
    week_number: int | None = None
    status: ContentStatus | None = None
    estimated_duration_minutes: int | None = None


class ContentResponse(CamelModel):
    """Schema for content responses (includes body from Git)"""

    id: str
    unit_id: str
    title: str
    content_type: str
    body: str = Field(default="", description="Markdown content from Git")
    content_json: dict[str, Any] | None = None
    summary: str | None = None
    order_index: int
    week_number: int | None = None
    status: str
    estimated_duration_minutes: int | None = None
    current_commit: str | None = None
    created_at: datetime | str
    updated_at: datetime | str | None = None


class ContentMetadata(CamelModel):
    """Schema for content metadata (without body - for listings)"""

    id: str
    unit_id: str
    title: str
    content_type: str
    summary: str | None = None
    order_index: int
    week_number: int | None = None
    status: str
    estimated_duration_minutes: int | None = None
    created_at: datetime | str
    updated_at: datetime | str | None = None


class ContentList(CamelModel):
    """Schema for content list responses"""

    contents: list[ContentMetadata]
    total: int


# =============================================================================
# Version History Schemas
# =============================================================================


class ContentVersion(CamelModel):
    """Schema for a content version (from Git history)"""

    commit: str
    date: str
    message: str
    author_email: str | None = None


class ContentHistory(CamelModel):
    """Schema for content version history"""

    content_id: str
    versions: list[ContentVersion]


class ContentDiff(CamelModel):
    """Schema for diff between versions"""

    content_id: str
    old_commit: str
    new_commit: str
    diff: str


class ContentRevertRequest(CamelModel):
    """Schema for reverting to a previous version"""

    commit: str = Field(..., description="Commit hash to revert to")


# =============================================================================
# LLM Generation schemas (for AI features)
# =============================================================================


class ContentGenerationRequest(CamelModel):
    """Request schema for content generation via LLM"""

    content_type: ContentType
    pedagogy_style: str
    topic: str | None = None
    context: str | None = None
    stream: bool = False
    unit_id: str | None = Field(
        default=None, description="Unit ID for Learning Design lookup"
    )
    design_id: str | None = Field(
        default=None, description="Specific Learning Design ID"
    )
    pedagogy_override: str | None = Field(
        default=None, description="Per-week pedagogy override"
    )
    week_number: int | None = Field(default=None, description="Week number for context")
    source_material_ids: list[str] | None = Field(
        default=None, description="IDs of existing materials to use as source context"
    )


class ContentEnhanceRequest(CamelModel):
    """Request schema for content enhancement via LLM"""

    content: str
    pedagogy_style: str
    suggestions: list[str] | None = None
    unit_id: str | None = Field(
        default=None, description="Unit ID for Learning Design lookup"
    )
    design_id: str | None = Field(
        default=None, description="Specific Learning Design ID"
    )
