"""
Pydantic schemas for Mode B (multi-file zip → existing unit) imports.

Mode B applies the canonical + source-files pattern from Phase 3 of the
structured-import plan: a zip of materials is grouped by (directory,
filename stem); one file per group becomes the editable WeeklyMaterial
and the rest are attached as downloadable source files.

Wire format is camelCase via ``CamelModel`` (matches the Mode A schemas
in routes/material_import.py).
"""

from __future__ import annotations

from app.schemas.base import CamelModel


class BatchGroupSourceFile(CamelModel):
    """A non-canonical file that will be attached as a source file."""

    path: str
    """Path of the file inside the uploaded zip."""

    filename: str
    """Bare filename (no directory)."""

    file_format: str
    """Lowercased extension without the dot (e.g. ``pdf``)."""


class BatchGroupPreview(CamelModel):
    """One multi-format group in a batch preview."""

    name: str
    """Group name (the shared filename stem)."""

    directory: str
    """Directory inside the zip the group lives in ("" for the root)."""

    detected_week: int | None
    """Week number derived from the canonical filename + folder path,
    or None when no week signal was found."""

    canonical_path: str
    """Path of the file that will be parsed into the editable material."""

    canonical_filename: str
    """Bare filename of the canonical file."""

    canonical_format: str
    """Lowercased extension of the canonical file."""

    parser: str
    """Id of the parser that will be used on the canonical file."""

    source_files: list[BatchGroupSourceFile]
    """Non-canonical files attached to this group, in upload order."""


class BatchStandaloneFile(CamelModel):
    """A file that grouped into a singleton — imported as its own material."""

    path: str
    filename: str
    file_format: str
    detected_week: int | None
    parser: str


class BatchPreviewResponse(CamelModel):
    """Result of analysing a batch zip without writing anything."""

    unit_id: str
    groups: list[BatchGroupPreview]
    """Multi-format groups (canonical + at least one source file)."""

    standalone_files: list[BatchStandaloneFile]
    """Single-format files, each imported as its own material."""

    warnings: list[str]
    """Things the user should know (e.g. unsupported extensions skipped)."""

    total_materials: int
    """How many WeeklyMaterials would be created (groups + standalones)."""

    total_source_files: int
    """How many source files would be attached across all groups."""


class BatchGroupOverride(CamelModel):
    """Per-group override supplied at apply time, keyed by group name.

    ``canonical_filename`` re-selects which member becomes the editable
    material (useful when a sparse PPTX should yield to a richer DOCX).
    ``week_number`` overrides the auto-detected week.
    """

    name: str
    canonical_filename: str | None = None
    week_number: int | None = None


class BatchApplyResponse(CamelModel):
    """Returned immediately by batch/apply — poll status for progress."""

    task_id: str


class BatchStatusResponse(CamelModel):
    """Progress snapshot for a running batch import task."""

    task_id: str
    status: str
    total_files: int
    processed_files: int
    current_file: str | None
    unit_id: str | None
    errors: list[str]


class AttachedSourceFile(CamelModel):
    """Metadata recorded on a material for one attached source file.

    Stored in ``material_metadata["attached_source_files"]`` and surfaced
    by the source-files listing endpoint.
    """

    filename: str
    file_format: str
    original_size: int
    sha256: str


class SourceFileListResponse(CamelModel):
    """Source files attached to a material."""

    material_id: str
    source_files: list[AttachedSourceFile]


__all__ = [
    "AttachedSourceFile",
    "BatchApplyResponse",
    "BatchGroupOverride",
    "BatchGroupPreview",
    "BatchGroupSourceFile",
    "BatchPreviewResponse",
    "BatchStandaloneFile",
    "BatchStatusResponse",
    "SourceFileListResponse",
]
