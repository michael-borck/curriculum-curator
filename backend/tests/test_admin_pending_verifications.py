"""Tests for the admin pending-verifications relay endpoint.

The verification code is normally emailed; this admin-only view surfaces it so
an operator on an instance without SMTP can relay it manually.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.api.routes.admin import list_pending_verifications
from app.models import User, UserRole
from app.models.email_verification import EmailVerification
from app.repositories import user_repo


@pytest.fixture
def admin_user(test_db: Session) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        password_hash="x",
        name="Admin User",
        role=UserRole.ADMIN.value,
        is_verified=True,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def _make_unverified_user(test_db: Session, email: str) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash="x",
        name="Pending Person",
        role=UserRole.LECTURER.value,
        is_verified=False,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestGetPendingVerifications:
    def test_lists_unverified_user_with_valid_code(self, test_db: Session) -> None:
        user = _make_unverified_user(test_db, "pending@example.com")
        code = user_repo.create_verification_code(test_db, user.id)

        pending = user_repo.get_pending_verifications(test_db)
        assert len(pending) == 1
        got_user, got_verification = pending[0]
        assert got_user.id == user.id
        assert got_verification.code == code

    def test_excludes_verified_users(self, test_db: Session) -> None:
        user = _make_unverified_user(test_db, "pending@example.com")
        user_repo.create_verification_code(test_db, user.id)
        user.is_verified = True
        test_db.commit()

        assert user_repo.get_pending_verifications(test_db) == []

    def test_excludes_used_codes(self, test_db: Session) -> None:
        user = _make_unverified_user(test_db, "pending@example.com")
        code = user_repo.create_verification_code(test_db, user.id)
        user_repo.verify_email_code(test_db, str(user.id), code)  # marks used

        assert user_repo.get_pending_verifications(test_db) == []

    def test_excludes_expired_codes(self, test_db: Session) -> None:
        user = _make_unverified_user(test_db, "pending@example.com")
        expired = EmailVerification(user_id=user.id, code="123456")
        expired.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        test_db.add(expired)
        test_db.commit()

        assert user_repo.get_pending_verifications(test_db) == []

    def test_returns_newest_valid_code(self, test_db: Session) -> None:
        user = _make_unverified_user(test_db, "pending@example.com")
        user_repo.create_verification_code(test_db, user.id)
        newest = user_repo.create_verification_code(test_db, user.id)

        pending = user_repo.get_pending_verifications(test_db)
        assert len(pending) == 1
        assert pending[0][1].code == newest


class TestPendingVerificationsEndpoint:
    @pytest.mark.asyncio
    async def test_endpoint_returns_pending(
        self, test_db: Session, admin_user: User
    ) -> None:
        user = _make_unverified_user(test_db, "pending@example.com")
        code = user_repo.create_verification_code(test_db, user.id)

        result = await list_pending_verifications(db=test_db, admin_user=admin_user)
        assert len(result) == 1
        assert result[0].email == "pending@example.com"
        assert result[0].code == code
        assert result[0].user_id == str(user.id)
