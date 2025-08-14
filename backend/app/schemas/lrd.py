"""
LRD (Learning Requirements Document) schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LRDStatus(str, Enum):
    """LRD approval status"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class LRDTargetAudience(BaseModel):
    """Target audience information"""

    level: str = Field(
        ..., description="Skill level (Beginner, Intermediate, Advanced)"
    )
    prerequisites: list[str] = Field(
        default_factory=list, description="Required prerequisites"
    )
    class_size: int = Field(30, description="Expected class size")
    age_group: str | None = Field(None, description="Target age group")


class LRDStructure(BaseModel):
    """Course structure definition"""

    pre_class: str | None = Field(None, description="Pre-class activities")
    in_class: str = Field(..., description="In-class activities")
    post_class: str | None = Field(None, description="Post-class activities")
    duration_weeks: int = Field(12, description="Course duration in weeks")
    hours_per_week: int = Field(3, description="Hours per week")


class LRDAssessment(BaseModel):
    """Assessment strategy"""

    formative: list[dict[str, Any]] = Field(
        default_factory=list, description="Formative assessment methods"
    )
    summative: list[dict[str, Any]] = Field(
        default_factory=list, description="Summative assessment methods"
    )
    weighting: dict[str, float] | None = Field(
        None, description="Assessment weightings"
    )


class LRDContent(BaseModel):
    """Complete LRD content structure"""

    topic: str = Field(..., description="Course topic")
    description: str = Field(..., description="Course description")
    objectives: list[str] = Field(..., description="Learning objectives")
    target_audience: LRDTargetAudience
    structure: LRDStructure
    assessment: LRDAssessment
    modules: list[dict[str, Any]] = Field(
        default_factory=list, description="Course modules"
    )
    resources: list[str] = Field(default_factory=list, description="Required resources")
    teaching_philosophy: str = Field(..., description="Teaching philosophy to apply")
    success_criteria: list[str] = Field(
        default_factory=list, description="Success criteria for the course"
    )


class ApprovalRecord(BaseModel):
    """Record of an approval action"""

    date: datetime
    approver_id: str
    approver_name: str
    status: str
    comments: str | None = None


class LRDBase(BaseModel):
    """Base LRD properties"""

    version: str = Field("1.0", description="LRD version")
    status: LRDStatus = Field(LRDStatus.DRAFT, description="Approval status")
    content: LRDContent


class LRDCreate(LRDBase):
    """Properties required to create an LRD"""

    course_id: str


class LRDUpdate(BaseModel):
    """Properties that can be updated"""

    status: LRDStatus | None = None
    content: LRDContent | None = None


class LRDApproval(BaseModel):
    """Approval/rejection request"""

    status: LRDStatus = Field(..., description="New status (approved/rejected)")
    comments: str = Field(..., description="Approval comments")


class LRDResponse(LRDBase):
    """LRD response with all properties"""

    id: str
    course_id: str
    created_at: datetime
    updated_at: datetime
    approval_history: list[ApprovalRecord] = Field(default_factory=list)
    task_lists: list[dict[str, Any]] = Field(default_factory=list)

    class Config:
        """Pydantic config"""

        from_attributes = True


class LRDListResponse(BaseModel):
    """List of LRDs with pagination"""

    lrds: list[LRDResponse]
    total: int
    skip: int
    limit: int


class TaskGeneration(BaseModel):
    """Task generation request from LRD"""

    include_optional: bool = Field(True, description="Include optional tasks")
    granularity: str = Field("detailed", description="Task granularity level")
    auto_assign: bool = Field(False, description="Auto-assign tasks to modules")


class GeneratedTasks(BaseModel):
    """Generated task list from LRD"""

    lrd_id: str
    total_tasks: int
    parent_tasks: list[dict[str, Any]]
    estimated_hours: float
    suggested_timeline: dict[str, Any]
