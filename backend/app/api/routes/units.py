"""
API routes for unit CRUD operations

Uses SQLAlchemy ORM via unit_repo.
"""

import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.models.unit import Unit
from app.repositories import unit_repo
from app.schemas.materials import MaterialCreate
from app.schemas.unit import (
    QuickCreateRequest,
    QuickCreateResponse,
    UnitCreate,
    UnitList,
    UnitResponse,
    UnitStatus,
    UnitUpdate,
)
from app.schemas.user import UserResponse
from app.services.git_content_service import get_git_service
from app.services.materials_service import materials_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/check-code")
async def check_unit_code(
    code: str = Query(...),
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> dict[str, bool]:
    """Check if a unit with the given code already exists for the current user."""
    exists = unit_repo.unit_exists_by_code(db, owner_id=current_user.id, code=code)
    return {"exists": exists}


@router.get("", response_model=UnitList)
async def get_units(
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: UnitStatus | None = None,
    search: str | None = None,
):
    """
    Get all units for the current user with optional filtering.
    """
    units = unit_repo.search_units(
        db,
        owner_id=current_user.id,
        search=search,
        status=status.value if status else None,
        skip=skip,
        limit=limit,
    )

    return UnitList(units=units, total=len(units))


@router.get("/archived", response_model=UnitList)
async def get_archived_units(
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Get all archived (soft-deleted) units for the current user.
    """
    units = unit_repo.get_archived_units(db, owner_id=current_user.id)
    return UnitList(units=units, total=len(units))


@router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Get a specific unit by ID.
    """
    unit = unit_repo.get_unit_by_id(db, unit_id)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    # Check ownership (admin can access any unit)
    if unit.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    return unit


@router.post("/create", response_model=UnitResponse)
async def create_unit(
    unit_data: UnitCreate,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Create a new unit.
    """
    logger.info("[CREATE_UNIT] === ROUTE HANDLER CALLED ===")
    logger.info(f"[CREATE_UNIT] User: {current_user.email}")
    logger.info(f"[CREATE_UNIT] Unit data received: {unit_data.model_dump()}")

    # Check if unit with same code already exists for this user
    # Handle semester - could be Enum or string depending on serialization
    semester_value = None
    if unit_data.semester:
        semester_value = (
            unit_data.semester.value
            if hasattr(unit_data.semester, "value")
            else str(unit_data.semester)
        )

    if unit_repo.unit_exists_by_code(
        db,
        owner_id=current_user.id,
        code=unit_data.code,
        year=unit_data.year,
        semester=semester_value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit with code {unit_data.code} already exists",
        )

    unit = unit_repo.create_unit(db, data=unit_data, owner_id=current_user.id)
    logger.info(f"[CREATE_UNIT] Unit created: {unit.id}")

    return unit


@router.post("/quick-create", response_model=QuickCreateResponse)
async def quick_create(
    data: QuickCreateRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Quick-create a material with an auto-generated lightweight unit.

    Creates a minimal unit behind the scenes plus a single WeeklyMaterial
    in week 1, then returns the IDs so the frontend can navigate straight
    to the unit page with that week pre-expanded and the user ready to
    edit their new material inline.
    """
    now = datetime.utcnow()
    content_type_value = (
        data.content_type.value
        if hasattr(data.content_type, "value")
        else str(data.content_type)
    )
    content_type_label = content_type_value.replace("_", " ").title()

    # Generate title if not provided
    material_title = data.title or f"{content_type_label} — {now.strftime('%d %b %Y')}"
    unit_title = f"Quick — {content_type_label} ({now.strftime('%d %b')})"

    # Generate unique code: QC-YYMMDDHHMMSS
    code = f"QC-{now.strftime('%y%m%d%H%M%S')}"

    # Create lightweight unit directly
    unit_id = str(uuid.uuid4())
    unit = Unit(
        id=unit_id,
        title=unit_title,
        code=code,
        owner_id=current_user.id,
        created_by_id=current_user.id,
        year=now.year,
        semester="semester_1",
        duration_weeks=1,
        credit_points=0,
        unit_metadata={"quick_create": True},
    )
    db.add(unit)
    db.flush()

    # Create a single WeeklyMaterial in week 1. The content_type selected
    # in the Quick Create modal becomes the material's ``type`` field, so
    # the inline editor opens with the right session format.
    material_data = MaterialCreate(
        week_number=1,
        title=material_title,
        type=content_type_value,
        description=None,
        content_json=None,
        duration_minutes=None,
        file_path=None,
        material_metadata={"quick_create": True},
        category="general",
        order_index=0,
        status="draft",
    )
    material = await materials_service.create_material(
        db=db,
        unit_id=uuid.UUID(unit_id),
        material_data=material_data,
        user_email=current_user.email,
    )

    logger.info(
        f"[QUICK_CREATE] Unit {unit_id} + material {material.id} for {current_user.email}"
    )

    return QuickCreateResponse(
        unit_id=unit_id,
        material_id=str(material.id),
        week_number=1,
        unit_title=unit_title,
        material_title=material_title,
        content_type=content_type_value,
    )


@router.put("/{unit_id}", response_model=UnitResponse)
async def update_unit(
    unit_id: str,
    unit_data: UnitUpdate,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Update an existing unit.
    """
    # Check if unit exists and user owns it
    existing_unit = unit_repo.get_unit_by_id(db, unit_id)

    if not existing_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    if existing_unit.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    unit = unit_repo.update_unit(db, unit_id=unit_id, data=unit_data)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update unit",
        )

    return unit


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    permanent: bool = Query(
        False, description="Permanently delete the unit and its git repo"
    ),
):
    """
    Delete a unit.

    By default (permanent=false), the unit is soft-deleted: marked as archived
    with all data and git history preserved. It can be restored later.

    With permanent=true, the unit and its git repository are irreversibly deleted.
    Permanent deletion is only allowed in LOCAL_MODE or for admin users.
    """
    # Check if unit exists and user owns it
    existing_unit = unit_repo.get_unit_by_id(db, unit_id)

    if not existing_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    if existing_unit.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    if permanent:
        # Hard delete: only allowed in LOCAL_MODE or for admins
        if not settings.LOCAL_MODE and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permanent deletion requires admin privileges",
            )

        # Delete from database (cascades to all related content)
        if not unit_repo.delete_unit(db, unit_id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete unit",
            )

        # Delete the Git repository for this unit (if it exists)
        git_service = get_git_service()
        git_service.delete_unit_repo(unit_id)
        logger.info(
            f"[DELETE_UNIT] Permanently deleted unit {unit_id} and its Git repository"
        )
    else:
        # Soft delete: mark as archived
        if not unit_repo.soft_delete_unit(db, unit_id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to archive unit",
            )
        logger.info(f"[DELETE_UNIT] Soft-deleted (archived) unit {unit_id}")


@router.post("/{unit_id}/restore", response_model=UnitResponse)
async def restore_unit(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Restore a soft-deleted (archived) unit back to draft status.
    """
    existing_unit = unit_repo.get_unit_by_id(db, unit_id)

    if not existing_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    if existing_unit.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    if existing_unit.status != "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit is not archived",
        )

    restored = unit_repo.restore_unit(db, unit_id)
    if not restored:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore unit",
        )

    logger.info(f"[RESTORE_UNIT] Restored unit {unit_id}")
    return restored


@router.post("/{unit_id}/duplicate", response_model=UnitResponse)
async def duplicate_unit(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    new_title: str | None = None,
):
    """
    Duplicate an existing unit.
    """
    # Check if unit exists and user owns it
    existing_unit = unit_repo.get_unit_by_id(db, unit_id)

    if not existing_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    if existing_unit.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    new_unit = unit_repo.duplicate_unit(
        db,
        unit_id=unit_id,
        owner_id=current_user.id,
        new_title=new_title,
    )

    if not new_unit:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate unit",
        )

    return new_unit


@router.delete("/{unit_id}/weeks/{week_number}", response_model=UnitResponse)
async def delete_week(
    unit_id: str,
    week_number: int,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Delete a week from a unit.

    Removes all materials and topics for the given week,
    shifts subsequent weeks down by 1, and decrements duration_weeks.
    """
    existing_unit = unit_repo.get_unit_by_id(db, unit_id)

    if not existing_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    if existing_unit.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    try:
        return await materials_service.delete_week(db, unit_id, week_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
