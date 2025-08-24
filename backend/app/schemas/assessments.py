"""
Pydantic schemas for assessments
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.learning_outcomes import ALOResponse, ULOResponse


class RubricCriterion(BaseModel):
    """Schema for a rubric criterion"""

    name: str = Field(..., min_length=1, description="Criterion name")
    description: str = Field(..., description="Criterion description")
    points: float = Field(..., ge=0, description="Maximum points")
    levels: list[str] = Field(default_factory=list, description="Performance levels")


class Rubric(BaseModel):
    """Schema for assessment rubric"""

    criteria: list[RubricCriterion] = Field(..., min_length=1)
    total_points: float = Field(..., ge=0)


class AssessmentBase(BaseModel):
    """Base schema for Assessments"""

    title: str = Field(..., min_length=1, max_length=500, description="Assessment title")
    type: str = Field(..., description="Assessment type (formative/summative)")
    category: str = Field(..., description="Assessment category (quiz, exam, project, etc.)")
    weight: float = Field(..., ge=0, le=100, description="Percentage of final grade")
    description: str | None = Field(None, description="Brief description")
    specification: str | None = Field(None, description="Detailed requirements")

    # Timeline
    release_week: int | None = Field(None, ge=1, le=52)
    release_date: date | None = None
    due_week: int | None = Field(None, ge=1, le=52)
    due_date: date | None = None
    duration: str | None = Field(None, max_length=100, description="Duration (e.g., '2 hours')")

    # Details
    questions: int | None = Field(None, ge=0, description="Number of questions")
    word_count: int | None = Field(None, ge=0, description="Word count requirement")
    group_work: bool = Field(default=False, description="Is group work allowed")
    submission_type: str | None = Field(None, description="Submission type (online/in-person/both)")
    status: str = Field(default="draft", description="Assessment status")


class AssessmentCreate(AssessmentBase):
    """Schema for creating an Assessment"""

    rubric: Rubric | None = None


class AssessmentUpdate(BaseModel):
    """Schema for updating an Assessment"""

    title: str | None = Field(None, min_length=1, max_length=500)
    type: str | None = None
    category: str | None = None
    weight: float | None = Field(None, ge=0, le=100)
    description: str | None = None
    specification: str | None = None
    release_week: int | None = Field(None, ge=1, le=52)
    release_date: date | None = None
    due_week: int | None = Field(None, ge=1, le=52)
    due_date: date | None = None
    duration: str | None = Field(None, max_length=100)
    rubric: Rubric | None = None
    questions: int | None = Field(None, ge=0)
    word_count: int | None = Field(None, ge=0)
    group_work: bool | None = None
    submission_type: str | None = None
    status: str | None = None


class AssessmentResponse(AssessmentBase):
    """Schema for Assessment response"""

    id: str
    unit_id: str
    rubric: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssessmentWithOutcomes(AssessmentResponse):
    """Schema for Assessment with its learning outcomes"""

    assessment_outcomes: list[ALOResponse] = []
    mapped_ulos: list[ULOResponse] = []
    linked_materials: list[str] = []  # Material IDs


class AssessmentMapping(BaseModel):
    """Schema for mapping assessments to ULOs"""

    ulo_ids: list[str] = Field(..., description="List of ULO IDs to map")


class AssessmentMaterialLink(BaseModel):
    """Schema for linking assessments to materials"""

    material_ids: list[str] = Field(..., description="List of material IDs to link")


class GradeDistribution(BaseModel):
    """Schema for grade distribution summary"""

    total_weight: float = Field(..., description="Total weight of all assessments")
    formative_weight: float = Field(..., description="Total weight of formative assessments")
    summative_weight: float = Field(..., description="Total weight of summative assessments")
    is_valid: bool = Field(..., description="Whether weights sum to 100%")
    assessments_by_category: dict[str, float] = Field(..., description="Weight by category")
    assessments_by_type: dict[str, int] = Field(..., description="Count by type")


class AssessmentTimeline(BaseModel):
    """Schema for assessment timeline"""

    week_number: int
    assessments: list[AssessmentResponse]
    total_weight: float


class AssessmentFilter(BaseModel):
    """Schema for filtering assessments"""

    type: str | None = None
    category: str | None = None
    status: str | None = None
    release_week: int | None = Field(None, ge=1, le=52)
    due_week: int | None = Field(None, ge=1, le=52)
    search: str | None = Field(None, description="Search in title and description")


class AssessmentValidation(BaseModel):
    """Schema for assessment validation results"""

    is_valid: bool
    total_weight: float
    errors: list[str] = []
    warnings: list[str] = []

    @field_validator("total_weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Validate total weight"""
        if v < 0 or v > 100:
            raise ValueError("Total weight must be between 0 and 100")
        return v
