"""
API endpoints for exporting individual materials and bulk material ZIP archives.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.schemas.unit import UnitResponse
from app.services.export_service import ExportFormat, export_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/materials/{material_id}/export")
async def export_material(
    material_id: str,
    db: Annotated[Session, Depends(get_db)],
    fmt: ExportFormat = Query(ExportFormat.HTML, alias="format"),
) -> StreamingResponse:
    """Export a single material as HTML, PDF, DOCX, or PPTX."""
    try:
        buf, filename, media_type = await export_service.export_material(
            material_id=material_id,
            db=db,
            fmt=fmt,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    return StreamingResponse(
        buf,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/units/{unit_id}/export/materials")
async def export_materials_zip(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    fmt: ExportFormat = Query(ExportFormat.HTML, alias="format"),
) -> StreamingResponse:
    """Export all materials for a unit as a ZIP archive organised by week."""
    try:
        buf, filename = await export_service.export_materials_zip(
            unit_id=unit.id,
            db=db,
            fmt=fmt,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
