"""
Export service package.

Provides a unified interface for exporting unit content to various formats:
- Document formats (HTML, PDF, DOCX, PPTX) via Pandoc + Typst
- QTI quiz packages (1.2 and 2.1)
- LMS packages (IMSCC, SCORM)
- H5P interactive content (future)

All exporters extend BaseExporter and return ExportResult.
"""

from app.services.export.base import BaseExporter, ExportResult

__all__ = ["BaseExporter", "ExportResult"]
