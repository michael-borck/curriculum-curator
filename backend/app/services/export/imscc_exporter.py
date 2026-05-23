"""IMS Common Cartridge export adapter — wraps the IMSCC export service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.export.base import (
    BaseExporter,
    ExportOptions,
    ExportResult,
    ExportScope,
)
from app.services.imscc_service import imscc_export_service
from app.services.lms_terminology import TargetLMS

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ImsccExporter(BaseExporter):
    """Exports a whole Unit as an IMS Common Cartridge (.imscc) package."""

    supported_scopes = frozenset({ExportScope.UNIT})

    async def export_unit(
        self, unit_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        buf, filename = imscc_export_service.export_unit(
            unit_id,
            db,
            target_lms=options.target_lms or TargetLMS.GENERIC,
            target_overrides=options.target_overrides,
            on_progress=options.on_progress,
        )
        return ExportResult(buf=buf, filename=filename, media_type="application/zip")
