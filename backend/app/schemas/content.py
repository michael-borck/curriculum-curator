"""
Content schemas for API requests and responses
"""

from typing import Any
from pydantic import BaseModel, Field


class ContentBase(BaseModel):
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


class ContentUpdate(BaseModel):
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


class ContentListResponse(BaseModel):
    """Schema for paginated content list responses"""
    
    contents: list[ContentResponse]
    total: int
    skip: int
    limit: int


# Legacy schemas for LLM generation (kept for compatibility)
class ContentGenerationRequest(BaseModel):
    """Request schema for content generation via LLM"""
    
    content_type: str
    pedagogy_style: str
    context: dict[str, Any]
    stream: bool = False


class ContentEnhanceRequest(BaseModel):
    """Request schema for content enhancement via LLM"""
    
    content: str
    pedagogy_style: str
    suggestions: list | None = None


class ContentValidationResponse(BaseModel):
    """Response schema for content validation"""
    
    is_valid: bool
    issues: list
    suggestions: list


# Simplified schemas for backward compatibility
class ContentGenerate(BaseModel):
    """Request schema for content generation"""

    topic: str
    pedagogy: str
    content_type: str


class ContentEnhance(BaseModel):
    """Request schema for content enhancement"""

    content: str
    enhancement_type: str