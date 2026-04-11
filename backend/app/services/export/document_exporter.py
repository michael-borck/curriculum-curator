"""
Document export (HTML, PDF, DOCX, PPTX) via Pandoc + Typst.

Wraps the existing ExportService with the BaseExporter interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.export.base import BaseExporter, ExportResult
from app.services.export_service import ExportFormat, ExportService
from app.services.export_service import export_service as _singleton

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class DocumentExporter(BaseExporter):
    """Exports materials/units to document formats using Pandoc + Typst."""

    def __init__(self, service: ExportService | None = None) -> None:
        self._service = service or _singleton

    async def export_material(
        self,
        material_id: str,
        db: Session,
        **kwargs: Any,
    ) -> ExportResult:
        fmt: ExportFormat = kwargs.get("fmt", ExportFormat.HTML)
        buf, filename, media_type = await self._service.export_material(
            material_id=material_id,
            db=db,
            fmt=fmt,
            title=kwargs.get("title"),
            author=kwargs.get("author"),
            reference_doc=kwargs.get("reference_doc"),
        )
        return ExportResult(buf=buf, filename=filename, media_type=media_type)

# Unit-level document export was removed during the pre-MVP Content
# cleanup (the underlying export_service.export_unit iterated legacy
# Content rows). If unit-level document export returns as a feature
# it should iterate WeeklyMaterial rows instead.


# Singleton
document_exporter = DocumentExporter()
