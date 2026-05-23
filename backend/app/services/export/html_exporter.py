"""HTML export adapter.

Unit scope → standalone single-file HTML for the whole unit.
Material scope → the material rendered as HTML (shared with the document path).
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from app.services.export.base import (
    BaseExporter,
    ExportOptions,
    ExportResult,
    ExportScope,
)
from app.services.export.document_exporter import export_material_document
from app.services.export_service import ExportFormat
from app.services.html_export_service import export_unit_html

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class HtmlExporter(BaseExporter):
    """Exports units (standalone HTML) and materials (rendered HTML)."""

    supported_scopes = frozenset({ExportScope.UNIT, ExportScope.MATERIAL})

    async def export_unit(
        self, unit_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        html_str, filename = export_unit_html(unit_id, db)
        buf = BytesIO(html_str.encode("utf-8"))
        buf.seek(0)
        return ExportResult(buf=buf, filename=filename, media_type="text/html")

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        return await export_material_document(material_id, db, ExportFormat.HTML)
