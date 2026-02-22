"""
Schemas for IMSCC / SCORM package import (round-trip).
"""

from app.schemas.base import CamelModel


class ImportPreview(CamelModel):
    """Preview information extracted from a package before committing."""

    format: str  # "imscc" or "scorm_1.2"
    is_round_trip: bool
    unit_code: str
    unit_title: str
    pedagogy_type: str
    difficulty_level: str
    year: int
    semester: str
    duration_weeks: int
    credit_points: int
    ulo_count: int
    material_count: int
    assessment_count: int
    aol_mapping_count: int
    sdg_mapping_count: int
    gc_mapping_count: int
    source_lms: str | None = None


class ImportResult(CamelModel):
    """Result of committing a package import."""

    unit_id: str
    unit_code: str
    unit_title: str
    ulo_count: int
    material_count: int
    assessment_count: int
    aol_mapping_count: int
    sdg_mapping_count: int
    gc_mapping_count: int
    weekly_topic_count: int
    source_lms: str | None = None
