"""
Export service package.

The export seam: every format is an adapter (extending ``BaseExporter``,
returning ``ExportResult``) registered in the ``export_registry``. Routes
dispatch through the registry by (format key, scope); adding a format means
writing one adapter and one registration line.
"""

from app.services.export.base import (
    BaseExporter,
    ExportContentError,
    ExportOptions,
    ExportResult,
    ExportScope,
    ExportUnsupportedError,
)
from app.services.export.registry import (
    ExportRegistry,
    UnknownExportFormatError,
    UnsupportedExportScopeError,
    export_registry,
)

__all__ = [
    "BaseExporter",
    "ExportContentError",
    "ExportOptions",
    "ExportRegistry",
    "ExportResult",
    "ExportScope",
    "ExportUnsupportedError",
    "UnknownExportFormatError",
    "UnsupportedExportScopeError",
    "export_registry",
]
