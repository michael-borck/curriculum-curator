"""
API endpoints for managing user export templates (PPTX/DOCX reference documents).

Upload once in Settings, used automatically on all PPTX/DOCX exports via
Pandoc's --reference-doc flag.
"""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.schemas.user import UserResponse
from app.services.template_storage import (
    get_export_templates,
    save_export_templates,
    user_templates_dir,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class TemplateInfo(BaseModel):
    id: str
    filename: str
    format: str
    uploaded_at: str
    is_default: bool


class TemplateListResponse(BaseModel):
    templates: list[TemplateInfo]
    defaults: dict[str, str | None]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/upload", response_model=TemplateInfo, status_code=status.HTTP_201_CREATED
)
async def upload_template(
    file: UploadFile,
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TemplateInfo:
    """Upload a PPTX or DOCX reference template."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.TEMPLATE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.TEMPLATE_EXTENSIONS)}",
        )

    # Read and check size
    data = await file.read()
    if len(data) > settings.TEMPLATE_MAX_SIZE:
        max_mb = settings.TEMPLATE_MAX_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_mb:.0f} MB.",
        )

    # Save to disk
    template_id = str(uuid.uuid4())
    user_dir = user_templates_dir(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    dest = user_dir / f"{template_id}{ext}"
    dest.write_bytes(data)

    fmt = ext.lstrip(".")
    now = datetime.now(tz=UTC).isoformat()

    # Update teaching_preferences metadata
    et = get_export_templates(current_user.teaching_preferences)
    templates: list[dict[str, str]] = et.get("templates", [])
    defaults: dict[str, str | None] = et.get("defaults", {"pptx": None, "docx": None})

    entry = {
        "id": template_id,
        "filename": file.filename,
        "format": fmt,
        "uploaded_at": now,
    }
    templates.append(entry)

    # Auto-set as default if none exists for this format
    if not defaults.get(fmt):
        defaults[fmt] = template_id

    et["templates"] = templates
    et["defaults"] = defaults
    save_export_templates(db, current_user.id, current_user.teaching_preferences, et)

    return TemplateInfo(
        id=template_id,
        filename=file.filename,
        format=fmt,
        uploaded_at=now,
        is_default=defaults.get(fmt) == template_id,
    )


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> TemplateListResponse:
    """List all uploaded templates for the current user."""
    et = get_export_templates(current_user.teaching_preferences)
    templates = et.get("templates", [])
    defaults: dict[str, str | None] = et.get("defaults", {"pptx": None, "docx": None})

    items = [
        TemplateInfo(
            id=t["id"],
            filename=t["filename"],
            format=t["format"],
            uploaded_at=t["uploaded_at"],
            is_default=defaults.get(t["format"]) == t["id"],
        )
        for t in templates
    ]

    return TemplateListResponse(templates=items, defaults=defaults)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete an uploaded template."""
    et = get_export_templates(current_user.teaching_preferences)
    templates: list[dict[str, str]] = et.get("templates", [])
    defaults: dict[str, str | None] = et.get("defaults", {"pptx": None, "docx": None})

    target = next((t for t in templates if t["id"] == template_id), None)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Remove file from disk
    fmt = target["format"]
    file_path = user_templates_dir(current_user.id) / f"{template_id}.{fmt}"
    if file_path.exists():
        file_path.unlink()

    # Remove from metadata
    templates = [t for t in templates if t["id"] != template_id]
    if defaults.get(fmt) == template_id:
        defaults[fmt] = None

    et["templates"] = templates
    et["defaults"] = defaults
    save_export_templates(db, current_user.id, current_user.teaching_preferences, et)


@router.put("/{template_id}/default", response_model=TemplateInfo)
async def set_default_template(
    template_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TemplateInfo:
    """Set a template as the default for its format."""
    et = get_export_templates(current_user.teaching_preferences)
    templates: list[dict[str, str]] = et.get("templates", [])
    defaults: dict[str, str | None] = et.get("defaults", {"pptx": None, "docx": None})

    target = next((t for t in templates if t["id"] == template_id), None)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    defaults[target["format"]] = template_id
    et["defaults"] = defaults
    save_export_templates(db, current_user.id, current_user.teaching_preferences, et)

    return TemplateInfo(
        id=target["id"],
        filename=target["filename"],
        format=target["format"],
        uploaded_at=target["uploaded_at"],
        is_default=True,
    )
