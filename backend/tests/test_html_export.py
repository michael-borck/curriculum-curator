"""
Tests for standalone HTML export service using in-memory SQLite.

Validates: HTML structure, content sections, filename generation,
learning outcomes, weekly materials, assessments, and inline styles.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from app.services.html_export_service import export_unit_html

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportBasics:
    """Test HTML structure and filename."""

    def test_export_returns_html_string(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_export_filename(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        _, filename = export_unit_html(str(populated_unit.id), test_db)
        assert filename.endswith(".html")
        assert "test1001" in filename.lower()

    def test_html_contains_title(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "TEST1001" in html
        assert "Introduction to Testing" in html

    def test_html_contains_unit_description(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "A unit for testing purposes" in html


class TestLearningOutcomes:
    """Test learning outcomes section."""

    def test_outcomes_section_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "Learning Outcomes" in html

    def test_outcome_codes_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "ULO1" in html
        assert "ULO2" in html

    def test_outcome_text_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "Analyze web technologies" in html
        assert "Create responsive web applications" in html

    def test_bloom_levels_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "ANALYZE" in html
        assert "CREATE" in html


class TestWeeklyMaterials:
    """Test weekly materials section."""

    def test_week_headings_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "Week 1" in html
        assert "HTML Basics" in html
        assert "Week 2" in html
        assert "CSS Fundamentals" in html

    def test_material_titles_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "HTML Lecture" in html
        assert "CSS Lecture" in html

    def test_material_content_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "Introduction to HTML tags and structure." in html
        assert "Styling with CSS selectors." in html


class TestAssessments:
    """Test assessments section."""

    def test_assessments_heading_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "Assessments" in html

    def test_assessment_titles_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "HTML Quiz" in html
        assert "Web Project" in html

    def test_assessment_weights_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "20.0%" in html
        assert "40.0%" in html


class TestInlineStyles:
    """Test that inline styles are present for standalone rendering."""

    def test_style_tag_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "<style>" in html

    def test_table_styles_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "border-collapse" in html

    def test_body_styles_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        html, _ = export_unit_html(str(populated_unit.id), test_db)
        assert "font-family" in html


class TestEdgeCases:
    """Test edge cases."""

    def test_nonexistent_unit_raises(self, test_db: Session) -> None:
        with pytest.raises(ValueError, match=r"Unit .* not found"):
            export_unit_html(str(uuid.uuid4()), test_db)

    def test_empty_unit_still_exports(
        self, test_db: Session, test_unit: Unit
    ) -> None:
        """A unit with no materials/assessments still exports valid HTML."""
        html, filename = export_unit_html(str(test_unit.id), test_db)
        assert "<!DOCTYPE html>" in html
        assert "Introduction to Testing" in html
        assert filename.endswith(".html")
