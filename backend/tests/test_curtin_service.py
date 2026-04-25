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
