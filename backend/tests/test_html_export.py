"""
Unit tests for standalone HTML export service.

Tests validate: HTML structure, content sections, and filename generation.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import Mock

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
from app.services.html_export_service import export_unit_html


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
    m2.week_number = 2
    m2.title = "CSS Lecture"
    m2.type = "lecture"
    m2.description = "<p>Styling with CSS selectors.</p>"
    m2.order_index = 0

    return [m1, m2]


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
    a1.learning_outcomes = []

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

    # Mock ULO mapping on second assessment
    ulo_mock = Mock()
    ulo_mock.outcome_code = "ULO1"
    ulo_mock.id = "ulo-001"
    a2.learning_outcomes = [ulo_mock]

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
def export_result(mock_db: Mock) -> tuple[str, str]:
    return export_unit_html("unit-001", mock_db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportBasics:
    """Test HTML structure and filename."""

    def test_export_returns_html_string(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_export_filename(self, export_result: tuple[str, str]) -> None:
        _, filename = export_result
        assert filename == "COMP1001_intro_to_web_dev.html"

    def test_html_contains_title(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "COMP1001" in html
        assert "Intro to Web Dev" in html

    def test_html_contains_unit_description(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "Learn the fundamentals of web development" in html


class TestLearningOutcomes:
    """Test learning outcomes section."""

    def test_outcomes_section_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "Learning Outcomes" in html

    def test_outcome_codes_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "ULO1" in html
        assert "ULO2" in html

    def test_outcome_text_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "Analyze web technologies" in html
        assert "Create responsive web applications" in html

    def test_bloom_levels_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "ANALYZE" in html
        assert "CREATE" in html


class TestWeeklyMaterials:
    """Test weekly materials section."""

    def test_week_headings_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "Week 1: HTML Basics" in html
        assert "Week 2: CSS Fundamentals" in html

    def test_material_titles_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "HTML Lecture" in html
        assert "CSS Lecture" in html

    def test_material_content_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "Introduction to HTML tags and structure." in html
        assert "Styling with CSS selectors." in html


class TestAssessments:
    """Test assessments section."""

    def test_assessments_heading_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "Assessments" in html

    def test_assessment_titles_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "HTML Quiz" in html
        assert "Web Project" in html

    def test_assessment_weights_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "20%" in html
        assert "40%" in html

    def test_assessment_ulo_mappings(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        # Web Project assessment should show ULO1 mapping
        assert "ULO1" in html

    def test_assessment_due_weeks(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        # Due week 4 and 12 should appear in table cells
        assert ">4<" in html
        assert ">12<" in html


class TestInlineStyles:
    """Test that inline styles are present for standalone rendering."""

    def test_style_tag_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "<style>" in html

    def test_table_styles_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "border-collapse" in html

    def test_body_styles_present(self, export_result: tuple[str, str]) -> None:
        html, _ = export_result
        assert "font-family" in html


class TestEmptyUnit:
    """Test export with a unit that has no materials or assessments."""

    def test_empty_unit_still_exports(self) -> None:
        unit = Mock(spec=Unit)
        unit.id = "unit-empty"
        unit.code = "COMP0000"
        unit.title = "Empty Unit"
        unit.description = None

        db = Mock()
        single_models: dict[type, Mock] = {
            Unit: _make_query_chain(unit, is_single=True),
            UnitOutline: _make_query_chain(None, is_single=True),
        }
        list_models: dict[type, Mock] = {
            WeeklyTopic: _make_query_chain([]),
            WeeklyMaterial: _make_query_chain([]),
            Assessment: _make_query_chain([]),
            UnitLearningOutcome: _make_query_chain([]),
            UnitAoLMapping: _make_query_chain([]),
            UnitSDGMapping: _make_query_chain([]),
            ULOGraduateCapabilityMapping: _make_query_chain([]),
        }
        all_models: dict[type, Mock] = {**single_models, **list_models}
        db.query.side_effect = lambda model: all_models.get(model, _make_query_chain([]))

        html, filename = export_unit_html("unit-empty", db)
        assert "<!DOCTYPE html>" in html
        assert "Empty Unit" in html
        assert filename == "COMP0000_empty_unit.html"
