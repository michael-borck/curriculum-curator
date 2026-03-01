"""
Package export endpoint — receives the user's final choices from the Export Dialog.

POST /units/{unit_id}/export/package          — background task (returns task_id)
POST /units/{unit_id}/export/package/sync     — synchronous (returns ZIP directly)
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
from app.services.imscc_service import imscc_export_service
from app.services.lms_terminology import TargetLMS
from app.services.scorm_service import scorm_export_service
from app.services.task_store import create_task, make_progress_cb

logger = logging.getLogger(__name__)

router = APIRouter()


class ExportTaskResponse(CamelModel):
    """Returned when an async export is kicked off."""

    task_id: str


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
    if request.package_type not in ("imscc", "scorm"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported package type: {request.package_type}",
        )

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

            override_map = _build_override_map(request)
            target_lms = _parse_target_lms(request.target_lms)
            cb = make_progress_cb(task)

            if request.package_type == "imscc":
                svc = imscc_export_service
            else:
                svc = scorm_export_service  # type: ignore[assignment]

            buf, filename = await asyncio.to_thread(
                svc.export_unit,
                unit.id,
                db,
                target_lms=target_lms,
                target_overrides=override_map,
                on_progress=cb,
            )

            # Write to a temp file so the download endpoint can serve it
            media_type = "application/zip"
            suffix = ".imscc" if request.package_type == "imscc" else ".zip"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(buf.getvalue())
                tmp_name = tmp.name

            task.result = {
                "file_path": tmp_name,
                "filename": filename,
                "media_type": media_type,
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
