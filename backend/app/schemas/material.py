"""
Material management schemas with versioning support
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MaterialType(str, Enum):
    """Types of educational materials"""

    LECTURE = "lecture"
    WORKSHEET = "worksheet"
    QUIZ = "quiz"
    LAB = "lab"
    CASE_STUDY = "case_study"
    READING = "reading"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    ASSESSMENT = "assessment"
    RESOURCE = "resource"


class MaterialFormat(str, Enum):
    """Material content format"""

    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    VIDEO = "video"
    INTERACTIVE_HTML = "interactive_html"
    JUPYTER = "jupyter"
    SLIDES = "slides"


class QualityMetrics(BaseModel):
    """Quality scoring metrics for materials"""

    completeness: float = Field(0.0, ge=0, le=100, description="Content completeness %")
    clarity: float = Field(0.0, ge=0, le=100, description="Clarity score %")
    engagement: float = Field(0.0, ge=0, le=100, description="Engagement score %")
    alignment: float = Field(0.0, ge=0, le=100, description="LO alignment score %")
    accessibility: float = Field(0.0, ge=0, le=100, description="Accessibility score %")
    overall: float = Field(0.0, ge=0, le=100, description="Overall quality score %")


class MaterialContent(BaseModel):
    """Structured content for materials"""

    format: MaterialFormat = Field(
        MaterialFormat.MARKDOWN, description="Content format"
    )
    body: str = Field(..., description="Main content body")
    metadata: dict[str, Any] | None = Field(
        None, description="Format-specific metadata"
    )
    media_urls: list[str] = Field(
        default_factory=list, description="Associated media URLs"
    )
    code_snippets: list[dict[str, str]] = Field(
        default_factory=list, description="Code examples"
    )
    exercises: list[dict[str, Any]] = Field(
        default_factory=list, description="Exercises"
    )
    solutions: list[dict[str, Any]] = Field(
        default_factory=list, description="Exercise solutions"
    )


class MaterialBase(BaseModel):
    """Base material properties"""

    type: MaterialType = Field(..., description="Material type")
    title: str = Field(..., description="Material title")
    description: str | None = Field(None, description="Material description")
    learning_objectives: list[str] = Field(
        default_factory=list, description="Learning objectives addressed"
    )
    prerequisites: list[str] = Field(
        default_factory=list, description="Prerequisite knowledge"
    )
    estimated_duration_minutes: int = Field(
        30, description="Estimated time to complete"
    )
    difficulty_level: str = Field("intermediate", description="Difficulty level")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")


class MaterialCreate(MaterialBase):
    """Properties required to create a material"""

    course_id: str = Field(..., description="Parent course ID")
    module_id: str | None = Field(None, description="Parent module ID")
    content: MaterialContent = Field(..., description="Material content")
    teaching_philosophy: str = Field(..., description="Teaching philosophy used")
    is_draft: bool = Field(True, description="Whether this is a draft")


class MaterialUpdate(BaseModel):
    """Properties that can be updated"""

    title: str | None = None
    description: str | None = None
    content: MaterialContent | None = None
    learning_objectives: list[str] | None = None
    prerequisites: list[str] | None = None
    estimated_duration_minutes: int | None = None
    difficulty_level: str | None = None
    tags: list[str] | None = None
    is_draft: bool | None = None


class MaterialVersion(BaseModel):
    """Version information for a material"""

    version: int = Field(..., description="Version number")
    parent_version_id: str | None = Field(None, description="Previous version ID")
    created_at: datetime
    created_by: str | None = Field(None, description="Creator user ID")
    change_summary: str | None = Field(None, description="Summary of changes")
    is_latest: bool = Field(True, description="Whether this is the latest version")


class MaterialResponse(MaterialBase):
    """Material response with all properties"""

    id: str
    course_id: str
    module_id: str | None
    version: int = 1
    parent_version_id: str | None = None
    is_latest: bool = True
    is_draft: bool = False
    teaching_philosophy: str
    quality_score: float | None = None
    quality_metrics: QualityMetrics | None = None
    content: dict[str, Any]  # Full content structure
    raw_content: str | None = None  # Raw markdown/text
    created_at: datetime
    updated_at: datetime
    created_by_id: str | None = None
    updated_by_id: str | None = None

    class Config:
        """Pydantic config"""

        from_attributes = True


class MaterialListResponse(BaseModel):
    """List of materials with pagination"""

    materials: list[MaterialResponse]
    total: int
    skip: int
    limit: int


class MaterialVersionHistory(BaseModel):
    """Version history for a material"""

    material_id: str
    current_version: int
    versions: list[MaterialVersion]
    total_versions: int


class MaterialDiff(BaseModel):
    """Difference between two material versions"""

    from_version: int
    to_version: int
    changes: dict[str, Any]
    added_lines: int = 0
    removed_lines: int = 0
    modified_sections: list[str] = Field(default_factory=list)


class MaterialTemplate(BaseModel):
    """Template for creating materials"""

    type: MaterialType
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    structure: dict[str, Any] = Field(..., description="Content structure")
    default_content: MaterialContent
    suggested_duration: int = Field(30, description="Suggested duration in minutes")
    best_for: list[str] = Field(
        default_factory=list, description="Best for these teaching philosophies"
    )


class MaterialBulkOperation(BaseModel):
    """Bulk operation on materials"""

    material_ids: list[str] = Field(..., description="Material IDs to operate on")
    operation: str = Field(
        ..., description="Operation: publish, archive, delete, move, tag"
    )
    data: dict[str, Any] | None = Field(None, description="Operation-specific data")


class MaterialImport(BaseModel):
    """Import materials from external source"""

    source_type: str = Field(..., description="Source type: file, url, lms")
    source_data: str = Field(..., description="Source data (path, URL, etc)")
    course_id: str = Field(..., description="Target course ID")
    module_id: str | None = Field(None, description="Target module ID")
    auto_convert: bool = Field(True, description="Auto-convert to platform format")
    preserve_formatting: bool = Field(True, description="Preserve original formatting")


class MaterialExport(BaseModel):
    """Export materials configuration"""

    format: str = Field(
        "markdown", description="Export format: markdown, html, pdf, scorm"
    )
    include_solutions: bool = Field(False, description="Include solutions")
    include_metadata: bool = Field(True, description="Include metadata")
    combine_materials: bool = Field(False, description="Combine into single file")


class MaterialAnalytics(BaseModel):
    """Analytics for a material"""

    material_id: str
    view_count: int = 0
    avg_time_spent_minutes: float = 0.0
    completion_rate: float = 0.0
    feedback_score: float | None = None
    revision_count: int = 0
    last_accessed: datetime | None = None
    engagement_metrics: dict[str, float] = Field(default_factory=dict)


class MaterialSearch(BaseModel):
    """Search parameters for materials"""

    query: str | None = Field(None, description="Search query")
    types: list[MaterialType] | None = Field(None, description="Filter by types")
    tags: list[str] | None = Field(None, description="Filter by tags")
    difficulty: str | None = Field(None, description="Filter by difficulty")
    min_quality_score: float | None = Field(None, ge=0, le=100)
    teaching_philosophy: str | None = Field(None)
    course_id: str | None = Field(None)
    module_id: str | None = Field(None)
    include_drafts: bool = Field(False)
    only_latest: bool = Field(True)


class MaterialClone(BaseModel):
    """Clone material request"""

    target_course_id: str = Field(..., description="Target course ID")
    target_module_id: str | None = Field(None, description="Target module ID")
    new_title: str | None = Field(None, description="New title (optional)")
    adapt_to_philosophy: str | None = Field(
        None, description="Adapt to different teaching philosophy"
    )
    create_as_draft: bool = Field(True, description="Create as draft")


class ContentValidation(BaseModel):
    """Content validation results"""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    quality_score: float = Field(0.0, ge=0, le=100)
    accessibility_issues: list[str] = Field(default_factory=list)
