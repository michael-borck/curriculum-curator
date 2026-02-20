"""
Unit tests for IMS Common Cartridge export service.

Tests mock the DB session and validate: ZIP structure, manifest XML,
HTML generation, and metadata JSON.
"""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import Any
from unittest.mock import Mock, patch

import pytest

# Set test environment before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.models.accreditation_mappings import (
    ULOGraduateCapabilityMapping,
    UnitAoLMapping,
    UnitSDGMapping,
)
from app.models.assessment import Assessment
from app.models.learning_outcome import UnitLearningOutcome
from app.models.unit import Unit
from app.models.unit_outline import UnitOutline
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic
from app.services.imscc_service import IMSCCExportService, _escape_html, _slugify

NS_CP = "http://www.imsglobal.org/xsd/imsccv1p2/imscp_v1p1"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_unit() -> Mock:
    unit = Mock(spec=Unit)
    unit.id = "unit-001"
    unit.code = "COMP1001"
    unit.title = "Intro to Web Dev"
    unit.description = "Learn the fundamentals of web development"
    unit.pedagogy_type = "project-based"
    unit.difficulty_level = "beginner"
    unit.year = 2026
    unit.semester = "semester_1"
    unit.duration_weeks = 12
    unit.credit_points = 6
    unit.status = "ACTIVE"
    return unit


@pytest.fixture()
def sample_outline(sample_unit: Mock) -> Mock:
    outline = Mock(spec=UnitOutline)
    outline.id = "outline-001"
    outline.unit_id = sample_unit.id
    outline.title = "Web Dev Outline"
    outline.description = "Course outline for Intro to Web Dev"
    outline.delivery_mode = "blended"
    return outline


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
    m2.week_number = 1
    m2.title = "HTML Activity"
    m2.type = "activity"
    m2.description = "<p>Build your first web page.</p>"
    m2.order_index = 1

    m3 = Mock(spec=WeeklyMaterial)
    m3.id = "mat-003"
    m3.unit_id = "unit-001"
    m3.week_number = 2
    m3.title = "CSS Lecture"
    m3.type = "lecture"
    m3.description = "<p>Styling with CSS selectors.</p>"
    m3.order_index = 0

    return [m1, m2, m3]


@pytest.fixture()
def sample_assessments() -> list[Mock]:
    a1 = Mock(spec=Assessment)
    a1.id = "assess-001"
    a1.unit_id = "unit-001"
    a1.title = "HTML Quiz"
    a1.type = "FORMATIVE"
    a1.category = "QUIZ"
    a1.weight = 20
    a1.description = "Short quiz on HTML fundamentals"
    a1.due_week = 4
    a1.duration = "30 minutes"
    a1.submission_type = "ONLINE"
    a1.group_work = False
    a1.specification = None

    a2 = Mock(spec=Assessment)
    a2.id = "assess-002"
    a2.unit_id = "unit-001"
    a2.title = "Web Project"
    a2.type = "SUMMATIVE"
    a2.category = "PROJECT"
    a2.weight = 40
    a2.description = "Build a complete website"
    a2.due_week = 12
    a2.duration = None
    a2.submission_type = "ONLINE"
    a2.group_work = True
    a2.specification = "<h3>Requirements</h3><p>Build a responsive site.</p>"

    return [a1, a2]


@pytest.fixture()
def sample_outcomes() -> list[Mock]:
    o1 = Mock(spec=UnitLearningOutcome)
    o1.id = "ulo-001"
    o1.unit_id = "unit-001"
    o1.outcome_code = "ULO1"
    o1.outcome_text = "Analyze web technologies and their applications"
    o1.bloom_level = "ANALYZE"
    o1.sequence_order = 1

    o2 = Mock(spec=UnitLearningOutcome)
    o2.id = "ulo-002"
    o2.unit_id = "unit-001"
    o2.outcome_code = "ULO2"
    o2.outcome_text = "Create responsive web applications"
    o2.bloom_level = "CREATE"
    o2.sequence_order = 2

    return [o1, o2]


@pytest.fixture()
def sample_aol() -> list[Mock]:
    m = Mock(spec=UnitAoLMapping)
    m.id = "aol-001"
    m.unit_id = "unit-001"
    m.competency_code = "AOL2"
    m.level = "R"
    m.notes = "Critical thinking reinforced"
    return [m]


@pytest.fixture()
def sample_sdg() -> list[Mock]:
    s = Mock(spec=UnitSDGMapping)
    s.id = "sdg-001"
    s.unit_id = "unit-001"
    s.sdg_code = "SDG4"
    s.notes = "Quality Education"
    return [s]


@pytest.fixture()
def sample_gc() -> list[Mock]:
    gc = Mock(spec=ULOGraduateCapabilityMapping)
    gc.id = "gc-001"
    gc.ulo_id = "ulo-001"
    gc.capability_code = "GC1"
    gc.notes = None
    return [gc]


def _make_query_chain(result: Any, *, is_single: bool = False) -> Mock:
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


@pytest.fixture()
def mock_db(
    sample_unit: Mock,
    sample_outline: Mock,
    sample_topics: list[Mock],
    sample_materials: list[Mock],
    sample_assessments: list[Mock],
    sample_outcomes: list[Mock],
    sample_aol: list[Mock],
    sample_sdg: list[Mock],
    sample_gc: list[Mock],
) -> Mock:
    db = Mock()

    # Map each model class to its mock query chain
    single_models: dict[type, Mock] = {
        Unit: _make_query_chain(sample_unit, is_single=True),
        UnitOutline: _make_query_chain(sample_outline, is_single=True),
    }
    list_models: dict[type, Mock] = {
        WeeklyTopic: _make_query_chain(sample_topics),
        WeeklyMaterial: _make_query_chain(sample_materials),
        Assessment: _make_query_chain(sample_assessments),
        UnitLearningOutcome: _make_query_chain(sample_outcomes),
        UnitAoLMapping: _make_query_chain(sample_aol),
        UnitSDGMapping: _make_query_chain(sample_sdg),
        ULOGraduateCapabilityMapping: _make_query_chain(sample_gc),
    }
    all_models: dict[type, Mock] = {**single_models, **list_models}

    db.query.side_effect = lambda model: all_models.get(model, _make_query_chain([]))
    return db


@pytest.fixture()
def export_result(mock_db: Mock) -> tuple[BytesIO, str]:
    service = IMSCCExportService()
    return service.export_unit("unit-001", mock_db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportBasics:
    """Test ZIP structure and filename."""

    def test_export_returns_valid_zip(self, export_result: tuple[BytesIO, str]) -> None:
        buf, filename = export_result
        assert filename == "COMP1001_intro_to_web_dev.imscc"
        assert zipfile.is_zipfile(buf)

    def test_zip_contains_required_files(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            assert "curriculum_curator_meta.json" in names
            assert "overview/learning_outcomes.html" in names
            assert "overview/accreditation.html" in names

    def test_zip_contains_weekly_material_files(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "week01/lecture_html_lecture.html" in names
            assert "week01/activity_html_activity.html" in names
            assert "week02/lecture_css_lecture.html" in names

    def test_zip_contains_assessment_files(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "assessments/assessment_1.html" in names
            assert "assessments/assessment_2.html" in names


class TestManifestXML:
    """Test imsmanifest.xml content and structure."""

    def test_manifest_is_valid_xml(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            xml_content = zf.read("imsmanifest.xml").decode("utf-8")
            root = ET.fromstring(xml_content)
            assert root.tag == f"{{{NS_CP}}}manifest"
            # Check schema version
            schema_ver = root.find(f".//{{{NS_CP}}}schemaversion")
            assert schema_ver is not None
            assert schema_ver.text == "1.2.0"

    def test_manifest_has_organization_hierarchy(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            root = ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))

            org = root.find(f".//{{{NS_CP}}}organization")
            assert org is not None
            assert org.get("structure") == "rooted-hierarchy"

            # Check for expected items by title text
            titles = [t.text for t in root.iter(f"{{{NS_CP}}}title") if t.text]
            assert "Overview" in titles
            # Week titles should contain "Week 1" and "Week 2"
            assert any("Week 1" in t for t in titles)
            assert any("Week 2" in t for t in titles)
            assert "Assessments" in titles

    def test_manifest_resources_match_files(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            root = ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))
            names = set(zf.namelist())

            resources = root.findall(f".//{{{NS_CP}}}resource")
            assert len(resources) > 0
            for res in resources:
                href = res.get("href")
                assert href in names, f"Resource href '{href}' not found in ZIP"


class TestMetaJSON:
    """Test curriculum_curator_meta.json content."""

    def _load_meta(self, export_result: tuple[BytesIO, str]) -> dict[str, Any]:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            return json.loads(zf.read("curriculum_curator_meta.json").decode("utf-8"))

    def test_meta_json_valid_structure(self, export_result: tuple[BytesIO, str]) -> None:
        meta = self._load_meta(export_result)
        assert meta["version"] == "1.0"
        assert meta["exported_from"] == "curriculum-curator"
        assert "exported_at" in meta
        assert "unit" in meta
        assert "learning_outcomes" in meta
        assert "aol_mappings" in meta
        assert "sdg_mappings" in meta

    def test_meta_json_unit_fields(self, export_result: tuple[BytesIO, str]) -> None:
        meta = self._load_meta(export_result)
        unit = meta["unit"]
        assert unit["code"] == "COMP1001"
        assert unit["title"] == "Intro to Web Dev"
        assert unit["pedagogy_type"] == "project-based"
        assert unit["year"] == 2026
        assert unit["semester"] == "semester_1"
        assert unit["duration_weeks"] == 12
        assert unit["credit_points"] == 6

    def test_meta_json_outcomes(self, export_result: tuple[BytesIO, str]) -> None:
        meta = self._load_meta(export_result)
        outcomes = meta["learning_outcomes"]
        assert len(outcomes) == 2

        assert outcomes[0]["code"] == "ULO1"
        assert outcomes[0]["bloom_level"] == "ANALYZE"
        assert "GC1" in outcomes[0]["graduate_capabilities"]

        assert outcomes[1]["code"] == "ULO2"
        assert outcomes[1]["bloom_level"] == "CREATE"


class TestHTMLContent:
    """Test generated HTML pages."""

    def test_learning_outcomes_html(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("overview/learning_outcomes.html").decode("utf-8")
            assert "ULO1" in html
            assert "ULO2" in html
            assert "ANALYZE" in html
            assert "CREATE" in html
            assert "<table>" in html

    def test_accreditation_html_aol(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("overview/accreditation.html").decode("utf-8")
            assert "AOL2" in html
            assert ">R<" in html

    def test_accreditation_html_gc_and_sdg(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("overview/accreditation.html").decode("utf-8")
            assert "GC1" in html
            assert "SDG4" in html

    def test_material_html_has_structure(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("week01/lecture_html_lecture.html").decode("utf-8")
            assert "<!DOCTYPE html>" in html
            assert "<h1>" in html
            assert "HTML Lecture" in html
            assert "<style>" in html

    def test_assessment_html_has_details(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("assessments/assessment_1.html").decode("utf-8")
            assert "20%" in html
            assert "FORMATIVE" in html
            assert "QUIZ" in html

    def test_assessment_with_spec_and_group_work(self, export_result: tuple[BytesIO, str]) -> None:
        buf, _ = export_result
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("assessments/assessment_2.html").decode("utf-8")
            assert "Group Work" in html
            assert "Specification" in html
            assert "responsive site" in html


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_export_empty_unit(self, sample_unit: Mock, sample_outline: Mock) -> None:
        """Unit with no materials/outcomes still produces valid ZIP."""
        db = Mock()

        def query_side_effect(model: type) -> Mock:
            if model is Unit:
                return _make_query_chain(sample_unit, is_single=True)
            if model is UnitOutline:
                return _make_query_chain(sample_outline, is_single=True)
            return _make_query_chain([])

        db.query.side_effect = query_side_effect

        service = IMSCCExportService()
        buf, _filename = service.export_unit("unit-001", db)

        assert zipfile.is_zipfile(buf)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            assert "overview/learning_outcomes.html" in names
            assert "overview/accreditation.html" in names
            # Empty unit should still have valid overview pages
            html = zf.read("overview/learning_outcomes.html").decode("utf-8")
            assert "No learning outcomes defined" in html

    def test_export_nonexistent_unit_raises(self) -> None:
        """ValueError when db returns None for unit."""
        db = Mock()

        chain = Mock()
        chain.filter.return_value = chain
        chain.first.return_value = None
        db.query.return_value = chain

        service = IMSCCExportService()
        with pytest.raises(ValueError, match=r"Unit .* not found"):
            service.export_unit("nonexistent", db)

    def test_html_special_chars_escaped(self) -> None:
        """<script> in title becomes &lt;script&gt; via _escape_html."""
        assert _escape_html("<script>alert('xss')</script>") == "&lt;script&gt;alert('xss')&lt;/script&gt;"
        assert _escape_html('He said "hello"') == "He said &quot;hello&quot;"
        assert _escape_html("A & B") == "A &amp; B"

    def test_slugify_special_characters(self) -> None:
        """Slugify produces URL-safe strings."""
        assert _slugify("Hello World!") == "hello_world"
        assert _slugify("Week 1: HTML & CSS") == "week_1_html_css"
        assert _slugify("  spaced  ") == "spaced"

    def test_material_html_escapes_title(self) -> None:
        """Material titles with HTML chars are escaped in the output."""
        service = IMSCCExportService()
        html = service._material_to_html("<script>xss</script>", "safe content")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
