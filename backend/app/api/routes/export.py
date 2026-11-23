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
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_material, get_user_unit
from app.models.weekly_material import WeeklyMaterial
from app.schemas.unit import UnitResponse
from app.services.branching_export_service import (
    build_ink_source,
    build_playable_html,
)
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
from app.services.narrated_deck_service import build_narrated_deck

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


@router.get("/materials/{material_id}/export/branching")
async def export_branching_story(
    material: Annotated[WeeklyMaterial, Depends(get_user_material)],
    export_format: str = Query("html", alias="format", pattern="^(html|ink)$"),
):
    """Download a playable HTML story or an Ink source file."""
    html = export_format == "html"
    content = build_playable_html(material) if html else build_ink_source(material)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This material has no branching cards",
        )
    safe_title = "".join(
        char if char.isalnum() or char in " -_" else "_"
        for char in (material.title or "branching-story")
    ).strip() or "branching-story"
    extension = "html" if html else "ink"
    return Response(
        content=content,
        media_type="text/html" if html else "text/plain",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_title}-story.{extension}"'
            )
        },
    )


@router.get("/materials/{material_id}/export/narrated")
async def export_narrated_deck(
    material: Annotated[WeeklyMaterial, Depends(get_user_material)],
):
    """Download a self-contained narrated HTML deck (browser speech playback)."""
    html = build_narrated_deck(material)
    safe_title = "".join(
        char if char.isalnum() or char in " -_" else "_"
        for char in (material.title or "narrated-deck")
    ).strip() or "narrated-deck"
    return Response(
        content=html,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}-narrated.html"'
        },
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
