"""
Unit repository - database operations for units

Handles all unit-related database queries using SQLAlchemy ORM.
"""

import uuid
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.unit import Unit
from app.schemas.unit import UnitCreate, UnitResponse, UnitUpdate


def _get_enum_value(value) -> str | None:
    """Safely get the value from an Enum or return the string as-is"""
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def _unit_to_response(unit: Unit) -> UnitResponse:
    """Convert Unit model to UnitResponse schema"""
    return UnitResponse(
        id=str(unit.id),
        title=unit.title,
        code=unit.code,
        description=unit.description,
        owner_id=str(unit.owner_id),
        status=unit.status,
        pedagogy_type=unit.pedagogy_type,
        difficulty_level=unit.difficulty_level,
        year=unit.year,
        semester=unit.semester,
        duration_weeks=unit.duration_weeks,
        unit_metadata=unit.unit_metadata,
        created_at=unit.created_at,
        updated_at=unit.updated_at,
    )


def create_unit(db: Session, data: UnitCreate, owner_id: str) -> UnitResponse:
    """Create a new unit"""
    # Handle year requirement - use current year if not provided
    year = data.year if data.year else datetime.utcnow().year

    unit = Unit(
        id=str(uuid.uuid4()),
        title=data.title,
        code=data.code,
        description=data.description,
        owner_id=owner_id,
        created_by_id=owner_id,
        pedagogy_type=_get_enum_value(data.pedagogy_type) or "inquiry-based",
        difficulty_level=_get_enum_value(data.difficulty_level) or "intermediate",
        year=year,
        semester=_get_enum_value(data.semester) or "semester_1",
        duration_weeks=data.duration_weeks or 12,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return _unit_to_response(unit)


def get_unit_by_id(db: Session, unit_id: str) -> UnitResponse | None:
    """Get unit by ID"""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    return _unit_to_response(unit) if unit else None


def get_units_by_owner(
    db: Session, owner_id: str, status: str | None = None
) -> list[UnitResponse]:
    """Get all units for an owner, optionally filtered by status.

    By default, archived units are excluded. Pass status="archived" to
    retrieve only archived units.
    """
    query = db.query(Unit).filter(Unit.owner_id == owner_id)

    if status:
        query = query.filter(Unit.status == status)
    else:
        query = query.filter(Unit.status != "archived")

    units = query.order_by(Unit.created_at.desc()).all()
    return [_unit_to_response(unit) for unit in units]


def update_unit(db: Session, unit_id: str, data: UnitUpdate) -> UnitResponse | None:
    """Update a unit"""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        return None

    # Update non-None values
    for key, value in data.model_dump().items():
        if value is not None:
            # Handle enum values
            actual_value = _get_enum_value(value) if hasattr(value, "value") else value
            if hasattr(unit, key):
                setattr(unit, key, actual_value)

    unit.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(unit)
    return _unit_to_response(unit)


def delete_unit(db: Session, unit_id: str) -> bool:
    """Delete a unit (cascades to content)"""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        return False

    db.delete(unit)
    db.commit()
    return True


def unit_exists(db: Session, unit_id: str) -> bool:
    """Check if unit exists"""
    return db.query(Unit).filter(Unit.id == unit_id).first() is not None


def is_owner(db: Session, unit_id: str, user_id: str) -> bool:
    """Check if user is the owner of the unit"""
    return (
        db.query(Unit).filter(Unit.id == unit_id, Unit.owner_id == user_id).first()
        is not None
    )


def get_unit_count_by_owner(db: Session, owner_id: str) -> int:
    """Get count of units for an owner"""
    return db.query(Unit).filter(Unit.owner_id == owner_id).count()


def unit_exists_by_code(
    db: Session,
    owner_id: str,
    code: str,
    year: int | None = None,
    semester: str | None = None,
) -> bool:
    """Check if a unit with given code already exists for this owner"""
    query = db.query(Unit).filter(Unit.owner_id == owner_id, Unit.code == code)

    if year and semester:
        query = query.filter(Unit.year == year, Unit.semester == semester)

    return query.first() is not None


def soft_delete_unit(db: Session, unit_id: str) -> bool:
    """Soft-delete a unit by setting status to archived."""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        return False

    unit.status = "archived"
    unit.archived_at = datetime.utcnow()
    db.commit()
    return True


def restore_unit(db: Session, unit_id: str) -> UnitResponse | None:
    """Restore a soft-deleted (archived) unit back to draft status."""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit or unit.status != "archived":
        return None

    unit.status = "draft"
    unit.archived_at = None
    unit.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(unit)
    return _unit_to_response(unit)


def get_archived_units(db: Session, owner_id: str) -> list[UnitResponse]:
    """Get all archived units for an owner."""
    units = (
        db.query(Unit)
        .filter(Unit.owner_id == owner_id, Unit.status == "archived")
        .order_by(Unit.archived_at.desc())
        .all()
    )
    return [_unit_to_response(unit) for unit in units]


def search_units(
    db: Session,
    owner_id: str,
    search: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[UnitResponse]:
    """Search units with optional filters.

    By default, archived units are excluded. Pass status="archived" to
    retrieve only archived units.
    """
    query = db.query(Unit).filter(Unit.owner_id == owner_id)

    if status:
        query = query.filter(Unit.status == status)
    else:
        query = query.filter(Unit.status != "archived")

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Unit.title.ilike(search_term),
                Unit.code.ilike(search_term),
                Unit.description.ilike(search_term),
            )
        )

    units = query.order_by(Unit.created_at.desc()).offset(skip).limit(limit).all()
    return [_unit_to_response(unit) for unit in units]


def duplicate_unit(
    db: Session,
    unit_id: str,
    owner_id: str,
    new_title: str | None = None,
) -> UnitResponse | None:
    """Duplicate a unit with a new ID"""
    original = db.query(Unit).filter(Unit.id == unit_id).first()
    if not original:
        return None

    title = new_title or f"{original.title} (Copy)"

    new_unit = Unit(
        id=str(uuid.uuid4()),
        title=title,
        code=original.code,
        description=original.description,
        owner_id=owner_id,
        created_by_id=owner_id,
        status="draft",  # Always start as draft
        pedagogy_type=original.pedagogy_type,
        difficulty_level=original.difficulty_level,
        year=original.year,
        semester=original.semester,
        duration_weeks=original.duration_weeks,
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    return _unit_to_response(new_unit)
