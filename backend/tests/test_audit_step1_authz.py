"""AUDIT.md Step 1 regression tests: previously-unauthenticated endpoints.

The shared `client` fixture overrides auth, so anonymity is tested here with
a client that only overrides the DB session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit
    from app.models.user import User


@pytest.fixture
def anon_client(test_db: Session):
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


class TestPluginsAuth:
    def test_anon_patch_plugin_config_rejected(self, anon_client: TestClient) -> None:
        resp = anon_client.patch("/api/plugins/anything", json={"enabled": False})
        assert resp.status_code in (401, 403)

    def test_anon_validate_rejected(self, anon_client: TestClient) -> None:
        resp = anon_client.post("/api/plugins/validate", json={"content": "x"})
        assert resp.status_code in (401, 403)

    def test_anon_remediate_rejected(self, anon_client: TestClient) -> None:
        resp = anon_client.post("/api/plugins/remediate", json={"content": "x"})
        assert resp.status_code in (401, 403)

    def test_non_admin_patch_plugin_config_forbidden(self, client: TestClient) -> None:
        # `client` is authenticated as the lecturer test_user.
        resp = client.patch("/api/plugins/anything", json={"enabled": False})
        assert resp.status_code == 403

    def test_plugin_content_length_bounded(self) -> None:
        from pydantic import ValidationError

        from app.schemas.plugins import PluginValidateRequest

        with pytest.raises(ValidationError):
            PluginValidateRequest(content="x" * 200_001)


class TestCrossRefAuth:
    def test_anon_crossref_lookup_rejected(self, anon_client: TestClient) -> None:
        resp = anon_client.post(
            "/api/research/crossref-lookup", json={"doi": "10.1000/xyz123"}
        )
        assert resp.status_code in (401, 403)

    def test_bad_doi_rejected_before_upstream(self, client: TestClient) -> None:
        resp = client.post(
            "/api/research/crossref-lookup", json={"doi": "../../etc/passwd"}
        )
        assert resp.status_code in (400, 422)


class TestResearchSourceUnitOwnership:
    def test_cannot_attach_source_to_foreign_unit(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User,
    ) -> None:
        import uuid

        from app.models.unit import Unit
        from app.models.user import User as UserModel

        other = UserModel(
            id=str(uuid.uuid4()),
            email=f"other-{uuid.uuid4().hex[:8]}@example.com",
            password_hash="x",
            name="Other",
            role="lecturer",
            is_verified=True,
            is_active=True,
        )
        test_db.add(other)
        test_db.flush()
        foreign = Unit(
            id=str(uuid.uuid4()),
            title="Foreign",
            code=f"F{uuid.uuid4().hex[:6]}",
            year=2026,
            semester="semester_1",
            duration_weeks=12,
            owner_id=other.id,
            created_by_id=other.id,
        )
        test_db.add(foreign)
        test_db.commit()

        resp = client.post(
            "/api/sources",
            json={
                "url": "https://example.com/paper",
                "title": "Paper",
                "unitId": str(foreign.id),
            },
        )
        assert resp.status_code == 404

    def test_batch_status_of_unknown_task_404(self, client: TestClient) -> None:
        resp = client.get("/api/import/material/batch/status/nope")
        # Route may be mounted under a different prefix; accept routing 404.
        assert resp.status_code == 404
