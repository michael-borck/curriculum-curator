"""Regression tests for the security-hardening fixes.

Covers the durable backstops added for path traversal (GitContentService
containment), git argument injection (commit validation), and SSRF
(assert_public_url) — see the security audit follow-up.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.models.unit import Unit
from app.models.user import User, UserRole
from app.models.weekly_material import WeeklyMaterial
from app.services.git_content_service import GitContentService
from app.utils.url_safety import UrlNotAllowedError, assert_public_url


# ──────────────────────────────────────────────────────────────
# GitContentService path containment (M1 / H3 backstop)
# ──────────────────────────────────────────────────────────────


class TestResolveWithin:
    def test_allows_normal_subpath(self, tmp_path: Path) -> None:
        resolved = GitContentService._resolve_within(tmp_path, "weeks/week-01/x.md")
        assert str(resolved).startswith(str(tmp_path.resolve()))

    def test_allows_repo_root(self, tmp_path: Path) -> None:
        # dir_path "" resolves to the repo root itself — permitted.
        assert GitContentService._resolve_within(tmp_path, "") == tmp_path.resolve()

    @pytest.mark.parametrize(
        "evil",
        [
            "../../../../etc/passwd",
            "weeks/../../secret",
            "/etc/passwd",
            "../outside",
        ],
    )
    def test_rejects_traversal(self, tmp_path: Path, evil: str) -> None:
        with pytest.raises(ValueError, match="escapes unit repository"):
            GitContentService._resolve_within(tmp_path, evil)


# ──────────────────────────────────────────────────────────────
# Git revision validation (M3 — argument injection)
# ──────────────────────────────────────────────────────────────


class TestValidateCommit:
    @pytest.mark.parametrize(
        "good",
        [
            "HEAD",
            "HEAD~1",
            "HEAD^",
            "a1b2c3d",
            "0123456789abcdef0123456789abcdef01234567",
        ],
    )
    def test_accepts_valid_revisions(self, good: str) -> None:
        assert GitContentService._validate_commit(good) == good

    @pytest.mark.parametrize(
        "bad",
        [
            "--output=/tmp/x",
            "-O/tmp/x",
            "HEAD; rm -rf /",
            "abc def",
            "not-a-sha",
            "",
        ],
    )
    def test_rejects_option_injection(self, bad: str) -> None:
        with pytest.raises(ValueError, match="Invalid git revision"):
            GitContentService._validate_commit(bad)


# ──────────────────────────────────────────────────────────────
# SSRF guard (H2)
# ──────────────────────────────────────────────────────────────


class TestAssertPublicUrl:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/admin",
            "http://localhost/",  # resolves to loopback
            "http://169.254.169.254/latest/meta-data/",  # cloud metadata
            "http://10.0.0.5/",
            "http://192.168.1.1/",
            "http://[::1]/",
        ],
    )
    async def test_blocks_internal_targets(self, url: str) -> None:
        with pytest.raises(UrlNotAllowedError):
            await assert_public_url(url)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "ftp://example.com/x",
            "gopher://x/",
            "data:text/html,x",
        ],
    )
    async def test_blocks_non_http_schemes(self, url: str) -> None:
        with pytest.raises(UrlNotAllowedError):
            await assert_public_url(url)

    @pytest.mark.asyncio
    async def test_blocks_missing_host(self) -> None:
        with pytest.raises(UrlNotAllowedError):
            await assert_public_url("http:///nohost")


# ──────────────────────────────────────────────────────────────
# Materials router object-level authorization (H1 — IDOR)
# ──────────────────────────────────────────────────────────────


class TestMaterialsIDOR:
    """A lecturer must not read/mutate another lecturer's material."""

    def _other_users_material(self, test_db) -> WeeklyMaterial:  # type: ignore[no-untyped-def]
        other = User(
            id=str(uuid.uuid4()),
            email="attacker@example.com",
            password_hash="x",
            name="Other Lecturer",
            role=UserRole.LECTURER.value,
            is_verified=True,
            is_active=True,
        )
        test_db.add(other)
        test_db.commit()
        unit = Unit(
            id=str(uuid.uuid4()),
            title="Private Unit",
            code="PRIV1001",
            year=2026,
            semester="semester_1",
            duration_weeks=12,
            owner_id=other.id,
            created_by_id=other.id,
            credit_points=6,
        )
        test_db.add(unit)
        test_db.commit()
        material = WeeklyMaterial(
            id=str(uuid.uuid4()),
            unit_id=unit.id,
            week_number=1,
            title="Secret Lecture",
            type="lecture",
            description="private",
            order_index=0,
        )
        test_db.add(material)
        test_db.commit()
        test_db.refresh(material)
        return material

    def test_cannot_read_other_users_material(self, client, test_db) -> None:  # type: ignore[no-untyped-def]
        material = self._other_users_material(test_db)
        resp = client.get(f"/api/materials/materials/{material.id}")
        assert resp.status_code == 404

    def test_cannot_delete_other_users_material(self, client, test_db) -> None:  # type: ignore[no-untyped-def]
        material = self._other_users_material(test_db)
        resp = client.delete(f"/api/materials/materials/{material.id}")
        assert resp.status_code == 404
        # And the row must still exist.
        assert test_db.get(WeeklyMaterial, material.id) is not None
