"""Tests for Curtin integration service and routes."""

from app.models.curtin_job import CurtinExportJob


def test_curtin_job_model_exists() -> None:
    assert CurtinExportJob.__tablename__ == "curtin_export_jobs"
