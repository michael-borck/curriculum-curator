"""
API routes for unit CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.models.unit import DifficultyLevel, PedagogyType, Semester, Unit, UnitStatus
from app.models.user import User
from app.schemas.unit import (
    UnitCreate,
    UnitResponse,
    UnitUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[UnitResponse])
def get_units(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: UnitStatus | None = None,
    search: str | None = None,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all units for the current user with optional filtering
    """
    query = db.query(Unit).filter(Unit.owner_id == current_user.id)

    if status:
        query = query.filter(Unit.status == status.value)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Unit.title.ilike(search_term),
                Unit.code.ilike(search_term),
                Unit.description.ilike(search_term),
            )
        )

    # Apply pagination
    units = query.offset(skip).limit(limit).all()

    # Convert UUIDs to strings for each unit
    for unit in units:
        unit.id = str(unit.id)
        unit.owner_id = str(unit.owner_id)
        unit.created_by_id = str(unit.created_by_id)
        if unit.updated_by_id:
            unit.updated_by_id = str(unit.updated_by_id)

    return units


@router.get("/{unit_id}", response_model=UnitResponse)
def get_unit(
    unit_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific unit by ID
    """
    unit = (
        db.query(Unit)
        .filter(Unit.id == unit_id, Unit.owner_id == current_user.id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    # Convert UUIDs to strings for response
    unit.id = str(unit.id)
    unit.owner_id = str(unit.owner_id)
    unit.created_by_id = str(unit.created_by_id)
    if unit.updated_by_id:
        unit.updated_by_id = str(unit.updated_by_id)

    return unit


@router.post("/", response_model=UnitResponse)
def create_unit(
    unit_data: UnitCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new unit
    """
    # Check if unit with same code, year, and semester already exists for this user
    existing_unit = (
        db.query(Unit)
        .filter(
            Unit.code == unit_data.code,
            Unit.year == unit_data.year,
            Unit.semester == unit_data.semester,
            Unit.owner_id == current_user.id,
        )
        .first()
    )

    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit with code {unit_data.code} already exists for {unit_data.year} {unit_data.semester if unit_data.semester else 'Semester 1'}",
        )

    # Create new unit
    db_unit = Unit(
        title=unit_data.title,
        code=unit_data.code,
        description=unit_data.description,
        year=unit_data.year,
        semester=unit_data.semester
        if unit_data.semester
        else Semester.SEMESTER_1.value,
        status=unit_data.status if unit_data.status else UnitStatus.DRAFT.value,
        pedagogy_type=unit_data.pedagogy_type
        if unit_data.pedagogy_type
        else PedagogyType.INQUIRY_BASED.value,
        difficulty_level=unit_data.difficulty_level
        if unit_data.difficulty_level
        else DifficultyLevel.INTERMEDIATE.value,
        duration_weeks=unit_data.duration_weeks or 12,
        credit_points=unit_data.credit_points or 6,
        prerequisites=unit_data.prerequisites,
        learning_hours=unit_data.learning_hours,
        owner_id=current_user.id,
        created_by_id=current_user.id,
        unit_metadata=unit_data.unit_metadata,
        generation_context=unit_data.generation_context,
    )

    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)

    # Convert UUIDs to strings for response
    db_unit.id = str(db_unit.id)
    db_unit.owner_id = str(db_unit.owner_id)
    db_unit.created_by_id = str(db_unit.created_by_id)
    if db_unit.updated_by_id:
        db_unit.updated_by_id = str(db_unit.updated_by_id)

    return db_unit


@router.put("/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_id: str,
    unit_data: UnitUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing unit
    """
    unit = (
        db.query(Unit)
        .filter(Unit.id == unit_id, Unit.owner_id == current_user.id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    # Update fields if provided
    update_data = unit_data.dict(exclude_unset=True)

    # Enums are already converted to strings by Pydantic CamelModel

    # Track who made the update
    update_data["updated_by_id"] = current_user.id

    for field, value in update_data.items():
        setattr(unit, field, value)

    db.commit()
    db.refresh(unit)

    # Convert UUIDs to strings for response
    unit.id = str(unit.id)
    unit.owner_id = str(unit.owner_id)
    unit.created_by_id = str(unit.created_by_id)
    if unit.updated_by_id:
        unit.updated_by_id = str(unit.updated_by_id)

    return unit


@router.delete("/{unit_id}")
def delete_unit(
    unit_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a unit
    """
    unit = (
        db.query(Unit)
        .filter(Unit.id == unit_id, Unit.owner_id == current_user.id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    db.delete(unit)
    db.commit()

    return {"message": "Unit deleted successfully"}


@router.post("/{unit_id}/duplicate", response_model=UnitResponse)
def duplicate_unit(
    unit_id: str,
    new_code: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Duplicate an existing unit with a new code
    """
    # Get original unit
    original_unit = (
        db.query(Unit)
        .filter(Unit.id == unit_id, Unit.owner_id == current_user.id)
        .first()
    )

    if not original_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    # Check if new code already exists
    existing_unit = (
        db.query(Unit)
        .filter(Unit.code == new_code, Unit.owner_id == current_user.id)
        .first()
    )

    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit with this code already exists",
        )

    # Create duplicate
    db_unit = Unit(
        title=f"{original_unit.title} (Copy)",
        code=new_code,
        description=original_unit.description,
        year=original_unit.year,
        semester=original_unit.semester,
        status=UnitStatus.DRAFT.value,  # Always set to draft for duplicates
        pedagogy_type=original_unit.pedagogy_type,
        difficulty_level=original_unit.difficulty_level,
        duration_weeks=original_unit.duration_weeks,
        credit_points=original_unit.credit_points,
        prerequisites=original_unit.prerequisites,
        learning_hours=original_unit.learning_hours,
        owner_id=current_user.id,
        created_by_id=current_user.id,
        unit_metadata=original_unit.unit_metadata,
        generation_context=original_unit.generation_context,
    )

    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)

    # Convert UUIDs to strings for response
    db_unit.id = str(db_unit.id)
    db_unit.owner_id = str(db_unit.owner_id)
    db_unit.created_by_id = str(db_unit.created_by_id)
    if db_unit.updated_by_id:
        db_unit.updated_by_id = str(db_unit.updated_by_id)

    return db_unit
