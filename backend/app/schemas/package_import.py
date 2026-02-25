"""
Schemas for IMSCC / SCORM package import (round-trip and unified).
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
    quiz_question_count: int = 0
    source_lms: str | None = None
    detected_content_areas: list[str] | None = None


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
    quiz_question_count: int = 0
    weekly_topic_count: int
    source_lms: str | None = None


# ---------------------------------------------------------------------------
# Unified import schemas
# ---------------------------------------------------------------------------


class FilePreviewItem(CamelModel):
    """One file inside a package, with best-guess mapping."""

    path: str
    filename: str
    extension: str
    size_bytes: int
    detected_type: str  # "material" | "assessment" | "outline" | "unknown"
    material_type: str | None = None  # "lecture", "reading", "quiz", etc.
    week_number: int | None = None
    title: str
    processable: bool


class SkippedFile(CamelModel):
    """A file that cannot be processed."""

    path: str
    filename: str
    reason: str  # "unsupported_format", "too_large", "corrupted", "image_not_imported", etc.
    category: str = "not_supported"  # "action_needed" | "not_supported" | "not_applicable"
    content_type: str = "unknown"  # "image" | "video" | "audio" | "lti_tool" | "rubric" | "announcement" | "discussion" | "external_link" | "access_control" | "unknown"


class UnifiedImportPreview(CamelModel):
    """Preview for any ZIP (IMSCC, SCORM, or plain)."""

    package_type: str  # "imscc" | "scorm" | "plain_zip" | "round_trip"
    source_lms: str | None = None
    is_round_trip: bool
    unit_code: str
    unit_title: str
    duration_weeks: int
    files: list[FilePreviewItem]
    skipped_files: list[SkippedFile]
    material_count: int
    assessment_count: int
    total_processable: int
    total_skipped: int
    detected_content_areas: list[str] | None = None


class UnifiedImportResult(CamelModel):
    """Result after applying a unified import."""

    unit_id: str
    unit_code: str
    unit_title: str
    task_id: str
