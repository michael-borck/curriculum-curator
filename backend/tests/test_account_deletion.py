"""Single-owner account hard delete."""

from __future__ import annotations

import uuid

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.security_log import SecurityLog
from app.models.unit import Unit
from app.models.unit_outline import UnitOutline
from app.models.user import User
from app.models.weekly_material import WeeklyMaterial
from app.services import account_deletion_service
from app.services.account_deletion_service import delete_user_account


def _user(db: Session, email: str) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=get_password_hash("Str0ng-Passw0rd!23"),
        name=email.split("@", maxsplit=1)[0],
        role="lecturer",
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def _unit(db: Session, owner: User, creator: User, code: str) -> Unit:
    unit = Unit(
        id=str(uuid.uuid4()),
        title=f"Unit {code}",
        code=code,
        year=2026,
        semester="semester_1",
        duration_weeks=12,
        owner_id=owner.id,
        created_by_id=creator.id,
    )
    db.add(unit)
    db.commit()
    return unit


def test_hard_delete_removes_owned_content_and_reassigns_audit(
    test_db: Session, monkeypatch
) -> None:
    user = _user(test_db, "delete-me@example.com")
    other = _user(test_db, "keep-me@example.com")
    owned = _unit(test_db, user, user, "DEL101")
    kept = _unit(test_db, other, user, "KEEP101")
    owned_id, kept_id = owned.id, kept.id

    outline = UnitOutline(
        id=str(uuid.uuid4()),
        unit_id=owned.id,
        title="Owned outline",
        duration_weeks=12,
        credit_points=6,
        created_by_id=user.id,
    )
    material = WeeklyMaterial(
        id=str(uuid.uuid4()),
        unit_id=owned.id,
        week_number=1,
        title="Owned material",
        type="reading",
    )
    log = SecurityLog(
        id=str(uuid.uuid4()),
        event_type="login_success",
        severity="info",
        user_id=user.id,
        user_email=user.email,
        ip_address="127.0.0.1",
        details={"email": user.email},
    )
    outline_id, material_id, log_id = outline.id, material.id, log.id
    test_db.add_all([outline, material, log])
    test_db.commit()

    monkeypatch.setattr(account_deletion_service, "_remove_files", lambda *_: None)
    delete_user_account(test_db, str(user.id))
    test_db.expire_all()

    assert test_db.query(User).filter(User.id == user.id).first() is None
    assert test_db.query(Unit).filter(Unit.id == owned_id).first() is None
    assert (
        test_db.query(UnitOutline).filter(UnitOutline.id == outline_id).first() is None
    )
    assert (
        test_db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id).first()
        is None
    )

    remaining = test_db.query(Unit).filter(Unit.id == kept_id).one()
    assert remaining.owner_id == other.id
    assert remaining.created_by_id == other.id

    anonymised = test_db.query(SecurityLog).filter(SecurityLog.id == log_id).one()
    assert anonymised.user_id is None
    assert anonymised.user_email is None
    assert anonymised.details is None
