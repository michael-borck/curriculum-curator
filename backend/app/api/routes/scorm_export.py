"""
API endpoint for SCORM 1.2 export.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.schemas.unit import UnitResponse
from app.services.lms_terminology import TargetLMS
from app.services.scorm_service import scorm_export_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/units/{unit_id}/export/scorm")
async def export_unit_scorm(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    target_lms: Annotated[TargetLMS, Query()] = TargetLMS.GENERIC,
) -> StreamingResponse:
    """Export a unit as a SCORM 1.2 (.zip) package."""
    buf, filename = scorm_export_service.export_unit(unit.id, db, target_lms=target_lms)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
