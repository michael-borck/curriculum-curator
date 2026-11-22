"""AUDIT.md Step 3 regression tests: registration and local-mode controls."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def empty_client(test_db: Session):
    """Client over an empty database with no auth override."""
    from app.api import deps
    from app.core import database as core_database
    from app.main import app

    def _override_get_db():
        yield test_db

    app.dependency_overrides[deps.get_db] = _override_get_db
    app.dependency_overrides[core_database.get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


STRONG_PW = "Str0ng-Passw0rd!23"


class TestWhitelistFailsClosed:
    def test_empty_whitelist_rejects(self, test_db: Session) -> None:
        from app.repositories import user_repo

        assert user_repo.is_email_whitelisted(test_db, "anyone@example.com") is False

    def test_matching_pattern_allows(self, test_db: Session) -> None:
        from app.repositories import user_repo

        user_repo.add_whitelist_pattern(test_db, "@example.com")
        assert user_repo.is_email_whitelisted(test_db, "a@example.com") is True
        assert user_repo.is_email_whitelisted(test_db, "a@other.com") is False


class TestFirstAdminSetupToken:
    def test_first_user_without_token_rejected(
        self, empty_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "SETUP_TOKEN", "one-time-token")
        resp = empty_client.post(
            "/api/auth/register",
            json={
                "email": "admin@example.com",
                "password": STRONG_PW,
                "name": "Admin User",
            },
        )
        assert resp.status_code == 403

    def test_first_user_with_wrong_token_rejected(
        self, empty_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.core.config import settings

        monkeypatch.setattr(settings, "SETUP_TOKEN", "one-time-token")
        resp = empty_client.post(
            "/api/auth/register",
            json={
                "email": "admin@example.com",
                "password": STRONG_PW,
                "name": "Admin User",
                "setupToken": "wrong",
            },
        )
        assert resp.status_code == 403

    def test_first_user_with_token_becomes_admin(
        self,
        empty_client: TestClient,
        test_db: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.core.config import settings
        from app.models.user import User

        monkeypatch.setattr(settings, "SETUP_TOKEN", "one-time-token")
        resp = empty_client.post(
            "/api/auth/register",
            json={
                "email": "admin@example.com",
                "password": STRONG_PW,
                "name": "Admin User",
                "setupToken": "one-time-token",
            },
        )
        assert resp.status_code == 200, resp.text
        created = test_db.query(User).filter_by(email="admin@example.com").one()
        assert created.role == "admin"
        assert created.is_verified is True

    def test_non_first_user_hits_failclosed_whitelist(
        self,
        empty_client: TestClient,
        test_db: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import uuid

        from app.core.config import settings
        from app.models.user import User

        monkeypatch.setattr(settings, "SETUP_TOKEN", "one-time-token")
        test_db.add(
            User(
                id=str(uuid.uuid4()),
                email="existing@example.com",
                password_hash="x",
                name="Existing",
                role="admin",
                is_verified=True,
                is_active=True,
            )
        )
        test_db.commit()

        resp = empty_client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": STRONG_PW,
                "name": "New User",
            },
        )
        assert resp.status_code == 403
