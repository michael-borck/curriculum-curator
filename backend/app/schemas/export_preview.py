"""Pydantic schemas for the export preview and package endpoints."""

from pydantic import Field

from app.schemas.base import CamelModel


class MaterialExportPreview(CamelModel):
    """Preview data for a single material in the export dialog."""

    material_id: str
    title: str
    week_number: int
    category: str
    content_types: list[str]
    resolved_targets: dict[str, list[str]]
    available_targets: dict[str, list[str]]


class ExportPreviewResponse(CamelModel):
    """Response from GET /units/{id}/export/preview."""

    materials: list[MaterialExportPreview]


class MaterialTargetOverride(CamelModel):
    """Per-material target overrides submitted by the export dialog."""

    material_id: str
    targets: dict[str, list[str]]


class ExportPackageRequest(CamelModel):
    """Request body for POST /units/{id}/export/package."""

    package_type: str  # "imscc" | "scorm" | "zip"
    target_lms: str = "generic"
    material_targets: list[MaterialTargetOverride] = Field(default_factory=list)
