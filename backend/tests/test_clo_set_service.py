"""Tests for CLOSetService — real in-memory SQLite, no mocks except LLM."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.clo_set import CLOItem, CLOSet
from app.models.learning_outcome import OutcomeType, UnitLearningOutcome
from app.models.unit import Unit
from app.models.user import User
from app.schemas.clo_sets import (
    CLOItemCreate,
    CLOItemUpdate,
    CLOSetCreate,
    CLOSetUpdate,
)
from app.services.clo_set_service import clo_set_service


# ── helpers ──────────────────────────────────────────────────


def make_set(db: Session, user: User, name: str = "BCS") -> CLOSet:
    return clo_set_service.create_clo_set(
        db, uuid.UUID(user.id), CLOSetCreate(name=name, program_code="BCS")
    )


def make_item(db: Session, clo_set: CLOSet, code: str = "CLO1") -> CLOItem:
    item = clo_set_service.add_clo_item(
        db,
        uuid.UUID(clo_set.id),
        uuid.UUID(clo_set.user_id),
        CLOItemCreate(code=code, description=f"Desc for {code}", order_index=0),
    )
    assert item is not None
    return item


def make_ulo(
    db: Session, unit: Unit, user: User, code: str = "ULO1"
) -> UnitLearningOutcome:
    ulo = UnitLearningOutcome(
        id=str(uuid.uuid4()),
        unit_id=unit.id,
        outcome_type=OutcomeType.ULO,
        outcome_code=code,
        outcome_text=f"Students will be able to {code}",
        bloom_level="apply",
        sequence_order=0,
        created_by_id=user.id,
        is_active=True,
        is_measurable=True,
    )
    db.add(ulo)
    db.commit()
    db.refresh(ulo)
    return ulo


# ── CLO Set CRUD ──────────────────────────────────────────────


def test_create_clo_set(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    assert clo_set.id is not None
    assert clo_set.name == "BCS"
    assert clo_set.user_id == test_user.id


def test_list_clo_sets_only_own(test_db: Session, test_user: User) -> None:
    other_user = User(
        id=str(uuid.uuid4()),
        email="other@example.com",
        password_hash="x",
        name="Other",
        role="lecturer",
        is_verified=True,
        is_active=True,
    )
    test_db.add(other_user)
    test_db.commit()

    make_set(test_db, test_user, "Mine")
    make_set(test_db, other_user, "Theirs")

    sets = clo_set_service.list_clo_sets(test_db, uuid.UUID(test_user.id))
    assert len(sets) == 1
    assert sets[0].name == "Mine"


def test_update_clo_set(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    updated = clo_set_service.update_clo_set(
        test_db,
        uuid.UUID(clo_set.id),
        uuid.UUID(test_user.id),
        CLOSetUpdate(name="Updated BCS"),
    )
    assert updated is not None
    assert updated.name == "Updated BCS"


def test_delete_clo_set(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    result = clo_set_service.delete_clo_set(
        test_db, uuid.UUID(clo_set.id), uuid.UUID(test_user.id)
    )
    assert result is True
    assert (
        clo_set_service.get_clo_set(
            test_db, uuid.UUID(clo_set.id), uuid.UUID(test_user.id)
        )
        is None
    )


# ── CLO Items ─────────────────────────────────────────────────


def test_add_clo_item(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    item = make_item(test_db, clo_set, "CLO1")
    assert item.code == "CLO1"
    assert item.clo_set_id == clo_set.id


def test_update_clo_item(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    item = make_item(test_db, clo_set, "CLO1")
    updated = clo_set_service.update_clo_item(
        test_db, uuid.UUID(item.id), CLOItemUpdate(description="Updated desc")
    )
    assert updated is not None
    assert updated.description == "Updated desc"


def test_delete_clo_item(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    item = make_item(test_db, clo_set, "CLO1")
    result = clo_set_service.delete_clo_item(test_db, uuid.UUID(item.id))
    assert result is True


def test_reorder_clo_items(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    item1 = make_item(test_db, clo_set, "CLO1")
    item2 = make_item(test_db, clo_set, "CLO2")
    reordered = clo_set_service.reorder_clo_items(
        test_db,
        uuid.UUID(clo_set.id),
        uuid.UUID(test_user.id),
        [item2.id, item1.id],
    )
    assert reordered[0].code == "CLO2"
    assert reordered[1].code == "CLO1"


def test_delete_set_cascades_to_items(test_db: Session, test_user: User) -> None:
    clo_set = make_set(test_db, test_user)
    item = make_item(test_db, clo_set, "CLO1")
    item_id = item.id
    clo_set_service.delete_clo_set(
        test_db, uuid.UUID(clo_set.id), uuid.UUID(test_user.id)
    )
    from sqlalchemy import select as sa_select

    result = test_db.execute(
        sa_select(CLOItem).where(CLOItem.id == item_id)
    ).scalar_one_or_none()
    assert result is None


# ── Unit assignments ──────────────────────────────────────────


def test_assign_and_unassign_clo_set(
    test_db: Session, test_user: User, test_unit: Unit
) -> None:
    clo_set = make_set(test_db, test_user)
    assignment = clo_set_service.assign_clo_set(
        test_db, uuid.UUID(test_unit.id), uuid.UUID(clo_set.id)
    )
    assert assignment is not None

    sets = clo_set_service.get_unit_clo_sets(test_db, uuid.UUID(test_unit.id))
    assert len(sets) == 1
    assert sets[0].id == clo_set.id

    clo_set_service.unassign_clo_set(
        test_db, uuid.UUID(test_unit.id), uuid.UUID(clo_set.id)
    )
    sets = clo_set_service.get_unit_clo_sets(test_db, uuid.UUID(test_unit.id))
    assert len(sets) == 0


def test_assign_clo_set_duplicate_is_idempotent(
    test_db: Session, test_user: User, test_unit: Unit
) -> None:
    clo_set = make_set(test_db, test_user)
    a1 = clo_set_service.assign_clo_set(
        test_db, uuid.UUID(test_unit.id), uuid.UUID(clo_set.id)
    )
    a2 = clo_set_service.assign_clo_set(
        test_db, uuid.UUID(test_unit.id), uuid.UUID(clo_set.id)
    )
    assert a1 is not None
    assert a2 is not None
    assert a1.id == a2.id


# ── ULO → CLO mappings ────────────────────────────────────────


def test_set_ulo_clo_mappings(
    test_db: Session, test_user: User, test_unit: Unit
) -> None:
    clo_set = make_set(test_db, test_user)
    item1 = make_item(test_db, clo_set, "CLO1")
    item2 = make_item(test_db, clo_set, "CLO2")
    ulo = make_ulo(test_db, test_unit, test_user)

    mappings = clo_set_service.set_ulo_clo_mappings(
        test_db, uuid.UUID(ulo.id), [item1.id, item2.id]
    )
    assert len(mappings) == 2

    # Replace: should only have item1 now
    mappings = clo_set_service.set_ulo_clo_mappings(
        test_db, uuid.UUID(ulo.id), [item1.id]
    )
    assert len(mappings) == 1
    assert mappings[0].clo_item_id == item1.id


def test_get_ulo_clo_mappings(
    test_db: Session, test_user: User, test_unit: Unit
) -> None:
    clo_set = make_set(test_db, test_user)
    item = make_item(test_db, clo_set, "CLO1")
    ulo = make_ulo(test_db, test_unit, test_user)
    clo_set_service.set_ulo_clo_mappings(test_db, uuid.UUID(ulo.id), [item.id])

    fetched = clo_set_service.get_ulo_clo_mappings(test_db, uuid.UUID(ulo.id))
    assert len(fetched) == 1
    assert fetched[0].clo_item_id == item.id
