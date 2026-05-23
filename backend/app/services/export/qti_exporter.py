"""QTI 2.1 quiz export adapter — wraps the QTI export service.

Gathers quiz nodes from WeeklyMaterial content (the loop that used to live in
the route) and builds the filename here, where the unit/material context lives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.repositories import unit_repo
from app.services.export._gather import gather_unit_quiz_questions, load_material
from app.services.export.base import (
    BaseExporter,
    ExportContentError,
    ExportOptions,
    ExportResult,
    ExportScope,
)
from app.services.qti_service import qti_exporter as _qti_service
from app.services.unit_export_data import extract_quiz_nodes, slugify

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class QtiExporter(BaseExporter):
    """Exports quiz questions as a QTI 2.1 (.zip) package, per unit or material."""

    supported_scopes = frozenset({ExportScope.UNIT, ExportScope.MATERIAL})

    async def export_unit(
        self, unit_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        unit = unit_repo.get_unit_by_id(db, unit_id)
        if unit is None:
            raise ExportContentError("Unit not found")
        questions = gather_unit_quiz_questions(unit_id, db)
        buf = _qti_service.export_qti21_zip(questions, f"{unit.code} - Quiz Export")
        filename = f"{unit.code}_{slugify(str(unit.title))}_qti.zip"
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        material = load_material(material_id, db)
        questions = (
            extract_quiz_nodes(material.content_json) if material.content_json else []
        )
        buf = _qti_service.export_qti21_zip(
            questions, f"{material.title} - Quiz Export"
        )
        filename = f"{slugify(str(material.title))}_qti.zip"
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")
