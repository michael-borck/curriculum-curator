"""
Pydantic schemas for analytics and reporting
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.base import CamelModel


class UnitOverview(CamelModel):
    """Overview statistics for a unit"""

    unit_id: str
    ulo_count: int
    materials: dict[str, Any]
    assessments: dict[str, Any]
    total_assessment_weight: float
    weeks_with_content: int
    last_updated: datetime


class ProgressReport(CamelModel):
    """Progress report for unit components"""

    unit_id: str
    materials: dict[str, Any]
    assessments: dict[str, Any]
    overall_completion: float
    incomplete_items: dict[str, list[dict]] | None = None


class CompletionReport(CamelModel):
    """Completion status report"""

    unit_id: str
    ulo_completion: list[dict[str, Any]]
    ulos_fully_covered: int
    ulos_total: int
    weeks_with_materials: list[int]
    weeks_with_assessments: list[int]
    completion_percentage: float


class AlignmentReport(CamelModel):
    """Learning outcome alignment report"""

    unit_id: str
    alignment_details: list[dict[str, Any]]
    summary: dict[str, Any]
    recommendations: list[str]


class WeeklyWorkload(CamelModel):
    """Weekly workload analysis"""

    week_number: int
    material_count: int
    material_duration_minutes: int
    assessment_count: int
    assessment_duration_minutes: int
    total_duration_minutes: int
    workload_hours: float
    materials: list[dict[str, Any]]
    assessments: list[dict[str, Any]]


class QualityScore(CamelModel):
    """Quality score for a unit"""

    unit_id: str
    overall_score: float = Field(ge=0, le=100)
    sub_scores: dict[str, float]
    grade: str
    calculated_at: datetime


class ValidationResult(CamelModel):
    """Unit validation result"""

    unit_id: str
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    strict_mode: bool
    validated_at: datetime


class UnitStatistics(CamelModel):
    """Detailed statistics for a unit"""

    unit_id: str
    materials: dict[str, Any]
    assessments: dict[str, Any]
    learning_outcomes: dict[str, Any]
    generated_at: datetime


class Recommendation(BaseModel):
    """Improvement recommendation"""

    category: str
    priority: str
    issue: str
    suggestion: str


class RecommendationReport(BaseModel):
    """Recommendations for unit improvement"""

    unit_id: str
    recommendations: list[Recommendation]
    generated_at: datetime


class ExportData(BaseModel):
    """Export data container"""

    unit_id: str
    export_date: str
    format: str
    data: dict[str, Any]
    csv_ready: bool | None = None
    pdf_ready: bool | None = None
    notice: str | None = None
