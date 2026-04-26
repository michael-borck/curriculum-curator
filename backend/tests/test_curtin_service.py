"""Tests for Curtin integration service and routes."""

from app.models.curtin_job import CurtinExportJob
from app.schemas.curtin import CurtinSettings, CurtinJobResponse


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


import pytest
from unittest.mock import MagicMock
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from app.services.curtin_service import _forgerock_login, CurtinServiceError


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
