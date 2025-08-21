"""
Pydantic schemas for course structure models
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# Course Outline Schemas
class UnitOutlineBase(BaseModel):
    """Base schema for course outline"""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    rationale: str | None = None
    duration_weeks: int = Field(default=12, ge=1, le=52)
    credit_points: int = Field(default=6, ge=1, le=12)
    student_workload_hours: int | None = Field(None, ge=1, le=500)
    delivery_mode: str | None = Field(None, pattern="^(face-to-face|online|blended)$")
    teaching_pattern: str | None = None
    prerequisites: str | None = None
    corequisites: str | None = None
    assumed_knowledge: str | None = None
    graduate_attributes: list[str] | None = None


class UnitOutlineCreate(UnitOutlineBase):
    """Schema for creating course outline"""

    unit_id: UUID


class UnitOutlineUpdate(BaseModel):
    """Schema for updating course outline"""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    rationale: str | None = None
    duration_weeks: int | None = Field(None, ge=1, le=52)
    credit_points: int | None = Field(None, ge=1, le=12)
    student_workload_hours: int | None = Field(None, ge=1, le=500)
    delivery_mode: str | None = None
    teaching_pattern: str | None = None
    prerequisites: str | None = None
    corequisites: str | None = None
    assumed_knowledge: str | None = None
    graduate_attributes: list[str] | None = None
    status: str | None = None


class UnitOutlineResponse(UnitOutlineBase):
    """Schema for course outline response"""

    id: UUID
    unit_id: UUID
    status: str
    completion_percentage: float
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None = None
    published_at: datetime | None = None

    class Config:
        from_attributes = True


# Learning Outcome Schemas
class LearningOutcomeBase(BaseModel):
    """Base schema for learning outcome"""

    outcome_type: str = Field(..., pattern="^(clo|ulo|wlo)$")
    outcome_code: str | None = Field(None, max_length=20)
    outcome_text: str = Field(..., min_length=10)
    bloom_level: str = Field(
        ..., pattern="^(remember|understand|apply|analyze|evaluate|create)$"
    )
    cognitive_processes: str | None = None
    sequence_order: int = Field(default=0, ge=0)
    assessment_methods: str | None = None
    is_measurable: bool = Field(default=True)
    success_criteria: str | None = None


class LearningOutcomeCreate(LearningOutcomeBase):
    """Schema for creating learning outcome"""

    unit_id: UUID | None = None
    unit_outline_id: UUID | None = None
    weekly_topic_id: UUID | None = None
    parent_outcome_id: UUID | None = None


class LearningOutcomeUpdate(BaseModel):
    """Schema for updating learning outcome"""

    outcome_text: str | None = Field(None, min_length=10)
    bloom_level: str | None = None
    cognitive_processes: str | None = None
    sequence_order: int | None = Field(None, ge=0)
    assessment_methods: str | None = None
    success_criteria: str | None = None
    is_active: bool | None = None


class LearningOutcomeResponse(LearningOutcomeBase):
    """Schema for learning outcome response"""

    id: UUID
    unit_id: UUID | None = None
    unit_outline_id: UUID | None = None
    weekly_topic_id: UUID | None = None
    parent_outcome_id: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Weekly Topic Schemas
class WeeklyTopicBase(BaseModel):
    """Base schema for weekly topic"""

    week_number: int = Field(..., ge=1, le=52)
    week_type: str = Field(
        default="regular", pattern="^(regular|revision|assessment|break|holiday)$"
    )
    topic_title: str = Field(..., min_length=1, max_length=500)
    topic_description: str | None = None
    key_concepts: list[str] | None = None
    learning_objectives: str | None = None
    pre_class_modules: list[dict[str, Any]] | None = None
    pre_class_duration_minutes: int | None = Field(None, ge=0, le=600)
    pre_class_resources: list[dict[str, str]] | None = None
    in_class_activities: list[dict[str, Any]] | None = None
    in_class_duration_minutes: int | None = Field(None, ge=0, le=600)
    in_class_format: str | None = None
    post_class_tasks: list[dict[str, Any]] | None = None
    post_class_duration_minutes: int | None = Field(None, ge=0, le=600)
    has_assessment: bool = Field(default=False)
    assessment_details: str | None = None
    required_readings: list[dict[str, str]] | None = None
    supplementary_resources: list[dict[str, str]] | None = None
    equipment_required: str | None = None


class WeeklyTopicCreate(WeeklyTopicBase):
    """Schema for creating weekly topic"""

    unit_outline_id: UUID
    unit_id: UUID | None = None


class WeeklyTopicUpdate(BaseModel):
    """Schema for updating weekly topic"""

    topic_title: str | None = Field(None, min_length=1, max_length=500)
    topic_description: str | None = None
    key_concepts: list[str] | None = None
    learning_objectives: str | None = None
    pre_class_modules: list[dict[str, Any]] | None = None
    pre_class_duration_minutes: int | None = Field(None, ge=0, le=600)
    in_class_activities: list[dict[str, Any]] | None = None
    in_class_duration_minutes: int | None = Field(None, ge=0, le=600)
    post_class_tasks: list[dict[str, Any]] | None = None
    post_class_duration_minutes: int | None = Field(None, ge=0, le=600)
    has_assessment: bool | None = None
    assessment_details: str | None = None
    is_complete: bool | None = None
    content_ready: bool | None = None


class WeeklyTopicResponse(WeeklyTopicBase):
    """Schema for weekly topic response"""

    id: UUID
    unit_outline_id: UUID
    unit_id: UUID | None = None
    is_complete: bool
    content_ready: bool
    total_student_hours: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Assessment Plan Schemas
class AssessmentPlanBase(BaseModel):
    """Base schema for assessment plan"""

    assessment_name: str = Field(..., min_length=1, max_length=500)
    assessment_type: str = Field(
        ...,
        pattern="^(quiz|assignment|exam|project|presentation|participation|lab_report|portfolio|peer_review|reflection)$",
    )
    assessment_mode: str = Field(default="summative", pattern="^(formative|summative)$")
    description: str = Field(..., min_length=10)
    weight_percentage: float = Field(..., ge=0, le=100)
    pass_mark: float | None = Field(None, ge=0, le=100)
    release_week: int | None = Field(None, ge=1, le=52)
    due_week: int = Field(..., ge=1, le=52)
    duration_minutes: int | None = Field(None, ge=1, le=600)
    submission_format: str | None = None
    submission_method: str | None = None
    group_work: bool = Field(default=False)
    group_size: int | None = Field(None, ge=2, le=10)
    aligned_outcome_ids: list[UUID] | None = None
    has_rubric: bool = Field(default=False)
    rubric_criteria: dict[str, Any] | None = None
    marking_criteria: str | None = None
    requirements: str | None = None
    instructions: str | None = None
    resources_provided: list[dict[str, str]] | None = None
    feedback_method: str | None = None
    feedback_timeline_days: int | None = Field(None, ge=1, le=60)
    late_penalty: str | None = None
    extension_policy: str | None = None


class AssessmentPlanCreate(AssessmentPlanBase):
    """Schema for creating assessment plan"""

    unit_outline_id: UUID
    unit_id: UUID | None = None


class AssessmentPlanUpdate(BaseModel):
    """Schema for updating assessment plan"""

    assessment_name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=10)
    weight_percentage: float | None = Field(None, ge=0, le=100)
    pass_mark: float | None = Field(None, ge=0, le=100)
    release_week: int | None = Field(None, ge=1, le=52)
    due_week: int | None = Field(None, ge=1, le=52)
    duration_minutes: int | None = Field(None, ge=1, le=600)
    submission_format: str | None = None
    submission_method: str | None = None
    group_work: bool | None = None
    group_size: int | None = Field(None, ge=2, le=10)
    aligned_outcome_ids: list[UUID] | None = None
    has_rubric: bool | None = None
    rubric_criteria: dict[str, Any] | None = None
    marking_criteria: str | None = None
    instructions: str | None = None
    is_finalized: bool | None = None
    materials_ready: bool | None = None


class AssessmentPlanResponse(AssessmentPlanBase):
    """Schema for assessment plan response"""

    id: UUID
    unit_outline_id: UUID
    unit_id: UUID | None = None
    is_finalized: bool
    materials_ready: bool
    estimated_hours: float | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Chat Session Schemas
class ChatSessionBase(BaseModel):
    """Base schema for chat session"""

    session_name: str | None = Field(None, max_length=500)
    session_type: str = Field(default="content_creation")
    pedagogy_preference: str | None = None
    complexity_level: str | None = None
    tone_preference: str | None = None


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating chat session"""

    unit_id: UUID | None = None
    unit_outline_id: UUID | None = None


class ChatSessionUpdate(BaseModel):
    """Schema for updating chat session"""

    session_name: str | None = Field(None, max_length=500)
    status: str | None = None
    current_stage: str | None = None
    pedagogy_preference: str | None = None
    complexity_level: str | None = None
    tone_preference: str | None = None
    user_satisfaction_score: float | None = Field(None, ge=1, le=5)
    feedback_notes: str | None = None


class ChatSessionResponse(ChatSessionBase):
    """Schema for chat session response"""

    id: UUID
    user_id: UUID
    unit_id: UUID | None = None
    unit_outline_id: UUID | None = None
    status: str
    current_stage: str
    progress_percentage: float
    message_count: int
    total_tokens_used: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    last_activity_at: datetime
    total_duration_minutes: int

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema for chat message"""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] | None = None


class ChatWorkflowStatus(BaseModel):
    """Schema for chat workflow status"""

    session_id: UUID
    current_stage: str
    progress_percentage: float
    decisions_made: dict[str, Any]
    pending_questions: list[str] | None = None
    can_advance: bool
    next_stage: str | None = None
