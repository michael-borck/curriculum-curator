"""
Tests for the ExportRegistry seam and the two generic export routes.

Covers the registry's capability matrix and dispatch, the exception → HTTP
mapping, and that the material-scope routes are ownership-checked via
``get_user_material``. Uses in-memory SQLite (the project's real-DB philosophy).
"""

from __future__ import annotations

import uuid
import zipfile
from typing import TYPE_CHECKING

import pytest

from app.models.unit import Unit
from app.models.user import User
from app.models.weekly_material import WeeklyMaterial
from app.services.export import (
    ExportContentError,
    ExportScope,
    UnknownExportFormatError,
    UnsupportedExportScopeError,
    export_registry,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

EXPECTED_FORMATS = {
    "scorm",
    "imscc",
    "qti",
    "h5p_question_set",
    "h5p_course_presentation",
    "h5p_branching",
    "h5p_interactive_video",
    "html",
    "pdf",
    "docx",
    "pptx",
}


# ---------------------------------------------------------------------------
# Capability matrix (no DB)
# ---------------------------------------------------------------------------


class TestRegistryShape:
    def test_all_expected_formats_registered(self) -> None:
        assert set(export_registry.formats()) == EXPECTED_FORMATS

    def test_unit_scope_formats(self) -> None:
        assert set(export_registry.available_formats(ExportScope.UNIT)) == {
            "scorm",
            "imscc",
            "qti",
            "h5p_question_set",
            "html",
        }

    def test_material_scope_formats(self) -> None:
        assert set(export_registry.available_formats(ExportScope.MATERIAL)) == {
            "qti",
            "h5p_question_set",
            "h5p_course_presentation",
            "h5p_branching",
            "h5p_interactive_video",
            "html",
            "pdf",
            "docx",
            "pptx",
        }

    @pytest.mark.parametrize(
        ("fmt", "scope", "expected"),
        [
            ("scorm", ExportScope.UNIT, True),
            ("scorm", ExportScope.MATERIAL, False),
            ("pdf", ExportScope.MATERIAL, True),
            ("pdf", ExportScope.UNIT, False),
            ("html", ExportScope.UNIT, True),
            ("html", ExportScope.MATERIAL, True),
            ("bogus", ExportScope.UNIT, False),
        ],
    )
    def test_supports(self, fmt: str, scope: ExportScope, expected: bool) -> None:
        assert export_registry.supports(fmt, scope) is expected


# ---------------------------------------------------------------------------
# Dispatch error mapping
# ---------------------------------------------------------------------------


class TestRegistryDispatchErrors:
    @pytest.mark.asyncio
    async def test_unknown_format_raises(self, test_db: Session) -> None:
        with pytest.raises(UnknownExportFormatError):
            await export_registry.export("bogus", ExportScope.UNIT, "any-id", test_db)

    @pytest.mark.asyncio
    async def test_unsupported_scope_raises(self, test_db: Session) -> None:
        with pytest.raises(UnsupportedExportScopeError):
            await export_registry.export(
                "scorm", ExportScope.MATERIAL, "any-id", test_db
            )

    @pytest.mark.asyncio
    async def test_missing_material_raises_content_error(
        self, test_db: Session
    ) -> None:
        with pytest.raises(ExportContentError):
            await export_registry.export(
                "html", ExportScope.MATERIAL, str(uuid.uuid4()), test_db
            )


# ---------------------------------------------------------------------------
# Real exports through the registry
# ---------------------------------------------------------------------------


class TestRegistryExport:
    @pytest.mark.asyncio
    async def test_material_html(
        self, test_db: Session, test_weekly_material: WeeklyMaterial
    ) -> None:
        result = await export_registry.export(
            "html", ExportScope.MATERIAL, str(test_weekly_material.id), test_db
        )
        assert result.media_type == "text/html"
        assert result.filename.endswith(".html")
        assert "Introduction to HTML tags and structure." in result.buf.read().decode(
            "utf-8"
        )

    @pytest.mark.asyncio
    async def test_unit_html(
        self,
        test_db: Session,
        test_unit: Unit,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        result = await export_registry.export(
            "html", ExportScope.UNIT, str(test_unit.id), test_db
        )
        assert result.media_type == "text/html"
        assert result.filename.endswith(".html")
        assert result.buf.getbuffer().nbytes > 0

    @pytest.mark.asyncio
    async def test_material_qti_empty_quiz_yields_zip(
        self, test_db: Session, test_weekly_material: WeeklyMaterial
    ) -> None:
        # No quiz nodes → qti still produces a (valid, empty) zip, not an error.
        result = await export_registry.export(
            "qti", ExportScope.MATERIAL, str(test_weekly_material.id), test_db
        )
        assert result.media_type == "application/zip"
        assert result.filename.endswith("_qti.zip")
        assert zipfile.is_zipfile(result.buf)

    @pytest.mark.asyncio
    async def test_material_h5p_no_quiz_raises(
        self, test_db: Session, test_weekly_material: WeeklyMaterial
    ) -> None:
        with pytest.raises(ExportContentError):
            await export_registry.export(
                "h5p_question_set",
                ExportScope.MATERIAL,
                str(test_weekly_material.id),
                test_db,
            )


# ---------------------------------------------------------------------------
# Route layer: dispatch + ownership (get_user_material)
# ---------------------------------------------------------------------------


def _make_other_users_material(db: Session) -> WeeklyMaterial:
    """Create a material owned by a different user (for ownership checks)."""
    other = User(
        id=str(uuid.uuid4()),
        email=f"other-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="x",
        name="Other User",
        role="lecturer",
        is_verified=True,
        is_active=True,
    )
    db.add(other)
    db.flush()
    unit = Unit(
        id=str(uuid.uuid4()),
        title="Other Unit",
        code="OTHER999",
        year=2026,
        semester="semester_1",
        duration_weeks=12,
        owner_id=other.id,
        created_by_id=other.id,
    )
    db.add(unit)
    db.flush()
    material = WeeklyMaterial(
        id=str(uuid.uuid4()),
        unit_id=unit.id,
        week_number=1,
        title="Other Material",
        type="lecture",
        description="<p>secret</p>",
        order_index=0,
    )
    db.add(material)
    db.commit()
    return material


class TestExportRoutes:
    def test_unit_html_route(self, client, test_unit: Unit) -> None:
        resp = client.get(f"/api/units/{test_unit.id}/export/html")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")

    def test_material_html_route_owner_ok(
        self,
        client,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        resp = client.get(f"/api/materials/{test_weekly_material.id}/export/html")
        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]

    def test_unknown_format_404(self, client, test_unit: Unit) -> None:
        resp = client.get(f"/api/units/{test_unit.id}/export/bogus")
        assert resp.status_code == 404

    def test_unsupported_scope_404(
        self,
        client,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        # scorm is unit-only → material scope rejected
        resp = client.get(f"/api/materials/{test_weekly_material.id}/export/scorm")
        assert resp.status_code == 404

    def test_material_not_found_404(self, client) -> None:
        resp = client.get(f"/api/materials/{uuid.uuid4()}/export/html")
        assert resp.status_code == 404

    def test_other_users_material_denied(
        self,
        client,
        test_db: Session,
    ) -> None:
        other_material = _make_other_users_material(test_db)
        resp = client.get(f"/api/materials/{other_material.id}/export/html")
        assert resp.status_code == 404

    def test_bulk_materials_route_wins_precedence(
        self,
        client,
        test_unit: Unit,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        # /units/{id}/export/materials must hit the bulk zip route, NOT the
        # generic /export/{export_format} catch-all (which would 404 'materials').
        resp = client.get(f"/api/units/{test_unit.id}/export/materials")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/zip")
