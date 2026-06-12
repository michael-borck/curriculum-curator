"""Tests for the admin system-settings endpoints (SystemConfig-backed)."""

import uuid

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
