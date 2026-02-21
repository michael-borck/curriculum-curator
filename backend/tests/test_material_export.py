"""
Unit tests for individual material export and bulk material ZIP export.

Tests validate:
- Single material export as HTML (with inline styles, no Pandoc)
- Single material export returns correct filename and media type
- Bulk ZIP export with week-folder structure
- Empty unit produces a valid (empty) ZIP
"""

from __future__ import annotations

import os
import zipfile
from io import BytesIO
from unittest.mock import Mock

import pytest

# Set test environment before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.models.unit import Unit
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic
from app.services.export_service import ExportFormat, ExportService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_query_chain(result, *, is_single: bool = False) -> Mock:
    """Create a mock query chain that supports .filter().order_by().all()/.first()."""
    chain = Mock()
    chain.filter.return_value = chain
    chain.order_by.return_value = chain
    if is_single:
        chain.all.return_value = result if isinstance(result, list) else [result]
        chain.first.return_value = result
    else:
        chain.all.return_value = result
        chain.first.return_value = result[0] if result else None
    return chain


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_unit() -> Mock:
    unit = Mock(spec=Unit)
    unit.id = "unit-001"
    unit.code = "COMP1001"
    unit.title = "Intro to Web Dev"
    unit.owner_id = "user-001"
    return unit


@pytest.fixture()
def sample_topics() -> list[Mock]:
    t1 = Mock(spec=WeeklyTopic)
    t1.id = "topic-001"
    t1.unit_id = "unit-001"
    t1.week_number = 1
    t1.topic_title = "HTML Basics"

    t2 = Mock(spec=WeeklyTopic)
    t2.id = "topic-002"
    t2.unit_id = "unit-001"
    t2.week_number = 2
    t2.topic_title = "CSS Fundamentals"

    return [t1, t2]


@pytest.fixture()
def sample_materials() -> list[Mock]:
    m1 = Mock(spec=WeeklyMaterial)
    m1.id = "mat-001"
    m1.unit_id = "unit-001"
    m1.week_number = 1
    m1.title = "HTML Lecture"
    m1.type = "lecture"
    m1.description = "<p>Introduction to HTML tags and structure.</p>"
    m1.order_index = 0

    m2 = Mock(spec=WeeklyMaterial)
    m2.id = "mat-002"
    m2.unit_id = "unit-001"
    m2.week_number = 2
    m2.title = "CSS Lecture"
    m2.type = "lecture"
    m2.description = "<p>Styling with CSS selectors.</p>"
    m2.order_index = 0

    return [m1, m2]


@pytest.fixture()
def mock_db_single_material(sample_materials: list[Mock]) -> Mock:
    """DB mock that returns a single material by ID."""
    db = Mock()
    mat = sample_materials[0]
    db.query.side_effect = lambda model: _make_query_chain(mat, is_single=True)
    return db


@pytest.fixture()
def mock_db_zip(
    sample_unit: Mock,
    sample_topics: list[Mock],
    sample_materials: list[Mock],
) -> Mock:
    """DB mock for bulk ZIP export."""
    db = Mock()
    models: dict[type, Mock] = {
        Unit: _make_query_chain(sample_unit, is_single=True),
        WeeklyTopic: _make_query_chain(sample_topics),
        WeeklyMaterial: _make_query_chain(sample_materials),
    }
    db.query.side_effect = lambda model: models.get(model, _make_query_chain([]))
    return db


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
        self, export_svc: ExportService, mock_db_single_material: Mock
    ) -> None:
        buf, _filename, _media_type = await export_svc.export_material(
            material_id="mat-001",
            db=mock_db_single_material,
            fmt=ExportFormat.HTML,
        )
        html = buf.read().decode("utf-8")
        assert "<!DOCTYPE html>" in html
        assert "<style>" in html
        assert "Introduction to HTML tags and structure." in html

    @pytest.mark.asyncio
    async def test_filename_and_media_type(
        self, export_svc: ExportService, mock_db_single_material: Mock
    ) -> None:
        _, filename, media_type = await export_svc.export_material(
            material_id="mat-001",
            db=mock_db_single_material,
            fmt=ExportFormat.HTML,
        )
        assert filename.endswith(".html")
        assert "html-lecture" in filename
        assert media_type == "text/html"

    @pytest.mark.asyncio
    async def test_title_in_html(
        self, export_svc: ExportService, mock_db_single_material: Mock
    ) -> None:
        buf, _, _ = await export_svc.export_material(
            material_id="mat-001",
            db=mock_db_single_material,
            fmt=ExportFormat.HTML,
        )
        html = buf.read().decode("utf-8")
        assert "HTML Lecture" in html

    @pytest.mark.asyncio
    async def test_material_not_found(self, export_svc: ExportService) -> None:
        db = Mock()
        db.query.return_value = _make_query_chain(None, is_single=True)
        with pytest.raises(ValueError, match="not found"):
            await export_svc.export_material(
                material_id="nonexistent",
                db=db,
                fmt=ExportFormat.HTML,
            )


# ---------------------------------------------------------------------------
# Bulk ZIP export tests
# ---------------------------------------------------------------------------


class TestExportMaterialsZip:
    """Test exporting all materials as a ZIP."""

    @pytest.mark.asyncio
    async def test_returns_valid_zip(
        self, export_svc: ExportService, mock_db_zip: Mock
    ) -> None:
        buf, filename = await export_svc.export_materials_zip(
            unit_id="unit-001",
            db=mock_db_zip,
            fmt=ExportFormat.HTML,
        )
        assert filename.endswith(".zip")
        with zipfile.ZipFile(buf) as zf:
            assert zf.testzip() is None  # no corrupt entries

    @pytest.mark.asyncio
    async def test_zip_contains_week_folders(
        self, export_svc: ExportService, mock_db_zip: Mock
    ) -> None:
        buf, _ = await export_svc.export_materials_zip(
            unit_id="unit-001",
            db=mock_db_zip,
            fmt=ExportFormat.HTML,
        )
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            # Should have week01 and week02 folders
            assert any("week01" in n for n in names)
            assert any("week02" in n for n in names)

    @pytest.mark.asyncio
    async def test_zip_contains_topic_slugs_in_folders(
        self, export_svc: ExportService, mock_db_zip: Mock
    ) -> None:
        buf, _ = await export_svc.export_materials_zip(
            unit_id="unit-001",
            db=mock_db_zip,
            fmt=ExportFormat.HTML,
        )
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert any("html-basics" in n for n in names)
            assert any("css-fundamentals" in n for n in names)

    @pytest.mark.asyncio
    async def test_zip_files_contain_html_content(
        self, export_svc: ExportService, mock_db_zip: Mock
    ) -> None:
        buf, _ = await export_svc.export_materials_zip(
            unit_id="unit-001",
            db=mock_db_zip,
            fmt=ExportFormat.HTML,
        )
        with zipfile.ZipFile(buf) as zf:
            for name in zf.namelist():
                content = zf.read(name).decode("utf-8")
                assert "<!DOCTYPE html>" in content

    @pytest.mark.asyncio
    async def test_empty_unit_produces_valid_zip(
        self, export_svc: ExportService
    ) -> None:
        unit = Mock(spec=Unit)
        unit.id = "unit-empty"
        unit.title = "Empty Unit"

        db = Mock()
        models: dict[type, Mock] = {
            Unit: _make_query_chain(unit, is_single=True),
            WeeklyTopic: _make_query_chain([]),
            WeeklyMaterial: _make_query_chain([]),
        }
        db.query.side_effect = lambda model: models.get(model, _make_query_chain([]))

        buf, filename = await export_svc.export_materials_zip(
            unit_id="unit-empty",
            db=db,
            fmt=ExportFormat.HTML,
        )
        assert filename.endswith(".zip")
        with zipfile.ZipFile(buf) as zf:
            assert zf.testzip() is None
            assert len(zf.namelist()) == 0

    @pytest.mark.asyncio
    async def test_unit_not_found(self, export_svc: ExportService) -> None:
        db = Mock()
        db.query.return_value = _make_query_chain(None, is_single=True)
        with pytest.raises(ValueError, match="not found"):
            await export_svc.export_materials_zip(
                unit_id="nonexistent",
                db=db,
                fmt=ExportFormat.HTML,
            )
