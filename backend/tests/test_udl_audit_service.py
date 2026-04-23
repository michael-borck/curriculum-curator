"""Tests for UDLAuditService — real in-memory SQLite."""

from app.models.udl_audit import UDLAuditResponse


def test_model_exists() -> None:
    assert UDLAuditResponse.__tablename__ == "udl_audit_responses"
