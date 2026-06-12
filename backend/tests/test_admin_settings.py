"""Tests for the admin system-settings endpoints (SystemConfig-backed)."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.api.routes.admin import (
    _load_system_settings,
    get_system_settings,
    update_system_settings,
)
from app.models import ConfigCategory, SystemConfig, User, UserRole
from app.schemas.admin import SystemSettingsUpdate


@pytest.fixture
def admin_user(test_db: Session) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        password_hash="hashed_password_placeholder",
        name="Admin User",
        role=UserRole.ADMIN.value,
        is_verified=True,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_settings_returns_defaults_on_empty_db(
    test_db: Session, admin_user: User
):
    settings = await get_system_settings(db=test_db, admin_user=admin_user)

    assert settings.password_min_length == 8
    assert settings.max_login_attempts == 5
    assert settings.enable_user_registration is True


@pytest.mark.asyncio
async def test_get_settings_reads_stored_config_values(
    test_db: Session, admin_user: User
):
    test_db.add(
        SystemConfig(
            key="security.max_login_attempts",
            value=3,
            category=ConfigCategory.SECURITY.value,
        )
    )
    test_db.commit()

    settings = await get_system_settings(db=test_db, admin_user=admin_user)

    assert settings.max_login_attempts == 3
    # Unstored fields still fall back to schema defaults
    assert settings.password_min_length == 8


@pytest.mark.asyncio
async def test_update_settings_persists_and_round_trips(
    test_db: Session, admin_user: User
):
    updated = await update_system_settings(
        settings_data=SystemSettingsUpdate(
            password_min_length=12, enable_user_registration=False
        ),
        db=test_db,
        admin_user=admin_user,
    )

    assert updated.password_min_length == 12
    assert updated.enable_user_registration is False

    # Values survive a fresh read from the database
    reloaded = _load_system_settings(test_db)
    assert reloaded.password_min_length == 12
    assert reloaded.enable_user_registration is False
    # Untouched fields keep their defaults
    assert reloaded.max_login_attempts == 5

    row = (
        test_db.query(SystemConfig)
        .filter(SystemConfig.key == "security.password_min_length")
        .one()
    )
    assert row.value == 12
    assert row.updated_by_id == admin_user.id


@pytest.mark.asyncio
async def test_update_settings_overwrites_existing_config_row(
    test_db: Session, admin_user: User
):
    test_db.add(
        SystemConfig(
            key="security.lockout_duration",
            value=30,
            category=ConfigCategory.SECURITY.value,
        )
    )
    test_db.commit()

    await update_system_settings(
        settings_data=SystemSettingsUpdate(lockout_duration_minutes=45),
        db=test_db,
        admin_user=admin_user,
    )

    rows = (
        test_db.query(SystemConfig)
        .filter(SystemConfig.key == "security.lockout_duration")
        .all()
    )
    assert len(rows) == 1
    assert rows[0].value == 45


# ---------------------------------------------------------------------------
# Enforcement: the persisted settings drive actual security behavior
# ---------------------------------------------------------------------------


def _store_setting(test_db: Session, key: str, value: object) -> None:
    test_db.add(
        SystemConfig(key=key, value=value, category=ConfigCategory.SECURITY.value)
    )
    test_db.commit()


def test_get_security_settings_reads_stored_values(test_db: Session):
    from app.core.security_settings import get_security_settings

    _store_setting(test_db, "security.password_min_length", 12)
    _store_setting(test_db, "security.max_login_attempts", 3)

    loaded = get_security_settings(test_db)

    assert loaded.password_min_length == 12
    assert loaded.max_login_attempts == 3
    assert loaded.lockout_duration_minutes == 15  # unset -> default


def test_get_security_settings_ignores_wrong_typed_rows(test_db: Session):
    from app.core.security_settings import get_security_settings

    _store_setting(test_db, "security.password_min_length", "twelve")
    _store_setting(test_db, "security.enable_user_registration", 0)

    loaded = get_security_settings(test_db)

    assert loaded.password_min_length == 8
    assert loaded.enable_user_registration is True


def test_password_validator_honours_admin_policy(test_db: Session):
    from app.core.password_validator import PasswordValidator
    from app.core.security_settings import get_security_settings

    _store_setting(test_db, "security.password_min_length", 16)
    _store_setting(test_db, "security.password_require_special", False)
    policy = get_security_settings(test_db)

    # 12 chars, no special char: fails only on the longer min length
    is_valid, errors = PasswordValidator.validate_password(
        "Zq3vKx9mTw1b", policy=policy
    )
    assert not is_valid
    assert any("16 characters" in e for e in errors)
    assert not any("special character" in e for e in errors)

    # Same password passes under the default policy except the special char
    is_valid_default, errors_default = PasswordValidator.validate_password(
        "Zq3vKx9mTw1b"
    )
    assert not is_valid_default
    assert any("special character" in e for e in errors_default)


def test_lockout_uses_configured_attempts_and_duration(test_db: Session):
    from app.repositories import security_repo

    email = "lockout-test@example.com"
    for _ in range(2):
        attempt = security_repo.record_login_failure(
            test_db,
            email,
            "10.0.0.1",
            max_attempts=3,
            lockout_minutes=45,
        )
        assert not attempt.is_locked

    attempt = security_repo.record_login_failure(
        test_db, email, "10.0.0.1", max_attempts=3, lockout_minutes=45
    )

    assert attempt.is_locked
    assert attempt.locked_until is not None
    # SQLite returns naive datetimes; normalise before comparing
    locked_until = attempt.locked_until.replace(tzinfo=UTC)
    expires_in = (locked_until - datetime.now(UTC)).total_seconds() / 60
    assert 40 <= expires_in <= 45
