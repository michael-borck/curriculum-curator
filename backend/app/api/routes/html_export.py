"""
API endpoint for standalone HTML export.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.schemas.unit import UnitResponse
from app.services.html_export_service import export_unit_html

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/units/{unit_id}/export/html")
async def export_unit_as_html(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Export a unit as a standalone HTML file with inline styles."""
    html, filename = export_unit_html(unit.id, db)

    return Response(
        content=html,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
