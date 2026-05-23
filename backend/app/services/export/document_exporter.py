"""Document export adapter (HTML, PDF, DOCX, PPTX) via Pandoc + Typst.

Wraps ``ExportService.export_material`` with the export seam, resolving the
owning user's reference-doc template here (locality) instead of in the route.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.repositories import unit_repo, user_repo
from app.services.export._gather import load_material
from app.services.export.base import (
    BaseExporter,
    ExportContentError,
    ExportOptions,
    ExportResult,
    ExportScope,
)
from app.services.export_service import (
    ExportFormat,
    export_service,
    get_user_template_path,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _resolve_reference_doc(
    material_unit_id: str, db: Session, fmt: ExportFormat
) -> Path | None:
    """Resolve the owning user's reference-doc template for this format, if any."""
    unit = unit_repo.get_unit_by_id(db, material_unit_id)
    if unit is None:
        return None
    owner = user_repo.get_user_by_id(db, str(unit.owner_id))
    if owner is None:
        return None
    return get_user_template_path(str(owner.id), fmt, owner.teaching_preferences)


async def export_material_document(
    material_id: str, db: Session, fmt: ExportFormat
) -> ExportResult:
    """Export a single material to a document format. Shared by the document and
    HTML adapters. Raises ExportContentError (→ 404) when the material is
    missing; lets FileNotFoundError (→ 503) and RuntimeError (→ 500) propagate.
    """
    material = load_material(material_id, db)
    reference_doc = _resolve_reference_doc(str(material.unit_id), db, fmt)
    try:
        buf, filename, media_type = await export_service.export_material(
            material_id=material_id,
            db=db,
            fmt=fmt,
            reference_doc=reference_doc,
        )
    except ValueError as exc:
        raise ExportContentError(str(exc)) from exc
    return ExportResult(buf=buf, filename=filename, media_type=media_type)


class DocumentExporter(BaseExporter):
    """Exports a single material to one document format (PDF, DOCX, PPTX)."""

    supported_scopes = frozenset({ExportScope.MATERIAL})

    def __init__(self, fmt: ExportFormat) -> None:
        self._fmt = fmt

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        return await export_material_document(material_id, db, self._fmt)
