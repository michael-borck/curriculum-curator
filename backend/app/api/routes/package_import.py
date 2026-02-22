"""
API routes for importing IMSCC / SCORM packages.

POST /api/import/package/analyze  — preview a package without saving
POST /api/import/package/create   — import and create all records
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.package_import import ImportPreview, ImportResult
from app.services.package_import_service import (
    PackageImportError,
    package_import_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
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
        raise HTTPException(status_code=400, detail="File exceeds 100 MB limit.")

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
        raise HTTPException(status_code=400, detail="File exceeds 100 MB limit.")

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
