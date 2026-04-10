"""
Structured material import API — Mode A (single file → existing unit).

Implements the first phase of the structured-import-plan: a user uploads
one PPTX (or in later phases DOCX/PDF/HTML/MD/IPYNB) and gets back a fully
structured WeeklyMaterial with editable content_json, slide breaks, speaker
notes, and embedded images. Replaces the legacy /api/content/upload path
which produces plain-text Content rows with no structure.

Mode B (multi-file zip → existing unit) and Mode C (full course → new
unit) ship in later phases.

Endpoints:

- ``GET  /parsers``                — list registered material parsers
- ``POST /single/preview``          — parse + return preview, no DB write
- ``POST /single/apply``            — parse + persist as a new WeeklyMaterial

Mode A is synchronous because a single file's parse + persist is fast
enough that background-task overhead isn't worth it. Modes B and C will
use the existing ImportTask polling pattern from ``unified_import_service``.
"""

import hashlib
import logging
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api import deps
from app.api.routes.materials import (
    _images_dir_for_material,
    _sanitize_filename,
)
from app.models.unit import Unit
from app.models.user import User
from app.models.weekly_material import WeeklyMaterial
from app.schemas.base import CamelModel
from app.schemas.materials import MaterialCreate
from app.services.git_content_service import get_git_service
from app.services.material_parsers import (
    autodetect,
    get_default_for_format,
    get_parser,
    list_parsers,
)
from app.services.material_parsers.base import (
    ExtractedImage,
    MaterialParseResult,
)
from app.services.materials_service import materials_service

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Response schemas
# =============================================================================


class ParserInfo(CamelModel):
    """Metadata for a registered material parser."""

    id: str
    display_name: str
    description: str
    supported_formats: list[str]
    requires_ai: bool
    is_default: bool


class ParserListResponse(CamelModel):
    parsers: list[ParserInfo]


class ImportPreviewResponse(CamelModel):
    """Result of parsing a file without writing anything to the database."""

    parser_used: str
    title: str
    content_json: dict[str, Any]
    image_count: int
    warnings: list[str]
    confidence: float


class ImportApplyResponse(CamelModel):
    """Result of applying a parsed file as a new WeeklyMaterial."""

    material_id: str
    unit_id: str
    week_number: int
    title: str
    parser_used: str
    image_count: int
    warnings: list[str]


# =============================================================================
# Helpers
# =============================================================================


_ALLOWED_EXTENSIONS = {"pptx"}
"""File extensions accepted by Mode A in this phase. Expands as more
parsers ship (per docs/structured-import-plan.md Phase 2)."""


def _normalise_extension(filename: str) -> str:
    """Return the lowercased extension without the leading dot."""
    return Path(filename).suffix.lower().lstrip(".")


async def _read_and_parse(
    file: UploadFile,
    parser_id_override: str | None,
) -> tuple[MaterialParseResult, bytes]:
    """Read the uploaded file, dispatch to a parser, return the result.

    Returns the parsed result and the raw bytes (so callers can persist
    images without re-reading the upload). Raises HTTPException with
    appropriate status codes for client errors.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    ext = _normalise_extension(file.filename)
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported format '.{ext}'. This phase supports: "
                f"{', '.join(sorted(_ALLOWED_EXTENSIONS))}. "
                "Other formats will be added in subsequent phases."
            ),
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Resolve parser: explicit override → auto-detect → format default
    if parser_id_override:
        try:
            parser = get_parser(parser_id_override)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
    else:
        autodetected = autodetect(file_bytes, file.filename)
        if autodetected:
            parser = get_parser(autodetected)
        else:
            try:
                parser = get_default_for_format(ext)
            except KeyError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

    try:
        result = await parser.parse(file_bytes, file.filename)
    except RuntimeError as exc:
        # Parser-internal failures (e.g. python-pptx not installed) bubble
        # up as 500s — they're install/config issues, not user errors
        logger.exception("Material parser failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parser failed: {exc}",
        ) from exc
    except Exception as exc:
        # Anything else from the parser is treated as a malformed file
        logger.exception("Material parser raised on file %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse file: {exc}",
        ) from exc

    return result, file_bytes


def _verify_unit_access(db: Session, unit_id: UUID, user: User) -> Unit:
    """Confirm the unit exists and the user owns it (or is admin).

    Mirrors the access pattern used by the legacy /api/content/upload route.
    """
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit or (unit.owner_id != user.id and user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )
    return unit


def _persist_images(
    *,
    images: list[ExtractedImage],
    unit_id: str,
    material: WeeklyMaterial,
    user_email: str,
) -> dict[str, str]:
    """Write extracted images to git and return a {original_filename: url} map.

    The map lets the caller rewrite content_json image src values from
    the parser's placeholder filenames to canonical image-serving URLs.

    Filename collisions inside the same material's image directory are
    resolved with an 8-char SHA256 suffix (matching ``upload_material_image``
    behaviour for consistency).
    """
    if not images:
        return {}

    git = get_git_service()
    images_dir = _images_dir_for_material(material)
    existing = set(git.list_directory(unit_id, images_dir))
    rewrites: dict[str, str] = {}

    for image in images:
        original_name = image.filename
        safe_name = _sanitize_filename(original_name)

        if safe_name in existing:
            stem = Path(safe_name).stem
            ext = Path(safe_name).suffix
            content_hash = hashlib.sha256(image.data).hexdigest()[:8]
            safe_name = f"{stem}-{content_hash}{ext}"

        existing.add(safe_name)
        image_path = f"{images_dir}/{safe_name}"

        git.save_binary(
            unit_id=unit_id,
            path=image_path,
            data=image.data,
            user_email=user_email,
            message=f"Imported image {safe_name} for {material.title}",
        )

        url = (
            f"/api/materials/units/{unit_id}/materials/{material.id}"
            f"/images/{safe_name}"
        )
        rewrites[original_name] = url

    return rewrites


def _rewrite_image_src(
    content_json: dict[str, Any], rewrites: dict[str, str]
) -> dict[str, Any]:
    """Return a copy of content_json with image src placeholders replaced.

    The parser emits image nodes with ``src`` set to a bare filename
    (e.g. ``"slide-1-0.png"``). After persistence we know the canonical
    URL and walk the tree replacing each match. The original content_json
    is not mutated.
    """
    if not rewrites:
        return content_json

    def _walk(node: dict[str, Any]) -> dict[str, Any]:
        new_node: dict[str, Any] = dict(node)
        if node.get("type") == "image":
            attrs = dict(node.get("attrs", {}))
            src = attrs.get("src", "")
            if src in rewrites:
                attrs["src"] = rewrites[src]
                new_node["attrs"] = attrs
        if "content" in node and isinstance(node["content"], list):
            new_node["content"] = [_walk(child) for child in node["content"]]
        return new_node

    return _walk(content_json)


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/parsers", response_model=ParserListResponse)
async def list_material_parsers(
    file_format: Annotated[
        str | None,
        Query(
            alias="format",
            description="Optional file extension (without dot) to filter by",
        ),
    ] = None,
) -> ParserListResponse:
    """List registered material parsers, optionally filtered by format."""
    raw = list_parsers(file_format)
    parsers: list[ParserInfo] = []
    for p in raw:
        formats_obj = p["supportedFormats"]
        formats_list: list[str] = (
            [str(f) for f in formats_obj]  # type: ignore[union-attr]
            if isinstance(formats_obj, (list, tuple))
            else []
        )
        parsers.append(
            ParserInfo(
                id=str(p["id"]),
                display_name=str(p["displayName"]),
                description=str(p["description"]),
                supported_formats=formats_list,
                requires_ai=bool(p["requiresAi"]),
                is_default=bool(p["isDefault"]),
            )
        )
    return ParserListResponse(parsers=parsers)


@router.post("/single/preview", response_model=ImportPreviewResponse)
async def preview_single_material(
    file: Annotated[UploadFile, File()],
    unit_id: Annotated[UUID, Form()],
    parser_id: Annotated[str | None, Form()] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> ImportPreviewResponse:
    """Parse an uploaded file and return a preview without persisting.

    The user reviews the preview, optionally adjusts target week / category,
    then calls ``/single/apply`` to commit. Image bytes are not persisted
    here — the apply step does that.
    """
    _verify_unit_access(db, unit_id, current_user)
    result, _bytes = await _read_and_parse(file, parser_id)

    return ImportPreviewResponse(
        parser_used=result.parser_used,
        title=result.title or "Untitled",
        content_json=result.content_json,
        image_count=len(result.images),
        warnings=result.warnings,
        confidence=result.confidence,
    )


@router.post("/single/apply", response_model=ImportApplyResponse)
async def apply_single_material(
    file: Annotated[UploadFile, File()],
    unit_id: Annotated[UUID, Form()],
    week_number: Annotated[int, Form(ge=1, le=52)],
    parser_id: Annotated[str | None, Form()] = None,
    title_override: Annotated[str | None, Form()] = None,
    category: Annotated[str, Form()] = "general",
    material_type: Annotated[str, Form(alias="type")] = "lecture",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> ImportApplyResponse:
    """Parse an uploaded file and create a new WeeklyMaterial.

    Persistence flow:
        1. Verify unit access
        2. Parse the file (no DB writes, no git writes)
        3. Create the WeeklyMaterial row (now we have material_id)
        4. Persist extracted images to git under the material's images dir
        5. Rewrite content_json image src placeholders to canonical URLs
        6. Save the rewritten content_json on the material
    """
    _verify_unit_access(db, unit_id, current_user)
    parsed, _file_bytes = await _read_and_parse(file, parser_id)

    final_title = title_override or parsed.title or "Untitled"

    # Step 1: create the material with empty description and no content_json
    # yet — we need the material id before we can persist images and
    # rewrite the image src URLs.
    material_create = MaterialCreate(
        week_number=week_number,
        title=final_title,
        type=material_type,
        category=category,
        description=None,
        content_json=None,
        order_index=0,  # service computes the real next index
        status="draft",
        duration_minutes=None,
        file_path=None,
        material_metadata=None,
    )
    material = await materials_service.create_material(
        db=db,
        unit_id=unit_id,
        material_data=material_create,
        user_email=current_user.email,
    )

    # Step 2: persist images and build the placeholder→URL rewrite map
    try:
        rewrites = _persist_images(
            images=parsed.images,
            unit_id=str(unit_id),
            material=material,
            user_email=current_user.email,
        )
    except Exception:
        logger.exception(
            "Failed to persist images for imported material %s", material.id
        )
        # The material exists but its images don't — surface as a 500
        # rather than leaving the user with a half-broken import. Caller
        # can delete the material and retry.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist extracted images. Material was created "
            "but images are missing — delete the material and retry.",
        ) from None

    # Step 3: rewrite image src placeholders and save content_json
    final_content_json = _rewrite_image_src(parsed.content_json, rewrites)
    material.content_json = final_content_json
    db.commit()
    db.refresh(material)

    return ImportApplyResponse(
        material_id=str(material.id),
        unit_id=str(material.unit_id),
        week_number=material.week_number,
        title=material.title,
        parser_used=parsed.parser_used,
        image_count=len(parsed.images),
        warnings=parsed.warnings,
    )
