"""
API endpoint for IMS Common Cartridge export.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.schemas.unit import UnitResponse
from app.services.imscc_service import imscc_export_service
from app.services.lms_terminology import TargetLMS

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/units/{unit_id}/export/imscc")
async def export_unit_imscc(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    target_lms: Annotated[TargetLMS, Query()] = TargetLMS.GENERIC,
) -> StreamingResponse:
    """Export a unit as an IMS Common Cartridge v1.1 (.imscc) file."""
    buf, filename = imscc_export_service.export_unit(
        unit.id, db, target_lms=target_lms
    )

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
