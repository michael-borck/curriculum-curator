"""Pydantic schemas for the export preview and package endpoints."""

from pydantic import Field

from app.schemas.base import CamelModel


class ExportTargetWarning(CamelModel):
    """A capability mismatch when exporting a content type to a target (9.21)."""

    severity: str  # "converted" | "dropped"
    message: str
    suggested_target: str | None = None


class MaterialExportPreview(CamelModel):
    """Preview data for a single material in the export dialog."""

    material_id: str
    title: str
    week_number: int
    category: str
    content_types: list[str]
    resolved_targets: dict[str, list[str]]
    available_targets: dict[str, list[str]]
    # Warnings keyed by "contentType:target" — populated only for pairs that
    # would silently drop or convert content (9.21).
    warnings: dict[str, list[ExportTargetWarning]] = Field(default_factory=dict)


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
