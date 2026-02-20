"""
Schemas for the Pandoc + Typst export service.
"""

from pydantic import Field

from app.schemas.base import CamelModel
from app.services.export_service import ExportFormat


class ExportRequest(CamelModel):
    """Request to export content or a unit."""

    format: ExportFormat = Field(..., description="Target export format")
    title: str | None = Field(None, description="Title override for the document")
    author: str | None = Field(None, description="Author name for document metadata")


class ExportAvailability(CamelModel):
    """Response indicating which export formats are available."""

    pandoc: bool = False
    pandoc_version: str | None = None
    typst: bool = False
    typst_version: str | None = None
    pdf_available: bool = False
    html_available: bool = False
    docx_available: bool = False
    pptx_available: bool = False
