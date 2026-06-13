"""
Export preview endpoints — resolved export plans for the export UIs.

GET /units/{unit_id}/export/preview         (Export Dialog)
GET /materials/{material_id}/export/preview (per-material download menu)
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_user_material,
    get_user_unit,
)
from app.models.weekly_material import WeeklyMaterial
from app.schemas.export_preview import (
    ExportPreviewResponse,
    MaterialExportPreview,
)
from app.schemas.unit import UnitResponse
from app.schemas.user import UserResponse
from app.services.format_resolver import (
    TARGETS_FOR_CONTENT_TYPE,
    detect_content_types,
    resolve_targets_for_material,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/units/{unit_id}/export/preview",
    response_model=ExportPreviewResponse,
)
async def export_preview(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> ExportPreviewResponse:
    """Return resolved export plan for all materials in a unit."""
    materials = (
        db.query(WeeklyMaterial)
        .filter(WeeklyMaterial.unit_id == unit.id)
        .order_by(WeeklyMaterial.week_number, WeeklyMaterial.order_index)
        .all()
    )

    # Level 2: user defaults from teaching_preferences
    prefs: dict[str, Any] = current_user.teaching_preferences or {}
    user_defaults: dict[str, list[str]] | None = prefs.get("export_defaults")

    previews: list[MaterialExportPreview] = []
    for mat in materials:
        content_types = detect_content_types(mat.content_json)
        resolved = resolve_targets_for_material(
            content_types,
            mat.export_targets_list,
            user_defaults,
        )
        available = {ct: TARGETS_FOR_CONTENT_TYPE.get(ct, []) for ct in content_types}
        previews.append(
            MaterialExportPreview(
                material_id=str(mat.id),
                title=str(mat.title),
                week_number=mat.week_number,
                category=str(mat.category),
                content_types=content_types,
                resolved_targets=resolved,
                available_targets=available,
            )
        )

    return ExportPreviewResponse(materials=previews)


@router.get(
    "/materials/{material_id}/export/preview",
    response_model=MaterialExportPreview,
)
async def material_export_preview(
    material: Annotated[WeeklyMaterial, Depends(get_user_material)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> MaterialExportPreview:
    """Return the resolved export plan for one material (download menu)."""
    prefs: dict[str, Any] = current_user.teaching_preferences or {}
    user_defaults: dict[str, list[str]] | None = prefs.get("export_defaults")

    content_types = detect_content_types(material.content_json)
    resolved = resolve_targets_for_material(
        content_types,
        material.export_targets_list,
        user_defaults,
    )
    return MaterialExportPreview(
        material_id=str(material.id),
        title=str(material.title),
        week_number=material.week_number,
        category=str(material.category),
        content_types=content_types,
        resolved_targets=resolved,
        available_targets={
            ct: TARGETS_FOR_CONTENT_TYPE.get(ct, []) for ct in content_types
        },
    )
