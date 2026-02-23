"""
API endpoints for document export using Pandoc + Typst.

Replaces the Quarto-based content_export routes with a simpler,
more bundleable export pipeline. See ADR-033.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_user_content,
    get_user_unit,
)
from app.schemas.content import ContentResponse
from app.schemas.export import ExportAvailability, ExportRequest
from app.schemas.unit import UnitResponse
from app.schemas.user import UserResponse
from app.services.export_service import export_service, get_user_template_path

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export/availability", response_model=ExportAvailability)
async def check_export_availability() -> ExportAvailability:
    """Check which export formats are available (Pandoc/Typst installed)."""
    result = export_service.check_availability()
    return ExportAvailability(**result)


@router.post("/content/{content_id}/export/document")
async def export_content_document(
    content: Annotated[ContentResponse, Depends(get_user_content)],
    export_request: ExportRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> StreamingResponse:
    """Export a single content item to the specified format."""
    reference_doc = get_user_template_path(
        current_user.id, export_request.format, current_user.teaching_preferences
    )
    try:
        buf, filename, media_type = await export_service.export_content(
            content_id=content.id,
            db=db,
            fmt=export_request.format,
            title=export_request.title,
            author=export_request.author,
            reference_doc=reference_doc,
        )
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


@router.post("/units/{unit_id}/export/document")
async def export_unit_document(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    export_request: ExportRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> StreamingResponse:
    """Export an entire unit (all contents) as a single document."""
    reference_doc = get_user_template_path(
        current_user.id, export_request.format, current_user.teaching_preferences
    )
    try:
        buf, filename, media_type = await export_service.export_unit(
            unit_id=unit.id,
            db=db,
            fmt=export_request.format,
            title=export_request.title,
            author=export_request.author,
            reference_doc=reference_doc,
        )
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
