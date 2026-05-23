"""
Base types for the export seam.

Every export adapter extends :class:`BaseExporter`, declares the scopes it
supports, and returns an :class:`ExportResult`. Per-export configuration is
carried by the typed :class:`ExportOptions`; each adapter honours the subset it
supports (only ``target_lms`` is supplied over HTTP — ``target_overrides`` and
``on_progress`` are passed programmatically by the package orchestrator).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.services.lms_terminology import TargetLMS
    from app.services.task_store import ProgressCallback


class ExportScope(str, Enum):
    """Whether an export targets a whole Unit or a single WeeklyMaterial."""

    UNIT = "unit"
    MATERIAL = "material"


@dataclass
class ExportResult:
    """The uniform return shape at the export seam.

    Each adapter computes its own filename and media_type — where that
    knowledge lives — instead of routes patching the gap.
    """

    buf: BytesIO
    filename: str
    media_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExportOptions:
    """Cross-cutting export options; each adapter honours the subset it supports.

    Attributes:
        target_lms: LMS dialect for package exports (scorm/imscc). ``None`` →
            the adapter's default (GENERIC).
        target_overrides: Per-material target overrides, supplied by the package
            orchestrator (``{material_id: {content_type: [targets]}}``).
        on_progress: Progress callback, supplied by the package orchestrator.
    """

    target_lms: TargetLMS | None = None
    target_overrides: dict[str, dict[str, list[str]]] | None = None
    on_progress: ProgressCallback | None = None


class ExportContentError(Exception):
    """No exportable content of the requested kind was found (maps to HTTP 404)."""


class ExportUnsupportedError(Exception):
    """Content exists but cannot be rendered in this format (maps to HTTP 422)."""


class BaseExporter:
    """An export adapter: produces an :class:`ExportResult` for a given scope.

    Override ``export_unit`` and/or ``export_material`` for the scopes listed in
    ``supported_scopes``. The defaults raise so an unlisted scope fails loudly,
    but the registry checks ``supported_scopes`` before dispatching.
    """

    supported_scopes: ClassVar[frozenset[ExportScope]] = frozenset()

    async def export_unit(
        self, unit_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        raise NotImplementedError(
            f"{type(self).__name__} does not support unit-level export"
        )

    async def export_material(
        self, material_id: str, db: Session, options: ExportOptions
    ) -> ExportResult:
        raise NotImplementedError(
            f"{type(self).__name__} does not support material-level export"
        )
