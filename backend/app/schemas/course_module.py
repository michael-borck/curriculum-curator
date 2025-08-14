"""
Course Module schemas for course structure management
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModuleType(str, Enum):
    """Module delivery type based on teaching philosophy"""

    TRADITIONAL = "traditional"
    FLIPPED = "flipped"
    PROJECT = "project"
    INQUIRY = "inquiry"
    COMPETENCY = "competency"
    MIXED = "mixed"


class ModuleContent(BaseModel):
    """Content structure for a module"""

    pre_class_content: dict[str, Any] | None = Field(
        None, description="Pre-class materials for flipped classroom"
    )
    in_class_content: dict[str, Any] | None = Field(
        None, description="In-class activities"
    )
    post_class_content: dict[str, Any] | None = Field(
        None, description="Post-class assignments"
    )
    resources: list[str] = Field(
        default_factory=list, description="Additional resources"
    )
    learning_objectives: list[str] = Field(
        default_factory=list, description="Module learning objectives"
    )


class CourseModuleBase(BaseModel):
    """Base course module properties"""

    number: int = Field(..., description="Module number in sequence")
    title: str = Field(..., description="Module title")
    description: str | None = Field(None, description="Module description")
    type: ModuleType = Field(ModuleType.TRADITIONAL, description="Module type")
    duration_minutes: int = Field(120, description="Expected duration in minutes")
    is_optional: bool = Field(False, description="Whether module is optional")
    prerequisites: list[int] = Field(
        default_factory=list, description="Prerequisite module numbers"
    )


class CourseModuleCreate(CourseModuleBase):
    """Properties required to create a course module"""

    course_id: str = Field(..., description="Parent course ID")
    content: ModuleContent | None = None


class CourseModuleUpdate(BaseModel):
    """Properties that can be updated"""

    title: str | None = None
    description: str | None = None
    type: ModuleType | None = None
    duration_minutes: int | None = None
    is_optional: bool | None = None
    prerequisites: list[int] | None = None
    content: ModuleContent | None = None
    is_complete: bool | None = None


class CourseModuleResponse(CourseModuleBase):
    """Course module response with all properties"""

    id: str
    course_id: str
    is_complete: bool = False
    materials_count: int = 0
    pre_class_content: dict[str, Any] | None = None
    in_class_content: dict[str, Any] | None = None
    post_class_content: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config"""

        from_attributes = True


class CourseModuleListResponse(BaseModel):
    """List of course modules"""

    modules: list[CourseModuleResponse]
    total: int
    course_id: str


class ModuleBulkOperation(BaseModel):
    """Bulk operation on modules"""

    module_ids: list[str] = Field(..., description="Module IDs to operate on")
    operation: str = Field(..., description="Operation: reorder, delete, mark_complete")
    data: dict[str, Any] | None = Field(None, description="Additional operation data")


class ModuleReorder(BaseModel):
    """Reorder modules in a course"""

    module_order: list[dict[str, int]] = Field(
        ..., description="List of module IDs and their new positions"
    )


class CourseClone(BaseModel):
    """Clone course request"""

    new_title: str = Field(..., description="Title for the cloned course")
    new_code: str = Field(..., description="Code for the cloned course")
    include_modules: bool = Field(True, description="Clone modules")
    include_materials: bool = Field(False, description="Clone materials")
    include_lrd: bool = Field(False, description="Clone LRD")
    semester: str | None = Field(None, description="Target semester")


class CourseTemplate(BaseModel):
    """Course template definition"""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    teaching_philosophy: str = Field(..., description="Recommended teaching philosophy")
    module_structure: list[dict[str, Any]] = Field(
        ..., description="Predefined module structure"
    )
    duration_weeks: int = Field(12, description="Default duration")
    assessment_structure: dict[str, float] | None = Field(
        None, description="Default assessment weights"
    )


class CourseProgress(BaseModel):
    """Course progress tracking"""

    course_id: str
    total_modules: int
    completed_modules: int
    total_materials: int
    completed_materials: int
    overall_progress: float = Field(..., description="Progress percentage 0-100")
    estimated_hours_remaining: float | None = None
    last_activity: datetime | None = None
    milestones: list[dict[str, Any]] = Field(default_factory=list)


class CourseStatistics(BaseModel):
    """Course statistics and analytics"""

    course_id: str
    student_count: int = 0
    avg_completion_rate: float = 0.0
    total_content_hours: float = 0.0
    module_statistics: list[dict[str, Any]] = Field(default_factory=list)
    engagement_metrics: dict[str, Any] | None = None
