"""
Standalone HTML export for entire units.

Wraps the existing export_unit_html function with the BaseExporter interface.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any

from app.services.export.base import BaseExporter, ExportResult
from app.services.html_export_service import export_unit_html

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class HTMLExporter(BaseExporter):
    """Exports units as standalone HTML with inline styles."""

    async def export_material(
        self,
        material_id: str,
        db: Session,
        **kwargs: Any,
    ) -> ExportResult:
        raise NotImplementedError(
            "HTMLExporter supports unit-level export only. "
            "Use DocumentExporter for single-material HTML export."
        )

    async def export_unit(
        self,
        unit_id: str,
        db: Session,
        **kwargs: Any,
    ) -> ExportResult:
        html_str, filename = export_unit_html(unit_id, db)
        buf = BytesIO(html_str.encode("utf-8"))
        buf.seek(0)
        return ExportResult(
            buf=buf,
            filename=filename,
            media_type="text/html",
        )


# Singleton
html_exporter = HTMLExporter()
