"""AUDIT.md Step 6 regression tests: cookie sessions, CSRF, desktop token."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def raw_client(test_db: Session):
    """Client over the test DB with no auth override (real JWT/cookie flow)."""
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


def _make_user(db: Session, password: str = "Str0ng-Passw0rd!23"):
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        id=str(uuid.uuid4()),
        email="cookie-user@example.com",
        password_hash=get_password_hash(password),
        name="Cookie User",
        role="lecturer",
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


class TestCookieSession:
    def test_login_sets_httponly_cookie_and_csrf(
        self, raw_client: TestClient, test_db: Session
    ) -> None:
        _make_user(test_db)
        resp = raw_client.post(
            "/api/auth/login",
            json={"email": "cookie-user@example.com", "password": "Str0ng-Passw0rd!23"},
        )
        assert resp.status_code == 200, resp.text
        cookies = resp.headers.get_list("set-cookie")
        session = next(c for c in cookies if c.startswith("cc_session="))
        csrf = next(c for c in cookies if c.startswith("cc_csrf="))
        assert "HttpOnly" in session
        assert "HttpOnly" not in csrf

    def test_cookie_alone_authenticates(
        self, raw_client: TestClient, test_db: Session
    ) -> None:
        _make_user(test_db)
        raw_client.post(
            "/api/auth/login",
            json={"email": "cookie-user@example.com", "password": "Str0ng-Passw0rd!23"},
        )
        resp = raw_client.get("/api/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "cookie-user@example.com"

    def test_cookie_mutation_requires_csrf_header(
        self, raw_client: TestClient, test_db: Session
    ) -> None:
        _make_user(test_db)
        raw_client.post(
            "/api/auth/login",
            json={"email": "cookie-user@example.com", "password": "Str0ng-Passw0rd!23"},
        )
        resp = raw_client.post(
            "/api/auth/change-password",
            json={
                "currentPassword": "Str0ng-Passw0rd!23",
                "newPassword": "An0ther-Passw0rd!23",
            },
        )
        assert resp.status_code == 403
        assert "CSRF" in resp.text

    def test_cookie_mutation_with_csrf_header_passes(
        self, raw_client: TestClient, test_db: Session
    ) -> None:
        _make_user(test_db)
        raw_client.post(
            "/api/auth/login",
            json={"email": "cookie-user@example.com", "password": "Str0ng-Passw0rd!23"},
        )
        csrf = raw_client.cookies.get("cc_csrf")
        assert csrf
        resp = raw_client.post(
            "/api/auth/change-password",
            json={
                "currentPassword": "Str0ng-Passw0rd!23",
                "newPassword": "An0ther-Passw0rd!23",
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200, resp.text


class TestDesktopToken:
    def test_local_mode_with_token_rejects_missing_header(
        self, raw_client: TestClient, test_db: Session, monkeypatch
    ) -> None:
        from app.api import deps
        from app.core.config import settings
        from app.models.user import User

        monkeypatch.setattr(settings, "LOCAL_MODE", True)
        monkeypatch.setattr(settings, "DESKTOP_TOKEN", "launch-token")
        test_db.add(
            User(
                id=deps.LOCAL_USER_ID,
                email=deps.LOCAL_USER_EMAIL,
                password_hash="x",
                name="Local",
                role="lecturer",
                is_verified=True,
                is_active=True,
            )
        )
        test_db.commit()

        assert raw_client.get("/api/auth/me").status_code == 401
        ok = raw_client.get(
            "/api/auth/me", headers={"X-Desktop-Token": "launch-token"}
        )
        assert ok.status_code == 200
