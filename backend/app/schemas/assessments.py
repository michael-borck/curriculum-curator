"""
Pydantic schemas for assessments
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.base import CamelModel
from app.schemas.learning_outcomes import ALOResponse, ULOResponse


class RubricType(str, Enum):
    """Supported rubric formats"""

    ANALYTIC = "analytic"
    SINGLE_POINT = "single_point"
    HOLISTIC = "holistic"
    CHECKLIST = "checklist"


class RubricLevel(CamelModel):
    """Column header in a rubric (performance level)"""

    label: str = Field(..., min_length=1, description="Level label (e.g. Excellent)")
    points: float | None = Field(None, description="Points for this level")
    description: str | None = Field(
        None, description="Level description (used by holistic rubrics)"
    )


class RubricCriterion(CamelModel):
    """Row in a rubric (criterion being assessed)"""

    name: str = Field(..., min_length=1, description="Criterion name")
    description: str = Field(default="", description="Criterion description")
    weight: float = Field(default=0, ge=0, description="Weight as % of total")
    cells: list[str] = Field(
        default_factory=list,
        description="One description per level (same order as levels)",
    )


class Rubric(CamelModel):
    """Schema for assessment rubric — covers analytic, single-point, holistic, checklist"""

    type: RubricType = Field(default=RubricType.ANALYTIC, description="Rubric format")
    levels: list[RubricLevel] = Field(
        default_factory=list, description="Column headers"
    )
    criteria: list[RubricCriterion] = Field(
        default_factory=list, description="Row definitions"
    )
    total_points: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_rubric_structure(self) -> "Rubric":
        """Validate structure based on rubric type."""
        if self.type == RubricType.HOLISTIC:
            if len(self.criteria) > 0:
                raise ValueError("Holistic rubrics must not have criteria rows")
            if len(self.levels) == 0:
                raise ValueError("Holistic rubrics require at least one level")
        elif len(self.criteria) > 0 and len(self.levels) > 0:
                for i, criterion in enumerate(self.criteria):
                    if len(criterion.cells) > 0 and len(criterion.cells) != len(
                        self.levels
                    ):
                        raise ValueError(
                            f"Criterion '{criterion.name}' (index {i}) has "
                            f"{len(criterion.cells)} cells but there are "
                            f"{len(self.levels)} levels"
                        )
        return self


class AssessmentBase(CamelModel):
    """Base schema for Assessments"""

    title: str = Field(
        ..., min_length=1, max_length=500, description="Assessment title"
    )
    type: str = Field(..., description="Assessment type (formative/summative)")
    category: str = Field(
        ..., description="Assessment category (quiz, exam, project, etc.)"
    )
    weight: float = Field(..., ge=0, le=100, description="Percentage of final grade")
    description: str | None = Field(None, description="Brief description")
    specification: str | None = Field(None, description="Detailed requirements")

    # Timeline
    release_week: int | None = Field(None, ge=1, le=52)
    release_date: date | None = None
    due_week: int | None = Field(None, ge=1, le=52)
    due_date: date | None = None
    duration: str | None = Field(
        None, max_length=100, description="Duration (e.g., '2 hours')"
    )

    # Details
    questions: int | None = Field(None, ge=0, description="Number of questions")
    word_count: int | None = Field(None, ge=0, description="Word count requirement")
    group_work: bool = Field(default=False, description="Is group work allowed")
    submission_type: str | None = Field(
        None, description="Submission type (online/in-person/both)"
    )
    status: str = Field(default="draft", description="Assessment status")


class AssessmentCreate(AssessmentBase):
    """Schema for creating an Assessment"""

    rubric: Rubric | None = None


class AssessmentUpdate(CamelModel):
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
    rubric: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AssessmentWithOutcomes(AssessmentResponse):
    """Schema for Assessment with its learning outcomes"""

    assessment_outcomes: list[ALOResponse] = Field(default_factory=list)
    mapped_ulos: list[ULOResponse] = Field(default_factory=list)
    linked_materials: list[str] = Field(default_factory=list)  # Material IDs


class AssessmentMapping(CamelModel):
    """Schema for mapping assessments to ULOs"""

    ulo_ids: list[str] = Field(..., description="List of ULO IDs to map")


class AssessmentMaterialLink(CamelModel):
    """Schema for linking assessments to materials"""

    material_ids: list[str] = Field(..., description="List of material IDs to link")


class GradeDistribution(CamelModel):
    """Schema for grade distribution summary"""

    total_weight: float = Field(..., description="Total weight of all assessments")
    formative_weight: float = Field(
        ..., description="Total weight of formative assessments"
    )
    summative_weight: float = Field(
        ..., description="Total weight of summative assessments"
    )
    is_valid: bool = Field(..., description="Whether weights sum to 100%")
    assessments_by_category: dict[str, float] = Field(
        ..., description="Weight by category"
    )
    assessments_by_type: dict[str, int] = Field(..., description="Count by type")


class AssessmentTimeline(BaseModel):
    """Schema for assessment timeline"""

    week_number: int
    assessments: list[AssessmentResponse]
    total_weight: float


class AssessmentFilter(CamelModel):
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
