"""Tests for Curtin integration service and routes."""

import pytest
from unittest.mock import MagicMock
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from app.models.curtin_job import CurtinExportJob
from app.schemas.curtin import CurtinSettings
from app.services.curtin_service import CurtinServiceError, _forgerock_login


def test_curtin_job_model_exists() -> None:
    assert CurtinExportJob.__tablename__ == "curtin_export_jobs"


def test_curtin_settings_defaults() -> None:
    s = CurtinSettings()
    assert s.litec_url == "https://litec.curtin.edu.au/outline.cfm"
    assert s.blackboard_url == "https://lms.curtin.edu.au/"
    assert s.campus == "Bentley Perth Campus"
    assert s.curtin_username == ""
    assert s.curtin_password == ""


def test_curtin_settings_camel_alias() -> None:
    """Schema serialises snake_case to camelCase for the frontend."""
    s = CurtinSettings(curtin_username="u", curtin_password="p")
    d = s.model_dump(by_alias=True)
    assert "curtinUsername" in d
    assert "curtinPassword" in d


def test_forgerock_login_raises_on_username_field_not_found() -> None:
    """_forgerock_login raises CurtinServiceError when SSO field is absent."""
    mock_page = MagicMock()
    mock_page.wait_for_selector.side_effect = PlaywrightTimeout("timeout")

    with pytest.raises(CurtinServiceError, match="Could not find SSO username field"):
        _forgerock_login(mock_page, "https://litec.curtin.edu.au/outline.cfm", "user", "pass")


def test_forgerock_login_raises_on_wrong_redirect() -> None:
    """_forgerock_login raises CurtinServiceError when login redirects away from curtin.edu.au."""
    mock_page = MagicMock()
    mock_page.wait_for_selector.return_value = None  # field found
    mock_page.url = "https://unexpected-domain.com/error"

    with pytest.raises(CurtinServiceError, match="Login may have failed"):
        _forgerock_login(mock_page, "https://litec.curtin.edu.au/outline.cfm", "user", "pass")


def test_forgerock_login_succeeds() -> None:
    """_forgerock_login completes without error on happy path."""
    mock_page = MagicMock()
    mock_page.wait_for_selector.return_value = None
    mock_page.url = "https://litec.curtin.edu.au/outline.cfm"

    _forgerock_login(mock_page, "https://litec.curtin.edu.au/outline.cfm", "user", "pass")

    mock_page.goto.assert_called_once_with(
        "https://litec.curtin.edu.au/outline.cfm",
        wait_until="networkidle",
        timeout=30000,
    )
    mock_page.fill.assert_any_call("input[name='callback_1']", "user")
    mock_page.fill.assert_any_call("input[type='password']", "pass")


from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.api.deps import get_current_active_user, get_db

client = TestClient(app)


def _override_deps(test_db: Session, test_user: User) -> None:
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_current_active_user] = lambda: test_user


def _clear_deps() -> None:
    app.dependency_overrides.clear()


def test_get_curtin_settings_returns_defaults(test_db: Session, test_user: User) -> None:
    """GET /api/curtin/settings returns defaults when no curtin prefs stored."""
    _override_deps(test_db, test_user)
    try:
        r = client.get("/api/curtin/settings")
        assert r.status_code == 200
        data = r.json()
        assert data["litecUrl"] == "https://litec.curtin.edu.au/outline.cfm"
        assert data["blackboardUrl"] == "https://lms.curtin.edu.au/"
        assert data["campus"] == "Bentley Perth Campus"
        assert data["curtinUsername"] == ""
    finally:
        _clear_deps()


def test_put_curtin_settings_persists(test_db: Session, test_user: User) -> None:
    """PUT /api/curtin/settings saves and GET returns the updated values."""
    _override_deps(test_db, test_user)
    try:
        r = client.put(
            "/api/curtin/settings",
            json={
                "curtinUsername": "jsmith",
                "curtinPassword": "secret",
                "litecUrl": "https://litec.curtin.edu.au/outline.cfm",
                "blackboardUrl": "https://lms.curtin.edu.au/",
                "campus": "Bentley Perth Campus",
            },
        )
        assert r.status_code == 200
        r2 = client.get("/api/curtin/settings")
        assert r2.json()["curtinUsername"] == "jsmith"
    finally:
        _clear_deps()


def test_outline_download_rejects_missing_credentials(test_db: Session, test_user: User) -> None:
    """POST /api/curtin/outline/download returns 400 when no credentials set."""
    _override_deps(test_db, test_user)
    try:
        r = client.post("/api/curtin/outline/download", json={"unitCode": "COMP1000"})
        assert r.status_code == 400
        assert "credentials" in r.json()["detail"].lower()
    finally:
        _clear_deps()


def test_course_build_rejects_missing_credentials(test_db: Session, test_user: User) -> None:
    """POST /api/curtin/course/build returns 400 when no credentials set."""
    _override_deps(test_db, test_user)
    try:
        r = client.post("/api/curtin/course/build", json={"courseName": "COMP1000"})
        assert r.status_code == 400
    finally:
        _clear_deps()
