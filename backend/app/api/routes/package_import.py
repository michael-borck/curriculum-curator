"""
API routes for importing IMSCC / SCORM packages.

Legacy endpoints:
  POST /api/import/package/analyze  — preview a package without saving
  POST /api/import/package/create   — import and create all records

Unified endpoints (handles ALL file types inside ZIPs):
  POST /api/import/unified/analyze       — upload ZIP, get full file preview
  POST /api/import/unified/apply         — apply import (returns task_id)
  GET  /api/import/unified/status/{id}   — poll background progress
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.package_import import (
    ImportPreview,
    ImportResult,
    UnifiedImportPreview,
    UnifiedImportResult,
)
from app.services.import_task_store import get_task
from app.services.package_import_service import (
    PackageImportError,
    package_import_service,
)
from app.services.unified_import_service import unified_import_service

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB (real Blackboard exports can be large)
ALLOWED_EXTENSIONS = {".imscc", ".zip"}


def _validate_upload(file: UploadFile) -> None:
    """Validate uploaded file extension."""
    filename = file.filename or ""
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Accepted: .imscc, .zip",
        )


@router.post("/import/package/analyze", response_model=ImportPreview)
async def analyze_package(
    file: UploadFile,
    _current_user: User = Depends(deps.get_current_active_user),
) -> ImportPreview:
    """Analyze an IMSCC or SCORM package and return a preview."""
    _validate_upload(file)

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 500 MB limit.")

    try:
        return package_import_service.analyze_package(contents)
    except PackageImportError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error analysing package")
        raise HTTPException(
            status_code=500, detail=f"Failed to analyse package: {e}"
        ) from e


@router.post("/import/package/create", response_model=ImportResult)
async def create_from_package(
    file: UploadFile,
    unit_code: str | None = Query(default=None, description="Override the unit code"),
    unit_title: str | None = Query(default=None, description="Override the unit title"),
    pedagogy_type: str | None = Query(
        default=None, description="Pedagogy type (for generic imports)"
    ),
    difficulty_level: str | None = Query(
        default=None, description="Difficulty level (for generic imports)"
    ),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> ImportResult:
    """Import an IMSCC or SCORM package, creating all database records."""
    _validate_upload(file)

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 500 MB limit.")

    try:
        return package_import_service.create_unit_from_package(
            zip_bytes=contents,
            current_user_id=str(current_user.id),
            db=db,
            unit_code_override=unit_code,
            unit_title_override=unit_title,
            pedagogy_type=pedagogy_type,
            difficulty_level=difficulty_level,
        )
    except PackageImportError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error importing package")
        raise HTTPException(
            status_code=500, detail=f"Failed to import package: {e}"
        ) from e


# ---------------------------------------------------------------------------
# Unified import endpoints
# ---------------------------------------------------------------------------


@router.post("/import/unified/analyze", response_model=UnifiedImportPreview)
async def unified_analyze(
    file: UploadFile,
    _current_user: User = Depends(deps.get_current_active_user),
) -> UnifiedImportPreview:
    """Analyze any ZIP (IMSCC, SCORM, or plain) and preview ALL files."""
    _validate_upload(file)

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 500 MB limit.")

    try:
        return unified_import_service.analyze(contents)
    except PackageImportError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in unified analyze")
        raise HTTPException(
            status_code=500, detail=f"Failed to analyse package: {e}"
        ) from e


@router.post("/import/unified/apply", response_model=UnifiedImportResult)
async def unified_apply(
    file: UploadFile,
    unit_code: str = Query(default="", description="Unit code"),
    unit_title: str = Query(default="", description="Unit title"),
    duration_weeks: int = Query(default=12, description="Duration in weeks"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> UnifiedImportResult:
    """Apply a unified import. Returns a task_id for progress polling."""
    _validate_upload(file)

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 500 MB limit.")

    try:
        return unified_import_service.apply(
            contents,
            user_id=str(current_user.id),
            user_email=current_user.email,
            db=db,
            unit_code=unit_code,
            unit_title=unit_title,
            duration_weeks=duration_weeks,
        )
    except PackageImportError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in unified apply")
        raise HTTPException(
            status_code=500, detail=f"Failed to start import: {e}"
        ) from e


class ImportTaskStatus(BaseModel):
    """Progress snapshot for a running import task."""

    task_id: str
    status: str
    total_files: int
    processed_files: int
    current_file: str | None
    unit_id: str | None
    unit_code: str | None
    unit_title: str | None
    errors: list[str]
    skipped_items: list[dict[str, str]]


@router.get("/import/unified/status/{task_id}", response_model=ImportTaskStatus)
async def unified_status(
    task_id: str,
    _current_user: User = Depends(deps.get_current_active_user),
) -> ImportTaskStatus:
    """Poll progress of a background import task."""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found or expired.")
    return ImportTaskStatus(
        task_id=task.task_id,
        status=task.status,
        total_files=task.total_files,
        processed_files=task.processed_files,
        current_file=task.current_file,
        unit_id=task.unit_id,
        unit_code=task.unit_code,
        unit_title=task.unit_title,
        errors=task.errors,
        skipped_items=task.skipped_items,
    )
