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

    page = unit_repo.search_units(
        test_db, owner_id=test_user.id, skip=0, limit=1
    )
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
            user_repo.verify_password_reset_code(test_db, test_user.id, wrong)
            is False
        )

    assert (
        user_repo.verify_password_reset_code(test_db, test_user.id, code) is False
    )
