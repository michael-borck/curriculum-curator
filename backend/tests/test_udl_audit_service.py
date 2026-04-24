"""Tests for UDLAuditService — real in-memory SQLite."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.udl_audit import UDLAuditResponse
from app.models.unit import Unit
from app.models.user import User
from app.schemas.udl_audit import UDLAuditBatchUpsert, UDLCheckpointEntry
from app.services.udl_audit_service import udl_audit_service


def test_model_exists() -> None:
    assert UDLAuditResponse.__tablename__ == "udl_audit_responses"


def test_list_profiles_returns_at_least_one() -> None:
    profiles = udl_audit_service.list_profiles()
    assert len(profiles) >= 1
    first = profiles[0]
    assert "id" in first
    assert "name" in first
    assert "checkpoints" in first


def test_list_guidelines_has_three_principles() -> None:
    guidelines = udl_audit_service.list_guidelines()
    assert len(guidelines["principles"]) == 3


def test_upsert_and_get_responses(test_db: Session, test_unit: Unit) -> None:
    unit_id = uuid.UUID(test_unit.id)
    profile_id = "inclusive-assessment-design"

    data = UDLAuditBatchUpsert(
        profile_id=profile_id,
        assessment_id="",
        responses=[
            UDLCheckpointEntry(checkpoint_id="4.1", response="doing_well"),
            UDLCheckpointEntry(checkpoint_id="2.4", response="needs_work", notes="review language"),
        ],
    )
    saved = udl_audit_service.upsert_responses(test_db, unit_id, data)
    assert len(saved) == 2
    codes = {r.checkpoint_id: r.response for r in saved}
    assert codes["4.1"] == "doing_well"
    assert codes["2.4"] == "needs_work"


def test_upsert_overwrites_existing(test_db: Session, test_unit: Unit) -> None:
    unit_id = uuid.UUID(test_unit.id)
    profile_id = "inclusive-assessment-design"

    first = UDLAuditBatchUpsert(
        profile_id=profile_id,
        assessment_id="",
        responses=[UDLCheckpointEntry(checkpoint_id="4.1", response="needs_work")],
    )
    udl_audit_service.upsert_responses(test_db, unit_id, first)

    second = UDLAuditBatchUpsert(
        profile_id=profile_id,
        assessment_id="",
        responses=[UDLCheckpointEntry(checkpoint_id="4.1", response="doing_well")],
    )
    saved = udl_audit_service.upsert_responses(test_db, unit_id, second)
    assert saved[0].response == "doing_well"
    # Only one row in DB
    rows = test_db.query(UDLAuditResponse).filter_by(
        unit_id=test_unit.id, checkpoint_id="4.1", assessment_id=""
    ).all()
    assert len(rows) == 1


def test_unit_scope_and_assessment_scope_are_independent(
    test_db: Session, test_unit: Unit
) -> None:
    unit_id = uuid.UUID(test_unit.id)
    assessment_uuid = str(uuid.uuid4())

    udl_audit_service.upsert_responses(
        test_db,
        unit_id,
        UDLAuditBatchUpsert(
            profile_id="inclusive-assessment-design",
            assessment_id="",
            responses=[UDLCheckpointEntry(checkpoint_id="4.1", response="doing_well")],
        ),
    )
    udl_audit_service.upsert_responses(
        test_db,
        unit_id,
        UDLAuditBatchUpsert(
            profile_id="inclusive-assessment-design",
            assessment_id=assessment_uuid,
            responses=[UDLCheckpointEntry(checkpoint_id="4.1", response="needs_work")],
        ),
    )

    unit_responses = udl_audit_service.get_responses(
        test_db, unit_id, "inclusive-assessment-design", ""
    )
    assessment_responses = udl_audit_service.get_responses(
        test_db, unit_id, "inclusive-assessment-design", assessment_uuid
    )
    assert unit_responses[0].response == "doing_well"
    assert assessment_responses[0].response == "needs_work"


def test_get_summary(test_db: Session, test_unit: Unit) -> None:
    unit_id = uuid.UUID(test_unit.id)
    udl_audit_service.upsert_responses(
        test_db,
        unit_id,
        UDLAuditBatchUpsert(
            profile_id="inclusive-assessment-design",
            assessment_id="",
            responses=[
                UDLCheckpointEntry(checkpoint_id="4.1", response="doing_well"),
                UDLCheckpointEntry(checkpoint_id="2.4", response="needs_work"),
                UDLCheckpointEntry(checkpoint_id="8.3", response="not_applicable"),
            ],
        ),
    )
    summary = udl_audit_service.get_summary(
        test_db, unit_id, "inclusive-assessment-design", ""
    )
    assert summary.doing_well == 1
    assert summary.needs_work == 1
    assert summary.not_applicable == 1
    assert summary.skipped == 3  # 6 total checkpoints in profile - 3 answered
    assert summary.total_checkpoints == 6
