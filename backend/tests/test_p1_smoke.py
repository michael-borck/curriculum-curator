"""
P1 Smoke Tests - End-to-End API Integration Tests

Exercises the full HTTP request -> route -> service -> DB -> response chain
using FastAPI TestClient with dependency overrides (no running server needed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _create_unit(client: TestClient, **overrides: Any) -> dict[str, Any]:
    """Helper to create a unit via the API and return the JSON response."""
    payload: dict[str, Any] = {
        "title": "Intro to Testing",
        "code": "TEST1001",
        "pedagogyType": "inquiry-based",
        "semester": "semester_1",
        "year": 2026,
        "durationWeeks": 12,
    }
    payload.update(overrides)
    resp = client.post("/api/units/create", json=payload)
    assert resp.status_code == 200, f"create_unit failed: {resp.text}"
    return resp.json()


def _create_ulo(
    client: TestClient,
    unit_id: str,
    code: str = "ULO1",
    description: str = "Demonstrate testing skills",
    bloom_level: str = "apply",
    order_index: int = 0,
) -> dict[str, Any]:
    resp = client.post(
        f"/api/outcomes/units/{unit_id}/ulos",
        json={
            "code": code,
            "description": description,
            "bloomLevel": bloom_level,
            "orderIndex": order_index,
        },
    )
    assert resp.status_code == 200, f"create_ulo failed: {resp.text}"
    return resp.json()


def _create_material(
    client: TestClient,
    unit_id: str,
    week: int = 1,
    title: str = "Lecture 1",
    mat_type: str = "lecture",
    duration: int = 60,
    status: str = "draft",
) -> dict[str, Any]:
    resp = client.post(
        f"/api/materials/units/{unit_id}/materials",
        json={
            "weekNumber": week,
            "title": title,
            "type": mat_type,
            "durationMinutes": duration,
            "status": status,
        },
    )
    assert resp.status_code == 200, f"create_material failed: {resp.text}"
    return resp.json()


def _create_assessment(
    client: TestClient,
    unit_id: str,
    title: str = "Quiz 1",
    a_type: str = "summative",
    category: str = "quiz",
    weight: float = 50.0,
    due_week: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": title,
        "type": a_type,
        "category": category,
        "weight": weight,
    }
    if due_week is not None:
        payload["dueWeek"] = due_week
    resp = client.post(
        f"/api/assessments/units/{unit_id}/assessments",
        json=payload,
    )
    assert resp.status_code == 200, f"create_assessment failed: {resp.text}"
    return resp.json()


# ──────────────────────────────────────────────────────────────
# Test 1: Unit CRUD (stories 1.1-1.3)
# ──────────────────────────────────────────────────────────────


class TestUnitCRUD:
    """Full lifecycle: create → read → update → list → delete."""

    def test_create_unit(self, client: TestClient) -> None:
        data = _create_unit(client)
        assert data["title"] == "Intro to Testing"
        assert data["code"] == "TEST1001"
        assert "id" in data

    def test_get_unit(self, client: TestClient) -> None:
        created = _create_unit(client)
        resp = client.get(f"/api/units/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["code"] == "TEST1001"

    def test_update_unit(self, client: TestClient) -> None:
        created = _create_unit(client)
        resp = client.put(
            f"/api/units/{created['id']}",
            json={"title": "Advanced Testing"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Advanced Testing"

    def test_list_units(self, client: TestClient) -> None:
        _create_unit(client, code="LIST1001")
        _create_unit(client, code="LIST1002")
        resp = client.get("/api/units")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        codes = [u["code"] for u in body["units"]]
        assert "LIST1001" in codes
        assert "LIST1002" in codes

    def test_soft_delete_unit(self, client: TestClient) -> None:
        created = _create_unit(client)
        unit_id = created["id"]

        # Default delete is soft-delete (archive)
        resp = client.delete(f"/api/units/{unit_id}")
        assert resp.status_code == 204

        # Unit still accessible by direct ID (archived, not destroyed)
        resp = client.get(f"/api/units/{unit_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

        # But excluded from the main listing
        resp = client.get("/api/units")
        unit_ids = [u["id"] for u in resp.json()["units"]]
        assert unit_id not in unit_ids

        # Appears in archived listing
        resp = client.get("/api/units/archived")
        assert resp.status_code == 200
        archived_ids = [u["id"] for u in resp.json()["units"]]
        assert unit_id in archived_ids

        # Restore
        resp = client.post(f"/api/units/{unit_id}/restore")
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    def test_hard_delete_unit(self, client: TestClient) -> None:
        created = _create_unit(client)
        unit_id = created["id"]

        # Permanent delete
        resp = client.delete(f"/api/units/{unit_id}", params={"permanent": True})
        assert resp.status_code == 204

        resp = client.get(f"/api/units/{unit_id}")
        assert resp.status_code == 404

    def test_get_nonexistent_unit_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/units/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Test 2: Learning Outcomes CRUD (stories 2.1-2.3)
# ──────────────────────────────────────────────────────────────


class TestLearningOutcomesCRUD:
    """Create, list, update, delete ULOs."""

    def test_create_and_list_ulos(self, client: TestClient) -> None:
        unit = _create_unit(client, code="ULO_UNIT")
        uid = unit["id"]

        _create_ulo(client, uid, code="ULO1", bloom_level="remember", order_index=0)
        _create_ulo(client, uid, code="ULO2", bloom_level="apply", order_index=1)
        _create_ulo(client, uid, code="ULO3", bloom_level="evaluate", order_index=2)

        resp = client.get(f"/api/outcomes/units/{uid}/ulos")
        assert resp.status_code == 200
        ulos = resp.json()
        assert len(ulos) == 3
        codes = [u["code"] for u in ulos]
        assert codes == ["ULO1", "ULO2", "ULO3"]

    def test_update_ulo(self, client: TestClient) -> None:
        unit = _create_unit(client, code="ULO_UPD")
        ulo = _create_ulo(client, unit["id"])
        ulo_id = ulo["id"]

        resp = client.put(
            f"/api/outcomes/ulos/{ulo_id}",
            json={"description": "Updated description", "bloomLevel": "analyze"},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["description"] == "Updated description"
        assert updated["bloomLevel"] == "analyze"

    def test_delete_ulo(self, client: TestClient) -> None:
        unit = _create_unit(client, code="ULO_DEL")
        uid = unit["id"]
        ulo1 = _create_ulo(client, uid, code="ULO1")
        _create_ulo(client, uid, code="ULO2")

        resp = client.delete(f"/api/outcomes/ulos/{ulo1['id']}")
        assert resp.status_code == 200

        resp = client.get(f"/api/outcomes/units/{uid}/ulos")
        assert len(resp.json()) == 1


# ──────────────────────────────────────────────────────────────
# Test 3: Materials CRUD (stories 3.1-3.6)
# ──────────────────────────────────────────────────────────────


class TestMaterialsCRUD:
    """Create, list, filter, update, duplicate, delete materials."""

    def test_create_and_list_materials(self, client: TestClient) -> None:
        unit = _create_unit(client, code="MAT_UNIT")
        uid = unit["id"]

        _create_material(client, uid, week=1, title="Week 1 Lecture")
        _create_material(client, uid, week=1, title="Week 1 Lab")
        _create_material(client, uid, week=2, title="Week 2 Lecture")

        resp = client.get(f"/api/materials/units/{uid}/materials")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_filter_materials_by_week(self, client: TestClient) -> None:
        unit = _create_unit(client, code="MAT_FILT")
        uid = unit["id"]

        _create_material(client, uid, week=1, title="W1 Lecture")
        _create_material(client, uid, week=2, title="W2 Lecture")

        resp = client.get(
            f"/api/materials/units/{uid}/materials", params={"week_number": 1}
        )
        assert resp.status_code == 200
        mats = resp.json()
        assert len(mats) == 1
        assert mats[0]["title"] == "W1 Lecture"

    def test_update_material(self, client: TestClient) -> None:
        unit = _create_unit(client, code="MAT_UPD")
        mat = _create_material(client, unit["id"])

        resp = client.put(
            f"/api/materials/materials/{mat['id']}",
            json={"title": "Updated Lecture", "durationMinutes": 90},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["title"] == "Updated Lecture"
        assert updated["durationMinutes"] == 90

    def test_duplicate_material(self, client: TestClient) -> None:
        unit = _create_unit(client, code="MAT_DUP")
        mat = _create_material(client, unit["id"], week=1, title="Original")

        resp = client.post(
            f"/api/materials/materials/{mat['id']}/duplicate",
            json={"targetWeek": 3, "newTitle": "Copy of Original"},
        )
        assert resp.status_code == 200
        dup = resp.json()
        assert dup["id"] != mat["id"]
        assert dup["weekNumber"] == 3
        assert dup["title"] == "Copy of Original"

    def test_delete_material(self, client: TestClient) -> None:
        unit = _create_unit(client, code="MAT_DEL")
        mat = _create_material(client, unit["id"])

        resp = client.delete(f"/api/materials/materials/{mat['id']}")
        assert resp.status_code == 200

        resp = client.get(f"/api/materials/units/{unit['id']}/materials")
        assert len(resp.json()) == 0


# ──────────────────────────────────────────────────────────────
# Test 4: Assessments + Weights (stories 4.1-4.3)
# ──────────────────────────────────────────────────────────────


class TestAssessmentsAndWeights:
    """Create assessments and validate weight distribution."""

    def test_create_assessments(self, client: TestClient) -> None:
        unit = _create_unit(client, code="ASSESS1")
        uid = unit["id"]

        a1 = _create_assessment(client, uid, title="Midterm", weight=40.0)
        a2 = _create_assessment(client, uid, title="Final", weight=60.0)

        assert a1["weight"] == 40.0
        assert a2["weight"] == 60.0

        resp = client.get(f"/api/assessments/units/{uid}/assessments")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_weight_validation_pass(self, client: TestClient) -> None:
        unit = _create_unit(client, code="ASSESS_OK")
        uid = unit["id"]

        _create_assessment(client, uid, title="A1", weight=60.0)
        _create_assessment(client, uid, title="A2", weight=40.0)

        resp = client.get(f"/api/assessments/units/{uid}/assessments/validate-weights")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_weight"] == pytest.approx(100.0)
        assert body["is_valid"] is True

    def test_weight_validation_over_100(self, client: TestClient) -> None:
        unit = _create_unit(client, code="ASSESS_OVER")
        uid = unit["id"]

        _create_assessment(client, uid, title="A1", weight=60.0)
        _create_assessment(client, uid, title="A2", weight=40.0)
        _create_assessment(client, uid, title="A3", weight=20.0)

        resp = client.get(f"/api/assessments/units/{uid}/assessments/validate-weights")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_weight"] == pytest.approx(120.0)
        assert body["is_valid"] is False

    def test_grade_distribution(self, client: TestClient) -> None:
        unit = _create_unit(client, code="GRADE_DIST")
        uid = unit["id"]

        _create_assessment(
            client, uid, title="Quiz", a_type="formative", category="quiz", weight=20.0
        )
        _create_assessment(
            client,
            uid,
            title="Exam",
            a_type="summative",
            category="exam",
            weight=80.0,
        )

        resp = client.get(
            f"/api/assessments/units/{uid}/assessments/grade-distribution"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["totalWeight"] == pytest.approx(100.0)
        assert body["formativeWeight"] == pytest.approx(20.0)
        assert body["summativeWeight"] == pytest.approx(80.0)


# ──────────────────────────────────────────────────────────────
# Test 5: Constructive Alignment (stories 2.4, 4.3, 7.4, 7.6)
# ──────────────────────────────────────────────────────────────


class TestConstructiveAlignment:
    """Full flow: unit → ULOs → materials → assessments → mappings → reports."""

    def test_alignment_flow(self, client: TestClient) -> None:
        # 1) Create unit
        unit = _create_unit(client, code="ALIGN1")
        uid = unit["id"]

        # 2) Create 2 ULOs
        ulo1 = _create_ulo(
            client, uid, code="ULO1", description="Apply testing", bloom_level="apply"
        )
        _create_ulo(
            client,
            uid,
            code="ULO2",
            description="Evaluate results",
            bloom_level="evaluate",
        )

        # 3) Create materials in week 1 and 2
        mat1 = _create_material(client, uid, week=1, title="Testing Intro")
        _create_material(client, uid, week=2, title="Testing Advanced")

        # 4) Create assessments (50% each)
        a1 = _create_assessment(client, uid, title="Quiz 1", weight=50.0, due_week=3)
        _create_assessment(client, uid, title="Quiz 2", weight=50.0, due_week=6)

        # 5) Map ULO1 to material1
        resp = client.put(
            f"/api/materials/materials/{mat1['id']}/mappings",
            json={"uloIds": [ulo1["id"]]},
        )
        assert resp.status_code == 200

        # 6) Map ULO1 to assessment1
        resp = client.put(
            f"/api/assessments/assessments/{a1['id']}/mappings",
            json={"uloIds": [ulo1["id"]]},
        )
        assert resp.status_code == 200

        # 7) Get alignment report — ULO1 should be aligned, ULO2 unaligned
        resp = client.get(f"/api/analytics/units/{uid}/alignment")
        assert resp.status_code == 200
        alignment = resp.json()
        details = alignment["alignmentDetails"]
        assert len(details) == 2

        # Find each ULO's alignment status
        by_code = {d["ulo_code"]: d for d in details}
        assert by_code["ULO1"]["material_count"] >= 1
        assert by_code["ULO1"]["assessment_count"] >= 1
        assert by_code["ULO2"]["material_count"] == 0
        assert by_code["ULO2"]["assessment_count"] == 0

        # 8) Get completion report
        resp = client.get(f"/api/analytics/units/{uid}/completion")
        assert resp.status_code == 200
        completion = resp.json()
        # Only 1 of 2 ULOs is fully covered
        assert completion["ulosTotal"] == 2
        assert completion["ulosFullyCovered"] == 1


# ──────────────────────────────────────────────────────────────
# Test 6: Analytics Accuracy (stories 8.1-8.5)
# ──────────────────────────────────────────────────────────────


class TestAnalyticsAccuracy:
    """Build a realistic unit and verify analytics match."""

    def _build_unit(self, client: TestClient) -> str:
        """Create a unit with 2 ULOs, 3 weeks of materials, 2 assessments."""
        unit = _create_unit(client, code="ANALYTICS1")
        uid = unit["id"]

        _create_ulo(client, uid, code="ULO1", bloom_level="apply")
        _create_ulo(client, uid, code="ULO2", bloom_level="analyze")

        # Week 1-3 materials (mix of draft/published)
        _create_material(
            client, uid, week=1, title="W1 Lecture", duration=60, status="published"
        )
        _create_material(
            client, uid, week=1, title="W1 Lab", duration=90, status="draft"
        )
        _create_material(
            client, uid, week=2, title="W2 Lecture", duration=60, status="published"
        )
        _create_material(
            client, uid, week=3, title="W3 Lecture", duration=60, status="draft"
        )

        _create_assessment(
            client, uid, title="Midterm", weight=40.0, due_week=6, category="exam"
        )
        _create_assessment(
            client,
            uid,
            title="Final Project",
            weight=60.0,
            due_week=12,
            category="project",
        )

        return uid

    def test_overview(self, client: TestClient) -> None:
        uid = self._build_unit(client)

        resp = client.get(f"/api/analytics/units/{uid}/overview")
        assert resp.status_code == 200
        body = resp.json()

        assert body["uloCount"] == 2
        assert body["materials"]["total"] == 4
        assert body["assessments"]["total"] == 2
        assert body["totalAssessmentWeight"] == pytest.approx(100.0)

    def test_progress(self, client: TestClient) -> None:
        uid = self._build_unit(client)

        resp = client.get(f"/api/analytics/units/{uid}/progress")
        assert resp.status_code == 200
        body = resp.json()

        # 2 published, 2 draft materials
        assert body["materials"]["published"] == 2
        assert body["materials"]["draft"] == 2

    def test_workload(self, client: TestClient) -> None:
        uid = self._build_unit(client)

        resp = client.get(
            f"/api/analytics/units/{uid}/workload",
            params={"start_week": 1, "end_week": 3},
        )
        assert resp.status_code == 200
        weeks = resp.json()

        # Should include weeks 1-3
        week_nums = [w["weekNumber"] for w in weeks]
        assert 1 in week_nums
        assert 2 in week_nums
        assert 3 in week_nums

        # Week 1 has 150 min (60 + 90)
        w1 = next(w for w in weeks if w["weekNumber"] == 1)
        assert w1["materialDurationMinutes"] == 150
        assert w1["materialCount"] == 2

    def test_quality_score(self, client: TestClient) -> None:
        uid = self._build_unit(client)

        resp = client.get(f"/api/analytics/units/{uid}/quality-score")
        assert resp.status_code == 200
        body = resp.json()

        assert "overallScore" in body
        assert body["overallScore"] >= 0
        assert "grade" in body
        assert "starRating" in body

    def test_validation(self, client: TestClient) -> None:
        uid = self._build_unit(client)

        resp = client.get(f"/api/analytics/units/{uid}/validation")
        assert resp.status_code == 200
        body = resp.json()

        # Should return some validation structure
        assert "is_valid" in body or "errors" in body or "warnings" in body


# ──────────────────────────────────────────────────────────────
# Test 7: Content Versioning (P2 - task 2E)
# ──────────────────────────────────────────────────────────────


def _create_content(
    client: TestClient,
    unit_id: str,
    title: str = "Lecture Notes",
    content_type: str = "lecture",
    body: str = "# Initial content",
    week_number: int = 1,
) -> dict[str, Any]:
    resp = client.post(
        f"/api/units/{unit_id}/content",
        json={
            "title": title,
            "contentType": content_type,
            "body": body,
            "weekNumber": week_number,
        },
    )
    assert resp.status_code == 200, f"create_content failed: {resp.text}"
    return resp.json()


class TestContentVersioning:
    """Create → edit → history → diff → revert lifecycle."""

    def test_create_content(self, client: TestClient) -> None:
        unit = _create_unit(client, code="VER_CREATE")
        content = _create_content(client, unit["id"])
        assert content["title"] == "Lecture Notes"
        assert "id" in content

    def test_update_creates_version(self, client: TestClient) -> None:
        unit = _create_unit(client, code="VER_UPDATE")
        uid = unit["id"]
        content = _create_content(client, uid, body="# Version 1")
        cid = content["id"]

        # Update body (should create a new Git commit)
        resp = client.put(
            f"/api/units/{uid}/content/{cid}",
            json={"body": "# Version 2"},
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == "# Version 2"

    def test_history_returns_commits(self, client: TestClient) -> None:
        unit = _create_unit(client, code="VER_HIST")
        uid = unit["id"]
        content = _create_content(client, uid, body="# v1")
        cid = content["id"]

        # Make an edit so there are at least 2 commits
        client.put(f"/api/units/{uid}/content/{cid}", json={"body": "# v2"})

        resp = client.get(f"/api/units/{uid}/content/{cid}/history")
        assert resp.status_code == 200
        history = resp.json()
        assert "versions" in history
        assert len(history["versions"]) >= 2
        # Each version should have a commit hash
        for v in history["versions"]:
            assert "commit" in v
            assert len(v["commit"]) >= 7

    def test_diff_between_commits(self, client: TestClient) -> None:
        unit = _create_unit(client, code="VER_DIFF")
        uid = unit["id"]
        content = _create_content(client, uid, body="# Original")
        cid = content["id"]

        client.put(f"/api/units/{uid}/content/{cid}", json={"body": "# Changed"})

        # Get history to find two commits
        hist = client.get(f"/api/units/{uid}/content/{cid}/history").json()
        commits = [v["commit"] for v in hist["versions"]]
        assert len(commits) >= 2

        old_commit = commits[-1]  # oldest
        new_commit = commits[0]  # newest

        resp = client.get(
            f"/api/units/{uid}/content/{cid}/diff",
            params={"old_commit": old_commit, "new_commit": new_commit},
        )
        assert resp.status_code == 200
        diff = resp.json()
        assert "diff" in diff
        assert len(diff["diff"]) > 0

    def test_revert_to_previous_commit(self, client: TestClient) -> None:
        unit = _create_unit(client, code="VER_REVERT")
        uid = unit["id"]
        content = _create_content(client, uid, body="# Original body")
        cid = content["id"]

        client.put(f"/api/units/{uid}/content/{cid}", json={"body": "# Changed body"})

        # Get history — oldest commit should be the original
        hist = client.get(f"/api/units/{uid}/content/{cid}/history").json()
        original_commit = hist["versions"][-1]["commit"]

        # Revert to original
        resp = client.post(
            f"/api/units/{uid}/content/{cid}/revert",
            json={"commit": original_commit},
        )
        assert resp.status_code == 200
        reverted = resp.json()
        assert reverted["body"] == "# Original body"

    def test_version_body_at_commit(self, client: TestClient) -> None:
        unit = _create_unit(client, code="VER_BODY")
        uid = unit["id"]
        content = _create_content(client, uid, body="# Snapshot content")
        cid = content["id"]

        hist = client.get(f"/api/units/{uid}/content/{cid}/history").json()
        commit = hist["versions"][0]["commit"]

        resp = client.get(f"/api/units/{uid}/content/{cid}/version/{commit}")
        assert resp.status_code == 200
        assert resp.json()["body"] == "# Snapshot content"
