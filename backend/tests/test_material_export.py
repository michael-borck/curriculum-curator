"""
Tests for individual material export and bulk material ZIP export
using in-memory SQLite.

Validates:
- Single material export as HTML (with inline styles, no Pandoc)
- Single material export returns correct filename and media type
- Bulk ZIP export with week-folder structure
- Empty unit produces a valid (empty) ZIP
"""

from __future__ import annotations

import uuid
import zipfile
from typing import TYPE_CHECKING

import pytest

from app.services.export_service import ExportFormat, ExportService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit
    from app.models.weekly_material import WeeklyMaterial


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def export_svc() -> ExportService:
    return ExportService()


# ---------------------------------------------------------------------------
# Single material export tests
# ---------------------------------------------------------------------------


class TestExportMaterialHTML:
    """Test exporting a single material as HTML."""

    @pytest.mark.asyncio
    async def test_returns_html_with_inline_styles(
        self,
        export_svc: ExportService,
        test_db: Session,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        buf, _filename, _media_type = await export_svc.export_material(
            material_id=str(test_weekly_material.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        html = buf.read().decode("utf-8")
        assert "<!DOCTYPE html>" in html
        assert "<style>" in html
        assert "Introduction to HTML tags and structure." in html

    @pytest.mark.asyncio
    async def test_filename_and_media_type(
        self,
        export_svc: ExportService,
        test_db: Session,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        _, filename, media_type = await export_svc.export_material(
            material_id=str(test_weekly_material.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        assert filename.endswith(".html")
        assert "html-lecture" in filename
        assert media_type == "text/html"

    @pytest.mark.asyncio
    async def test_title_in_html(
        self,
        export_svc: ExportService,
        test_db: Session,
        test_weekly_material: WeeklyMaterial,
    ) -> None:
        buf, _, _ = await export_svc.export_material(
            material_id=str(test_weekly_material.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        html = buf.read().decode("utf-8")
        assert "HTML Lecture" in html

    @pytest.mark.asyncio
    async def test_material_not_found(
        self, export_svc: ExportService, test_db: Session
    ) -> None:
        with pytest.raises(ValueError, match="not found"):
            await export_svc.export_material(
                material_id=str(uuid.uuid4()),
                db=test_db,
                fmt=ExportFormat.HTML,
            )


# ---------------------------------------------------------------------------
# Bulk ZIP export tests
# ---------------------------------------------------------------------------


class TestExportMaterialsZip:
    """Test exporting all materials as a ZIP."""

    @pytest.mark.asyncio
    async def test_returns_valid_zip(
        self, export_svc: ExportService, test_db: Session, populated_unit: Unit
    ) -> None:
        buf, filename = await export_svc.export_materials_zip(
            unit_id=str(populated_unit.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        assert filename.endswith(".zip")
        with zipfile.ZipFile(buf) as zf:
            assert zf.testzip() is None

    @pytest.mark.asyncio
    async def test_zip_contains_week_folders(
        self, export_svc: ExportService, test_db: Session, populated_unit: Unit
    ) -> None:
        buf, _ = await export_svc.export_materials_zip(
            unit_id=str(populated_unit.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert any("week01" in n for n in names)
            assert any("week02" in n for n in names)

    @pytest.mark.asyncio
    async def test_zip_contains_topic_slugs_in_folders(
        self, export_svc: ExportService, test_db: Session, populated_unit: Unit
    ) -> None:
        buf, _ = await export_svc.export_materials_zip(
            unit_id=str(populated_unit.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert any("html-basics" in n for n in names)
            assert any("css-fundamentals" in n for n in names)

    @pytest.mark.asyncio
    async def test_zip_files_contain_html_content(
        self, export_svc: ExportService, test_db: Session, populated_unit: Unit
    ) -> None:
        buf, _ = await export_svc.export_materials_zip(
            unit_id=str(populated_unit.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        with zipfile.ZipFile(buf) as zf:
            for name in zf.namelist():
                content = zf.read(name).decode("utf-8")
                assert "<!DOCTYPE html>" in content

    @pytest.mark.asyncio
    async def test_empty_unit_produces_valid_zip(
        self, export_svc: ExportService, test_db: Session, test_unit: Unit
    ) -> None:
        """Unit with no materials produces a valid empty ZIP."""
        buf, filename = await export_svc.export_materials_zip(
            unit_id=str(test_unit.id),
            db=test_db,
            fmt=ExportFormat.HTML,
        )
        assert filename.endswith(".zip")
        with zipfile.ZipFile(buf) as zf:
            assert zf.testzip() is None
            assert len(zf.namelist()) == 0

    @pytest.mark.asyncio
    async def test_unit_not_found(
        self, export_svc: ExportService, test_db: Session
    ) -> None:
        with pytest.raises(ValueError, match="not found"):
            await export_svc.export_materials_zip(
                unit_id=str(uuid.uuid4()),
                db=test_db,
                fmt=ExportFormat.HTML,
            )
