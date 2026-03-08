"""
Schemas for the unit outline import feature (ADR-063).
"""

from pydantic import Field

from app.schemas.base import CamelModel

# ---------------------------------------------------------------------------
# Shared sub-schemas (camelCase serialisation)
# ---------------------------------------------------------------------------


class OutlineULO(CamelModel):
    code: str = ""
    description: str
    bloom_level: str = "understand"


class OutlineWeek(CamelModel):
    week_number: int
    topic: str
    activities: list[str] = Field(default_factory=list)
    readings: list[str] = Field(default_factory=list)


class OutlineAssessment(CamelModel):
    title: str
    category: str = "assignment"
    weight: float = 0.0
    due_week: int | None = None
    description: str = ""


class OutlineTextbook(CamelModel):
    title: str
    authors: str = ""
    isbn: str = ""
    required: bool = True


class OutlineSnippet(CamelModel):
    heading: str
    content: str
    keep: bool = True


# ---------------------------------------------------------------------------
# Parse response (returned by POST /parse)
# ---------------------------------------------------------------------------


class OutlineParseResponse(CamelModel):
    """Structured extraction from an outline document, ready for review."""

    unit_code: str | None = None
    unit_title: str | None = None
    description: str | None = None
    credit_points: int | None = None
    duration_weeks: int | None = None
    year: int | None = None
    semester: str | None = None
    prerequisites: str | None = None
    delivery_mode: str | None = None
    teaching_pattern: str | None = None

    learning_outcomes: list[OutlineULO] = Field(default_factory=list)
    weekly_schedule: list[OutlineWeek] = Field(default_factory=list)
    assessments: list[OutlineAssessment] = Field(default_factory=list)
    textbooks: list[OutlineTextbook] = Field(default_factory=list)
    supplementary_info: list[OutlineSnippet] = Field(default_factory=list)

    confidence: float = 0.0
    parser_used: str = "generic"
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Apply request (POST /apply — user-reviewed data)
# ---------------------------------------------------------------------------


class OutlineApplyRequest(CamelModel):
    """User-reviewed extraction to apply as a new unit."""

    # Unit metadata (edited by user)
    unit_code: str = Field(..., min_length=1, max_length=20)
    unit_title: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    credit_points: int = Field(default=6, ge=0, le=100)
    duration_weeks: int = Field(default=12, ge=1, le=52)
    year: int | None = None
    semester: str | None = None
    prerequisites: str = ""
    delivery_mode: str = ""
    teaching_pattern: str = ""
    pedagogy_type: str = "mixed_approach"

    # Structured data (edited by user)
    learning_outcomes: list[OutlineULO] = Field(default_factory=list)
    weekly_schedule: list[OutlineWeek] = Field(default_factory=list)
    assessments: list[OutlineAssessment] = Field(default_factory=list)
    textbooks: list[OutlineTextbook] = Field(default_factory=list)
    supplementary_info: list[OutlineSnippet] = Field(default_factory=list)

    # Metadata
    parser_used: str = "generic"


# ---------------------------------------------------------------------------
# Parser info (GET /parsers)
# ---------------------------------------------------------------------------


class ParserInfo(CamelModel):
    id: str
    display_name: str
    description: str
    supported_formats: list[str]
