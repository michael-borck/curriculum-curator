"""
AI-specific request/response schemas for scaffold, fill-gap, etc.
"""

from pydantic import Field

from app.schemas.base import CamelModel

# =============================================================================
# Scaffold Unit
# =============================================================================


class ScaffoldUnitRequest(CamelModel):
    """Request to generate a full unit structure from a title + description."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    duration_weeks: int = Field(default=12, ge=1, le=52)
    pedagogy_style: str = Field(default="mixed_approach")


class ScaffoldULO(CamelModel):
    code: str
    description: str
    bloom_level: str


class ScaffoldWeek(CamelModel):
    week_number: int
    topic: str
    activities: list[str] = Field(default_factory=list)


class ScaffoldAssessment(CamelModel):
    title: str
    category: str
    weight: float
    due_week: int | None = None


class ScaffoldUnitResponse(CamelModel):
    """AI-generated unit structure for review before saving."""

    title: str
    description: str
    ulos: list[ScaffoldULO]
    weeks: list[ScaffoldWeek]
    assessments: list[ScaffoldAssessment]


# =============================================================================
# Fill the Gap
# =============================================================================


class FillGapRequest(CamelModel):
    """Request to generate content for a specific gap in a unit."""

    unit_id: str
    gap_type: str = Field(
        ..., description="Type of gap: ulo, material, assessment"
    )
    context: str = Field(
        default="", description="Additional context for generation"
    )


class FillGapResponse(CamelModel):
    """Generated content to fill a gap."""

    gap_type: str
    generated_content: str
    suggestions: list[str] = Field(default_factory=list)
