"""
API endpoint for checking export format availability.

Per-material document export lives in ``routes/material_export.py``; the
legacy per-Content and per-unit document export routes were removed
during the Content model cleanup (see docs/code-audit-2026-04-11.md).
"""

import logging

from fastapi import APIRouter

from app.schemas.export import ExportAvailability
from app.services.export_service import export_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export/availability", response_model=ExportAvailability)
async def check_export_availability() -> ExportAvailability:
    """Check which export formats are available (Pandoc/Typst installed)."""
    result = export_service.check_availability()
    return ExportAvailability(**result)
