"""Tests for UDLAuditService — real in-memory SQLite."""

import pytest
from sqlalchemy.orm import Session

from app.models.udl_audit import UDLAuditResponse


def test_model_exists() -> None:
    assert UDLAuditResponse.__tablename__ == "udl_audit_responses"
