"""Tests for the resource ownership seam (ADR-066).

Proves the gates actually fire: non-owners get 404, owners get through, admins
bypass. Covers both the route-level dependencies and the deps helpers.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from fastapi import HTTPException

from app.api.deps import filter_owned_unit_ids, load_owned_or_404
from app.models.assessment import Assessment
from app.models.learning_outcome import UnitLearningOutcome
from app.models.unit import Unit
from app.models.user import User
from app.schemas.user import UserResponse

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session


def _user_resp(user_id: str, role: str = "lecturer") -> UserResponse:
    return UserResponse.model_validate(
        {
            "id": user_id,
            "email": f"{user_id[:8]}@example.com",
            "name": "U",
            "role": role,
            "is_verified": True,
            "is_active": True,
            "created_at": "2026-01-01T00:00:00",
        }
    )


def _other_owner_setup(
    db: Session,
) -> tuple[User, Unit, Assessment, UnitLearningOutcome]:
    """Create a second user with a unit + assessment + ULO they own."""
    other = User(
        id=str(uuid.uuid4()),
        email=f"other-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="x",
        name="Other",
        role="lecturer",
        is_verified=True,
        is_active=True,
    )
    db.add(other)
    db.flush()
    unit = Unit(
        id=str(uuid.uuid4()),
        title="Other Unit",
        code=f"OTH{uuid.uuid4().hex[:4]}",
        year=2026,
        semester="semester_1",
        duration_weeks=12,
        owner_id=other.id,
        created_by_id=other.id,
    )
    db.add(unit)
    db.flush()
    assessment = Assessment(
        id=str(uuid.uuid4()),
        unit_id=unit.id,
        title="Other Quiz",
        type="formative",
        category="quiz",
        weight=20.0,
        status="draft",
    )
    ulo = UnitLearningOutcome(
        id=str(uuid.uuid4()),
        unit_id=unit.id,
        outcome_type="ulo",
        outcome_code="ULO1",
        outcome_text="Other outcome",
        bloom_level="ANALYZE",
        sequence_order=1,
        created_by_id=other.id,
    )
    db.add_all([assessment, ulo])
    db.commit()
    return other, unit, assessment, ulo


# ---------------------------------------------------------------------------
# Route-level gates (client is authenticated as test_user, who owns test_unit)
# ---------------------------------------------------------------------------


class TestRouteGates:
    def test_assessment_owner_allowed(
        self,
        client: TestClient,
        test_assessment: Assessment,  # under test_unit, owned by test_user
    ) -> None:
        resp = client.get(f"/api/assessments/assessments/{test_assessment.id}")
        assert resp.status_code == 200

    def test_assessment_non_owner_404(
        self, client: TestClient, test_db: Session
    ) -> None:
        _, _, other_assessment, _ = _other_owner_setup(test_db)
        resp = client.get(f"/api/assessments/assessments/{other_assessment.id}")
        assert resp.status_code == 404

    def test_ulo_owner_allowed(
        self, client: TestClient, test_ulo: UnitLearningOutcome
    ) -> None:
        resp = client.get(f"/api/outcomes/ulos/{test_ulo.id}")
        assert resp.status_code == 200

    def test_ulo_non_owner_404(self, client: TestClient, test_db: Session) -> None:
        _, _, _, other_ulo = _other_owner_setup(test_db)
        resp = client.get(f"/api/outcomes/ulos/{other_ulo.id}")
        assert resp.status_code == 404

    def test_unit_scoped_analytics_non_owner_404(
        self, client: TestClient, test_db: Session
    ) -> None:
        _, other_unit, _, _ = _other_owner_setup(test_db)
        resp = client.get(f"/api/analytics/units/{other_unit.id}/overview")
        assert resp.status_code == 404

    def test_unit_structure_owner_allowed(
        self, client: TestClient, test_unit: Unit
    ) -> None:
        # Consolidated from an inline owner-filter query onto the seam (stage 3).
        resp = client.get(f"/api/units/{test_unit.id}/structure")
        assert resp.status_code == 200

    def test_unit_structure_non_owner_404(
        self, client: TestClient, test_db: Session
    ) -> None:
        _, other_unit, _, _ = _other_owner_setup(test_db)
        resp = client.get(f"/api/units/{other_unit.id}/structure")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Helper: load_owned_or_404 (admin bypass, owner, stranger)
# ---------------------------------------------------------------------------


class TestLoadOwnedOr404:
    def test_owner_via_unit_returns_resource(self, test_db: Session) -> None:
        owner, _, assessment, _ = _other_owner_setup(test_db)
        result = load_owned_or_404(
            test_db,
            Assessment,
            str(assessment.id),
            _user_resp(str(owner.id)),
            via_unit=True,
        )
        assert result.id == assessment.id

    def test_stranger_gets_404(self, test_db: Session) -> None:
        _, _, assessment, _ = _other_owner_setup(test_db)
        with pytest.raises(HTTPException) as exc:
            load_owned_or_404(
                test_db,
                Assessment,
                str(assessment.id),
                _user_resp(str(uuid.uuid4())),
                via_unit=True,
            )
        assert exc.value.status_code == 404

    def test_admin_bypasses(self, test_db: Session) -> None:
        _, _, assessment, _ = _other_owner_setup(test_db)
        result = load_owned_or_404(
            test_db,
            Assessment,
            str(assessment.id),
            _user_resp(str(uuid.uuid4()), role="admin"),
            via_unit=True,
        )
        assert result.id == assessment.id

    def test_missing_resource_404(self, test_db: Session) -> None:
        with pytest.raises(HTTPException) as exc:
            load_owned_or_404(
                test_db,
                Assessment,
                str(uuid.uuid4()),
                _user_resp(str(uuid.uuid4())),
                via_unit=True,
            )
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Helper: filter_owned_unit_ids (batch endpoints)
# ---------------------------------------------------------------------------


class TestFilterOwnedUnitIds:
    def test_drops_non_owned(
        self, test_db: Session, test_unit: Unit, test_user: User
    ) -> None:
        _, other_unit, _, _ = _other_owner_setup(test_db)
        result = filter_owned_unit_ids(
            test_db,
            [str(test_unit.id), str(other_unit.id)],
            _user_resp(str(test_user.id)),
        )
        assert result == [str(test_unit.id)]

    def test_admin_gets_all(self, test_db: Session, test_unit: Unit) -> None:
        _, other_unit, _, _ = _other_owner_setup(test_db)
        ids = [str(test_unit.id), str(other_unit.id)]
        result = filter_owned_unit_ids(
            test_db, ids, _user_resp(str(uuid.uuid4()), role="admin")
        )
        assert result == ids
