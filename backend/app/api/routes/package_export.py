"""
Package export endpoint — receives the user's final choices from the Export Dialog.

POST /units/{unit_id}/export/package          — background task (returns task_id)
POST /units/{unit_id}/export/package/sync     — synchronous (returns ZIP directly)

Dispatches through the ExportRegistry by package type (scorm/imscc); the
adapters own the per-material target-override logic and offload the heavy work
off the event loop.
"""

import asyncio
import logging
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.schemas.base import CamelModel
from app.schemas.export_preview import ExportPackageRequest
from app.schemas.unit import UnitResponse
from app.services.export import ExportOptions, ExportScope, export_registry
from app.services.lms_terminology import TargetLMS
from app.services.task_store import create_task, make_progress_cb

logger = logging.getLogger(__name__)

router = APIRouter()

_PACKAGE_FORMATS = ("imscc", "scorm")


class ExportTaskResponse(CamelModel):
    """Returned when an async export is kicked off."""

    task_id: str


def _build_override_map(
    request: ExportPackageRequest,
) -> dict[str, dict[str, list[str]]]:
    """Convert the request's material_targets list into the dict the adapters expect."""
    return {mt.material_id: mt.targets for mt in request.material_targets}


def _parse_target_lms(raw: str) -> TargetLMS:
    """Safely convert a string to TargetLMS, defaulting to GENERIC."""
    try:
        return TargetLMS(raw)
    except ValueError:
        return TargetLMS.GENERIC


def _validate_package_type(package_type: str) -> None:
    if package_type not in _PACKAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported package type: {package_type}",
        )


# ------------------------------------------------------------------
# Async background export (returns task_id immediately)
# ------------------------------------------------------------------
@router.post("/units/{unit_id}/export/package", response_model=ExportTaskResponse)
async def export_package(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    request: ExportPackageRequest,
) -> ExportTaskResponse:
    """Kick off a background package export and return the task_id."""
    _validate_package_type(request.package_type)

    task = create_task(
        "export",
        meta={
            "unit_id": unit.id,
            "unit_code": unit.code,
            "package_type": request.package_type,
        },
    )

    async def _run() -> None:
        try:
            task.status = "processing"
            task.label = "Preparing export…"
            task.notify()

            options = ExportOptions(
                target_lms=_parse_target_lms(request.target_lms),
                target_overrides=_build_override_map(request),
                on_progress=make_progress_cb(task),
            )
            result = await export_registry.export(
                request.package_type, ExportScope.UNIT, str(unit.id), db, options
            )

            # Write to a temp file so the download endpoint can serve it
            suffix = ".imscc" if request.package_type == "imscc" else ".zip"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(result.buf.getvalue())
                tmp_name = tmp.name

            task.result = {
                "file_path": tmp_name,
                "filename": result.filename,
                "media_type": result.media_type,
            }
            task.status = "completed"
            task.label = "Export complete"
            task.notify()
        except Exception as exc:
            logger.exception("Background export failed")
            task.errors.append(str(exc))
            task.status = "failed"
            task.label = "Export failed"
            task.notify()

    asyncio.ensure_future(_run())  # noqa: RUF006
    return ExportTaskResponse(task_id=task.task_id)


# ------------------------------------------------------------------
# Synchronous export (returns ZIP directly — kept for simple cases)
# ------------------------------------------------------------------
@router.post("/units/{unit_id}/export/package/sync")
async def export_package_sync(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    request: ExportPackageRequest,
) -> StreamingResponse:
    """Export a unit package synchronously (returns the ZIP directly)."""
    _validate_package_type(request.package_type)

    options = ExportOptions(
        target_lms=_parse_target_lms(request.target_lms),
        target_overrides=_build_override_map(request),
    )
    result = await export_registry.export(
        request.package_type, ExportScope.UNIT, str(unit.id), db, options
    )

    return StreamingResponse(
        result.buf,
        media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )
