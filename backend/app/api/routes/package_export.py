"""
Package export endpoint — receives the user's final choices from the Export Dialog.

POST /units/{unit_id}/export/package
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.schemas.export_preview import ExportPackageRequest
from app.schemas.unit import UnitResponse
from app.services.imscc_service import imscc_export_service
from app.services.lms_terminology import TargetLMS
from app.services.scorm_service import scorm_export_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_override_map(
    request: ExportPackageRequest,
) -> dict[str, dict[str, list[str]]]:
    """Convert the request's material_targets list into the dict the services expect."""
    override_map: dict[str, dict[str, list[str]]] = {}
    for mt in request.material_targets:
        override_map[mt.material_id] = mt.targets
    return override_map


def _parse_target_lms(raw: str) -> TargetLMS:
    """Safely convert a string to TargetLMS, defaulting to GENERIC."""
    try:
        return TargetLMS(raw)
    except ValueError:
        return TargetLMS.GENERIC


@router.post("/units/{unit_id}/export/package")
async def export_package(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    request: ExportPackageRequest,
) -> StreamingResponse:
    """Export a unit package with per-material target overrides from the dialog."""
    override_map = _build_override_map(request)
    target_lms = _parse_target_lms(request.target_lms)

    if request.package_type == "imscc":
        buf, filename = imscc_export_service.export_unit(
            unit.id,
            db,
            target_lms=target_lms,
            target_overrides=override_map,
        )
    elif request.package_type == "scorm":
        buf, filename = scorm_export_service.export_unit(
            unit.id,
            db,
            target_lms=target_lms,
            target_overrides=override_map,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported package type: {request.package_type}",
        )

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
