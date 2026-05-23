"""SCORM 1.2 export adapter — wraps the SCORM export service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.export.base import (
    BaseExporter,
    ExportOptions,
    ExportResult,
    ExportScope,
)
from app.services.lms_terminology import TargetLMS
from app.services.scorm_service import scorm_export_service

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ScormExporter(BaseExporter):
    """Exports a whole Unit as a SCORM 1.2 (.zip) package."""

    supported_scopes = frozenset({ExportScope.UNIT})

    async def export_unit(
        self, unit_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        buf, filename = scorm_export_service.export_unit(
            unit_id,
            db,
            target_lms=options.target_lms or TargetLMS.GENERIC,
            target_overrides=options.target_overrides,
            on_progress=options.on_progress,
        )
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")
