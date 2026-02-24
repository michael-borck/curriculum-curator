"""
Pydantic schemas for UDL (Universal Design for Learning) scoring
"""

from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class UDLSubScores(CamelModel):
    """Sub-dimension scores for UDL assessment"""

    representation: float = Field(ge=0, le=100)
    engagement: float = Field(ge=0, le=100)
    expression: float = Field(ge=0, le=100)
    accessibility: float = Field(ge=0, le=100)


class UDLWeekScore(CamelModel):
    """Per-week UDL score"""

    week_number: int
    has_content: bool
    sub_scores: UDLSubScores
    star_rating: float = Field(ge=0, le=5)


class UDLUnitScore(CamelModel):
    """Unit-level UDL score with sub-dimensions"""

    unit_id: str
    overall_score: float = Field(ge=0, le=100)
    star_rating: float = Field(ge=0, le=5)
    sub_scores: UDLSubScores
    assessment_format_diversity: float = Field(ge=0, le=100)
    grade: str
    calculated_at: datetime


class UDLSuggestion(CamelModel):
    """A single UDL improvement suggestion"""

    dimension: str
    priority: str
    issue: str
    suggestion: str


class UDLSuggestionsResponse(CamelModel):
    """Response containing UDL suggestions"""

    unit_id: str
    suggestions: list[UDLSuggestion]
    generated_at: datetime
