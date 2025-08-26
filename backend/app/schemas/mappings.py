"""
Pydantic schemas for outcome mappings and relationships
"""

from datetime import datetime

from pydantic import BaseModel, Field


class OutcomeMapping(BaseModel):
    """Base schema for outcome mappings"""

    ulo_id: str = Field(..., description="Unit Learning Outcome ID")
    created_at: datetime | None = None


class MaterialULOMapping(BaseModel):
    """Schema for mapping materials to ULOs"""

    material_id: str = Field(..., description="Material ID")
    ulo_ids: list[str] = Field(..., description="List of ULO IDs to map")


class AssessmentULOMapping(BaseModel):
    """Schema for mapping assessments to ULOs"""

    assessment_id: str = Field(..., description="Assessment ID")
    ulo_ids: list[str] = Field(..., description="List of ULO IDs to map")


class WLOULOMapping(BaseModel):
    """Schema for mapping WLOs to ULOs"""

    wlo_id: str = Field(..., description="Weekly Learning Outcome ID")
    ulo_ids: list[str] = Field(..., description="List of ULO IDs to map")


class MaterialAssessmentLink(BaseModel):
    """Schema for linking materials to assessments"""

    material_id: str = Field(..., description="Material ID")
    assessment_ids: list[str] = Field(..., description="List of assessment IDs to link")


class OutcomeCoverage(BaseModel):
    """Schema for outcome coverage analysis"""

    ulo_id: str
    ulo_code: str
    ulo_description: str
    material_count: int = 0
    assessment_count: int = 0
    weekly_coverage: list[int] = []
    coverage_status: str  # well-covered, moderate, gap


class OutcomeCoverageReport(BaseModel):
    """Schema for full outcome coverage report"""

    total_ulos: int
    covered_ulos: int
    coverage_percentage: float
    outcomes: list[OutcomeCoverage]
    gaps: list[str]  # ULO IDs with no coverage
    recommendations: list[str]


class AlignmentMatrix(BaseModel):
    """Schema for outcome alignment matrix"""

    ulos: list[dict[str, str]]  # id, code, description
    materials: list[dict[str, str]]  # id, title, week
    assessments: list[dict[str, str]]  # id, title, type
    material_mappings: dict[str, list[str]]  # material_id -> [ulo_ids]
    assessment_mappings: dict[str, list[str]]  # assessment_id -> [ulo_ids]


class BulkMapping(BaseModel):
    """Schema for bulk mapping operations"""

    source_type: str = Field(
        ..., description="Type of source (material/assessment/wlo)"
    )
    source_ids: list[str] = Field(..., min_length=1, description="List of source IDs")
    ulo_ids: list[str] = Field(..., min_length=1, description="List of ULO IDs to map")
    operation: str = Field(
        default="add", description="Operation type (add/remove/replace)"
    )


class MappingSummary(BaseModel):
    """Schema for mapping summary statistics"""

    total_ulos: int
    total_materials: int
    total_assessments: int
    mapped_materials: int
    mapped_assessments: int
    unmapped_materials: int
    unmapped_assessments: int
    average_ulos_per_material: float
    average_ulos_per_assessment: float
