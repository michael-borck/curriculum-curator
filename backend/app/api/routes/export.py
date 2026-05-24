"""
Unified export routes — two thin generic endpoints over the ExportRegistry.

    GET /units/{unit_id}/export/{export_format}
    GET /materials/{material_id}/export/{export_format}

All format-specific logic lives behind the registry seam; these routes only
authorise the target, dispatch, and stream. Unsupported (format, scope) pairs
and missing content map to clean HTTP status codes.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_material, get_user_unit
from app.models.weekly_material import WeeklyMaterial
from app.schemas.unit import UnitResponse
from app.services.export import (
    ExportContentError,
    ExportOptions,
    ExportResult,
    ExportScope,
    ExportUnsupportedError,
    UnknownExportFormatError,
    UnsupportedExportScopeError,
    export_registry,
)
from app.services.lms_terminology import TargetLMS

logger = logging.getLogger(__name__)

router = APIRouter()


def _stream(result: ExportResult) -> StreamingResponse:
    return StreamingResponse(
        result.buf,
        media_type=result.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )


async def _dispatch(
    export_format: str,
    scope: ExportScope,
    target_id: str,
    db: Session,
    target_lms: TargetLMS,
) -> StreamingResponse:
    options = ExportOptions(target_lms=target_lms)
    try:
        result = await export_registry.export(
            export_format, scope, target_id, db, options
        )
    except ExportUnsupportedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except (
        UnknownExportFormatError,
        UnsupportedExportScopeError,
        ExportContentError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return _stream(result)


@router.get("/units/{unit_id}/export/{export_format}")
async def export_unit(
    export_format: str,
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    target_lms: Annotated[TargetLMS, Query()] = TargetLMS.GENERIC,
) -> StreamingResponse:
    """Export a whole unit in the given format (e.g. scorm, imscc, qti, html)."""
    return await _dispatch(
        export_format, ExportScope.UNIT, str(unit.id), db, target_lms
    )


@router.get("/materials/{material_id}/export/{export_format}")
async def export_material(
    export_format: str,
    material: Annotated[WeeklyMaterial, Depends(get_user_material)],
    db: Annotated[Session, Depends(get_db)],
    target_lms: Annotated[TargetLMS, Query()] = TargetLMS.GENERIC,
) -> StreamingResponse:
    """Export a single material in the given format (e.g. pdf, docx, h5p_*)."""
    return await _dispatch(
        export_format, ExportScope.MATERIAL, str(material.id), db, target_lms
    )
