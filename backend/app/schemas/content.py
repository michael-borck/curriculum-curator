"""
Content schemas for API requests and responses
"""

from typing import Any

from pydantic import Field

from app.schemas.base import CamelModel


class ContentBase(CamelModel):
    """Base content schema with common fields"""

    title: str = Field(..., min_length=1, max_length=500)
    type: str = Field(...)  # ContentType enum value
    content_markdown: str | None = None
    summary: str | None = None
    estimated_duration_minutes: int | None = Field(None, ge=0, le=600)
    difficulty_level: str | None = None
    learning_objectives: list[str] | None = None


class ContentCreate(ContentBase):
    """Schema for creating new content"""

    unit_id: str = Field(...)
    parent_content_id: str | None = None
    order_index: int = Field(default=0, ge=0)
    status: str | None = Field(default="draft")


class ContentUpdate(CamelModel):
    """Schema for updating content - all fields optional"""

    title: str | None = Field(None, min_length=1, max_length=500)
    type: str | None = None
    status: str | None = None
    content_markdown: str | None = None
    summary: str | None = None
    order_index: int | None = Field(None, ge=0)
    estimated_duration_minutes: int | None = Field(None, ge=0, le=600)
    difficulty_level: str | None = None
    learning_objectives: list[str] | None = None


class ContentResponse(ContentBase):
    """Schema for content responses"""

    id: str
    status: str
    unit_id: str
    parent_content_id: str | None
    order_index: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ContentListResponse(CamelModel):
    """Schema for paginated content list responses"""

    contents: list[ContentResponse]
    total: int
    skip: int
    limit: int


# Legacy schemas for LLM generation (kept for compatibility)
class ContentGenerationRequest(CamelModel):
    """Request schema for content generation via LLM"""

    content_type: str
    pedagogy_style: str
    context: dict[str, Any]
    stream: bool = False


class ContentEnhanceRequest(CamelModel):
    """Request schema for content enhancement via LLM"""

    content: str
    pedagogy_style: str
    suggestions: list | None = None


class ContentValidationResponse(CamelModel):
    """Response schema for content validation"""

    is_valid: bool
    issues: list
    suggestions: list


# Simplified schemas for backward compatibility
class ContentGenerate(CamelModel):
    """Request schema for content generation"""

    topic: str
    pedagogy: str
    content_type: str


class ContentEnhance(CamelModel):
    """Request schema for content enhancement"""

    content: str
    enhancement_type: str


class ContentVersionCreate(CamelModel):
    """Schema for creating a new content version"""
    
    title: str = Field(..., min_length=1, max_length=500)
    content_markdown: str | None = None
    content_html: str | None = None
    change_description: str | None = None


class ContentVersionResponse(CamelModel):
    """Schema for content version responses"""
    
    id: str
    material_id: str = Field(alias="materialId")
    version: int
    parent_version_id: str | None = Field(None, alias="parentVersionId")
    title: str
    content: dict[str, Any]
    raw_content: str | None = Field(None, alias="rawContent")
    created_at: str = Field(alias="createdAt")
    created_by: str | None = Field(None, alias="createdBy")
    change_summary: str | None = Field(None, alias="changeSummary")
    is_latest: bool = Field(alias="isLatest")
    word_count: int | None = Field(None, alias="wordCount")
    quality_score: float | None = Field(None, alias="qualityScore")


class ContentVersionCompare(CamelModel):
    """Schema for comparing two content versions"""
    
    old_version_id: str = Field(alias="oldVersionId")
    new_version_id: str = Field(alias="newVersionId")
    differences: list[dict[str, Any]]
