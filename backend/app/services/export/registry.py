"""The export seam: one registry mapping a format key → adapter.

The single source of truth for "what export formats exist." Adding a format =
write one adapter + one ``register`` line below. Format keys are the canonical
underscore vocabulary shared with ``format_resolver`` (see CONTEXT.md).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.export.base import (
    BaseExporter,
    ExportOptions,
    ExportResult,
    ExportScope,
)
from app.services.export.document_exporter import DocumentExporter
from app.services.export.h5p_exporter import (
    H5pBranchingExporter,
    H5pCoursePresentationExporter,
    H5pInteractiveVideoExporter,
    H5pQuestionSetExporter,
)
from app.services.export.html_exporter import HtmlExporter
from app.services.export.imscc_exporter import ImsccExporter
from app.services.export.qti_exporter import QtiExporter
from app.services.export.scorm_exporter import ScormExporter
from app.services.export_service import ExportFormat

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class UnknownExportFormatError(Exception):
    """Requested an export format that isn't registered (maps to HTTP 404)."""

    def __init__(self, fmt: str) -> None:
        super().__init__(f"Unknown export format: {fmt}")
        self.fmt = fmt


class UnsupportedExportScopeError(Exception):
    """Format exists but doesn't support the requested scope (maps to HTTP 404)."""

    def __init__(self, fmt: str, scope: ExportScope) -> None:
        super().__init__(
            f"Export format '{fmt}' does not support {scope.value}-level export"
        )
        self.fmt = fmt
        self.scope = scope


class ExportRegistry:
    """Maps export format keys to adapters and dispatches by (format, scope)."""

    def __init__(self) -> None:
        self._adapters: dict[str, BaseExporter] = {}

    def register(self, fmt: str, adapter: BaseExporter) -> None:
        self._adapters[fmt] = adapter

    def formats(self) -> list[str]:
        """All registered format keys."""
        return sorted(self._adapters)

    def supports(self, fmt: str, scope: ExportScope) -> bool:
        adapter = self._adapters.get(fmt)
        return adapter is not None and scope in adapter.supported_scopes

    def available_formats(self, scope: ExportScope) -> list[str]:
        """Format keys that support the given scope."""
        return sorted(
            fmt
            for fmt, adapter in self._adapters.items()
            if scope in adapter.supported_scopes
        )

    async def export(
        self,
        fmt: str,
        scope: ExportScope,
        target_id: str,
        db: Session,
        options: ExportOptions | None = None,
    ) -> ExportResult:
        adapter = self._adapters.get(fmt)
        if adapter is None:
            raise UnknownExportFormatError(fmt)
        if scope not in adapter.supported_scopes:
            raise UnsupportedExportScopeError(fmt, scope)
        opts = options or ExportOptions()
        if scope is ExportScope.UNIT:
            return await adapter.export_unit(target_id, db, opts)
        return await adapter.export_material(target_id, db, opts)


def _build_default_registry() -> ExportRegistry:
    """Construct the registry with every export adapter wired in."""
    registry = ExportRegistry()
    # Whole-unit LMS packages
    registry.register("scorm", ScormExporter())
    registry.register("imscc", ImsccExporter())
    # Per-material content targets (canonical vocabulary, shared with format_resolver)
    registry.register("qti", QtiExporter())
    registry.register("h5p_question_set", H5pQuestionSetExporter())
    registry.register("h5p_course_presentation", H5pCoursePresentationExporter())
    registry.register("h5p_branching", H5pBranchingExporter())
    registry.register("h5p_interactive_video", H5pInteractiveVideoExporter())
    registry.register("html", HtmlExporter())
    # Document formats (single material → Pandoc/Typst)
    registry.register("pdf", DocumentExporter(ExportFormat.PDF))
    registry.register("docx", DocumentExporter(ExportFormat.DOCX))
    registry.register("pptx", DocumentExporter(ExportFormat.PPTX))
    return registry


export_registry = _build_default_registry()
