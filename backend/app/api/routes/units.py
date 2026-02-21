"""
API routes for unit CRUD operations

Uses SQLAlchemy ORM via unit_repo.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.repositories import unit_repo
from app.schemas.unit import (
    UnitCreate,
    UnitList,
    UnitResponse,
    UnitStatus,
    UnitUpdate,
)
from app.schemas.user import UserResponse
from app.services.git_content_service import get_git_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/test")
async def test_units_router():
    """Test endpoint to verify router is working"""
    return {"message": "Units router is working!", "status": "OK"}


@router.post("/test-post")
async def test_post_endpoint():
    """Dead simple POST test - no auth, no validation, nothing"""
    logger.info("[TEST-POST] This endpoint was called!")
    return {"message": "POST works!", "status": "OK"}


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
