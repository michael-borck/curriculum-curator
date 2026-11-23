"""Regression tests for the LOW/MEDIUM audit items."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_camel_model_rejects_unknown_fields() -> None:
    from app.schemas.research import ResearchSettings

    with pytest.raises(ValidationError):
        ResearchSettings(preferredTier=1, unexpectedField=True)


def test_like_wildcards_are_escaped() -> None:
    from app.repositories.unit_repo import _escape_like

    assert _escape_like("100%_done") == "100\\%\\_done"


def test_unit_count_is_not_page_size(test_db: Session, test_user) -> None:
    from app.models.unit import Unit
    from app.repositories import unit_repo

    for index in range(3):
        test_db.add(
            Unit(
                id=str(uuid.uuid4()),
                title=f"Unit {index}",
                code=f"U{index}",
                year=2026,
                semester="semester_1",
                duration_weeks=12,
                owner_id=test_user.id,
                created_by_id=test_user.id,
            )
        )
    test_db.commit()

    page = unit_repo.search_units(test_db, owner_id=test_user.id, skip=0, limit=1)
    total = unit_repo.count_units(test_db, owner_id=test_user.id)

    assert len(page) == 1
    assert total == 3


def test_verification_code_locks_after_repeated_misses(
    test_db: Session, test_user
) -> None:
    from app.repositories import user_repo

    code = user_repo.create_verification_code(test_db, test_user.id)
    wrong = "000000" if code != "000000" else "111111"

    for _ in range(5):
        assert user_repo.verify_email_code(test_db, test_user.id, wrong) is False

    assert user_repo.verify_email_code(test_db, test_user.id, code) is False


def test_password_reset_code_locks_after_repeated_misses(
    test_db: Session, test_user
) -> None:
    from app.repositories import user_repo

    code = user_repo.create_password_reset_code(test_db, test_user.id)
    wrong = "000000" if code != "000000" else "111111"

    for _ in range(5):
        assert (
            user_repo.verify_password_reset_code(test_db, test_user.id, wrong) is False
        )

    assert user_repo.verify_password_reset_code(test_db, test_user.id, code) is False


def test_failed_import_cleanup_removes_git_paths(monkeypatch) -> None:
    import app.services.unified_import_service as service_module

    calls: list[str] = []

    class FakeGit:
        def delete_file(self, unit_id, path, user_email, message=None):
            calls.append(path)

    monkeypatch.setattr(service_module, "get_git_service", FakeGit)

    service_module.unified_import_service._cleanup_written_paths(
        "unit-1", ["a/image1.png", "a/image2.png"], "user@example.com"
    )

    # Deleted newest-first so nested/dependent paths unwind safely.
    assert calls == ["a/image2.png", "a/image1.png"]


def test_sqlite_upgrade_adds_new_columns(tmp_path, monkeypatch) -> None:
    from sqlalchemy import create_engine, text

    from app.core import database as core_database
    from app.core.config import settings

    db_path = tmp_path / "legacy.db"
    legacy_engine = create_engine(f"sqlite:///{db_path}")
    with legacy_engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE users (id VARCHAR PRIMARY KEY, email VARCHAR, "
                "password_hash VARCHAR, name VARCHAR, role VARCHAR, "
                "is_verified BOOLEAN, is_active BOOLEAN)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE email_verifications (id VARCHAR PRIMARY KEY, "
                "user_id VARCHAR, code VARCHAR(6) NOT NULL, expires_at DATETIME, "
                "used BOOLEAN, created_at DATETIME)"
            )
        )

    monkeypatch.setattr(core_database, "engine", legacy_engine)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{db_path}")
    core_database._ensure_sqlite_schema()

    with legacy_engine.begin() as conn:
        user_cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()
        }
        verification_cols = {
            row[1]
            for row in conn.execute(
                text("PRAGMA table_info(email_verifications)")
            ).fetchall()
        }

    assert {"token_version", "totp_secret", "totp_enabled"} <= user_cols
    assert "code_hash" in verification_cols
    assert "code" not in verification_cols
    assert "attempts" in verification_cols
