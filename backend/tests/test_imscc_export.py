"""
Tests for IMS Common Cartridge export service using in-memory SQLite.

Validates: ZIP structure, manifest XML, HTML generation, metadata JSON,
edge cases, and utility functions.
"""

from __future__ import annotations

import json
import uuid
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pytest

from app.services.imscc_service import IMSCCExportService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit
from app.services.unit_export_data import escape_html, slugify

NS_CP = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportBasics:
    """Test ZIP structure and filename."""

    def test_export_returns_valid_zip(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, filename = service.export_unit(str(populated_unit.id), test_db)
        assert "test1001" in filename.lower()
        assert filename.endswith(".imscc")
        assert zipfile.is_zipfile(buf)

    def test_zip_contains_required_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            assert "curriculum_curator_meta.json" in names
            assert "overview/learning_outcomes.html" in names
            assert "overview/accreditation.html" in names

    def test_zip_contains_weekly_material_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert any("week01" in n and "lecture" in n for n in names)

    def test_zip_contains_assessment_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert any("assessments/" in n for n in names)


class TestManifestXML:
    """Test imsmanifest.xml content and structure."""

    def _get_root(self, buf: BytesIO) -> ET.Element:
        with zipfile.ZipFile(buf, "r") as zf:
            return ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))

    def test_manifest_is_valid_xml(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        root = self._get_root(buf)
        assert root.tag == f"{{{NS_CP}}}manifest"
        schema_ver = root.find(f".//{{{NS_CP}}}schemaversion")
        assert schema_ver is not None
        assert schema_ver.text == "1.1.0"

    def test_manifest_has_organization_hierarchy(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        root = self._get_root(buf)
        org = root.find(f".//{{{NS_CP}}}organization")
        assert org is not None
        assert org.get("structure") == "rooted-hierarchy"

        titles = [t.text for t in root.iter(f"{{{NS_CP}}}title") if t.text]
        assert "Overview" in titles
        assert any("Week 1" in t for t in titles)
        assert "Assessments" in titles

    def test_manifest_resources_match_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            root = ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))
            names = set(zf.namelist())
            resources = root.findall(f".//{{{NS_CP}}}resource")
            assert len(resources) > 0
            for res in resources:
                href = res.get("href")
                assert href in names


class TestMetaJSON:
    """Test curriculum_curator_meta.json content."""

    def _load_meta(self, buf: BytesIO) -> dict[str, Any]:
        with zipfile.ZipFile(buf, "r") as zf:
            return json.loads(zf.read("curriculum_curator_meta.json").decode("utf-8"))

    def test_meta_json_valid_structure(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        assert meta["version"] == "1.0"
        assert meta["exported_from"] == "curriculum-curator"
        assert "exported_at" in meta
        assert "unit" in meta
        assert "learning_outcomes" in meta
        assert "aol_mappings" in meta
        assert "sdg_mappings" in meta

    def test_meta_json_unit_fields(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        unit_meta = meta["unit"]
        assert unit_meta["code"] == "TEST1001"
        assert unit_meta["year"] == 2026
        assert unit_meta["semester"] == "semester_1"
        assert unit_meta["duration_weeks"] == 12
        assert unit_meta["credit_points"] == 6

    def test_meta_json_outcomes(self, test_db: Session, populated_unit: Unit) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        outcomes = meta["learning_outcomes"]
        assert len(outcomes) == 2
        codes = {o["code"] for o in outcomes}
        assert "ULO1" in codes
        assert "ULO2" in codes


class TestManifestCategories:
    """Test category sub-headers in manifest XML."""

    def _get_root(self, buf: BytesIO) -> ET.Element:
        with zipfile.ZipFile(buf, "r") as zf:
            return ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))

    def test_manifest_category_subheaders(
        self, test_db: Session, test_user: Any
    ) -> None:
        """Export unit with categorized materials, verify XML nesting."""
        from app.models.unit import Unit as UnitModel
        from app.models.unit_outline import UnitOutline
        from app.models.weekly_material import WeeklyMaterial
        from app.models.weekly_topic import WeeklyTopic

        # Create a unit with categorized materials
        unit = UnitModel(
            id=str(uuid.uuid4()),
            title="Category Manifest Test",
            code="CATM001",
            year=2026,
            semester="semester_1",
            pedagogy_type="inquiry-based",
            difficulty_level="intermediate",
            duration_weeks=12,
            owner_id=str(test_user.id),
            created_by_id=str(test_user.id),
            credit_points=6,
        )
        test_db.add(unit)
        test_db.flush()

        outline = UnitOutline(
            unit_id=str(unit.id),
            title="Cat Test",
            duration_weeks=12,
            credit_points=6,
            status="planning",
            created_by_id=str(test_user.id),
        )
        test_db.add(outline)
        test_db.flush()

        topic = WeeklyTopic(
            unit_outline_id=str(outline.id),
            unit_id=str(unit.id),
            week_number=1,
            topic_title="Week with categories",
            created_by_id=str(test_user.id),
        )
        test_db.add(topic)
        test_db.flush()

        for i, (cat, title) in enumerate(
            [
                ("pre_class", "Pre Reading"),
                ("in_class", "Class Activity"),
                ("post_class", "Homework"),
            ]
        ):
            mat = WeeklyMaterial(
                unit_id=str(unit.id),
                week_number=1,
                title=title,
                type="lecture",
                category=cat,
                description=f"<p>{title} content</p>",
                order_index=i,
            )
            test_db.add(mat)
        test_db.commit()

        service = IMSCCExportService()
        buf, _ = service.export_unit(str(unit.id), test_db)
        root = self._get_root(buf)

        # Find week 1 item
        week_item = root.find(f".//{{{NS_CP}}}item[@identifier='week_01']")
        assert week_item is not None

        # Should have category sub-headers
        titles = [t.text for t in week_item.iter(f"{{{NS_CP}}}title") if t.text]
        assert "Pre-class" in titles
        assert "In-class" in titles
        assert "Post-class" in titles

    def test_manifest_no_subheaders_when_all_general(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        """All general materials → flat structure (no category sub-headers)."""
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        root = self._get_root(buf)

        # Find week 1 item
        week_item = root.find(f".//{{{NS_CP}}}item[@identifier='week_01']")
        assert week_item is not None

        # Should NOT have category sub-headers
        titles = [t.text for t in week_item.iter(f"{{{NS_CP}}}title") if t.text]
        assert "Pre-class" not in titles
        assert "In-class" not in titles
        assert "Post-class" not in titles


class TestHTMLContent:
    """Test generated HTML pages."""

    def test_learning_outcomes_html(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("overview/learning_outcomes.html").decode("utf-8")
            assert "ULO1" in html
            assert "ULO2" in html
            assert "ANALYZE" in html
            assert "CREATE" in html

    def test_accreditation_html_aol(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("overview/accreditation.html").decode("utf-8")
            assert "AOL2" in html

    def test_accreditation_html_gc_and_sdg(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            html = zf.read("overview/accreditation.html").decode("utf-8")
            assert "GC1" in html
            assert "SDG4" in html

    def test_material_html_has_structure(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            # Find a week01 material file
            week01_files = [
                n for n in zf.namelist() if "week01" in n and n.endswith(".html")
            ]
            assert len(week01_files) > 0
            html = zf.read(week01_files[0]).decode("utf-8")
            assert "<!DOCTYPE html>" in html
            assert "<style>" in html


class TestMetaJSONV2:
    """Test meta.json v2 fields (materials, assessments, weekly_topics)."""

    def _load_meta(self, buf: BytesIO) -> dict[str, Any]:
        with zipfile.ZipFile(buf, "r") as zf:
            return json.loads(zf.read("curriculum_curator_meta.json").decode("utf-8"))

    def test_meta_json_v2_has_materials(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        assert meta["meta_version"] == "2.0"
        assert "materials" in meta
        materials = meta["materials"]
        assert len(materials) == 3  # populated_unit has 3 materials
        for mat in materials:
            assert "id" in mat
            assert "week_number" in mat
            assert "title" in mat
            assert "type" in mat
            assert "category" in mat
            assert "order_index" in mat
            assert "href" in mat

    def test_meta_json_v2_has_assessments(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        assessments = meta["assessments"]
        assert len(assessments) == 2  # populated_unit has 2 assessments
        for a in assessments:
            assert "id" in a
            assert "title" in a
            assert "type" in a
            assert "category" in a
            assert "weight" in a
            assert "href" in a

    def test_meta_json_v2_has_weekly_topics(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        topics = meta["weekly_topics"]
        assert len(topics) == 3  # populated_unit has 3 weekly topics
        for t in topics:
            assert "week_number" in t
            assert "topic_title" in t
            assert "week_type" in t

    def test_meta_json_v2_backward_compat(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        # v1 compat fields still present
        assert meta["version"] == "1.0"
        assert "unit" in meta
        assert "learning_outcomes" in meta
        assert "aol_mappings" in meta
        assert "sdg_mappings" in meta


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_export_empty_unit(self, test_db: Session, test_unit: Unit) -> None:
        """Unit with no materials/outcomes still produces valid ZIP."""
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(test_unit.id), test_db)
        assert zipfile.is_zipfile(buf)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            assert "overview/learning_outcomes.html" in names

    def test_export_nonexistent_unit_raises(self, test_db: Session) -> None:
        service = IMSCCExportService()
        with pytest.raises(ValueError, match=r"Unit .* not found"):
            service.export_unit(str(uuid.uuid4()), test_db)

    def test_html_special_chars_escaped(self) -> None:
        assert (
            escape_html("<script>alert('xss')</script>")
            == "&lt;script&gt;alert('xss')&lt;/script&gt;"
        )
        assert escape_html('He said "hello"') == "He said &quot;hello&quot;"
        assert escape_html("A & B") == "A &amp; B"

    def test_slugify_special_characters(self) -> None:
        assert slugify("Hello World!") == "hello_world"
        assert slugify("Week 1: HTML & CSS") == "week_1_html_css"
        assert slugify("  spaced  ") == "spaced"

    def test_material_html_escapes_title(self) -> None:
        service = IMSCCExportService()
        html = service._material_to_html("<script>xss</script>", "safe content")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestH5PEmbedding:
    """Test H5P embedding when material export_format is h5p_question_set."""

    def test_h5p_material_produces_h5p_file_instead_of_qti(
        self, test_db: Session, test_user: Any
    ) -> None:
        """Material with export_format='h5p_question_set' embeds .h5p in ZIP."""
        from app.models.unit import Unit as UnitModel
        from app.models.unit_outline import UnitOutline
        from app.models.weekly_material import WeeklyMaterial
        from app.models.weekly_topic import WeeklyTopic

        unit = UnitModel(
            id=str(uuid.uuid4()),
            title="H5P Embed Test",
            code="H5P001",
            year=2026,
            semester="semester_1",
            pedagogy_type="inquiry-based",
            difficulty_level="intermediate",
            duration_weeks=12,
            owner_id=str(test_user.id),
            created_by_id=str(test_user.id),
            credit_points=6,
        )
        test_db.add(unit)
        test_db.flush()

        outline = UnitOutline(
            unit_id=str(unit.id),
            title="H5P Test",
            duration_weeks=12,
            credit_points=6,
            status="planning",
            created_by_id=str(test_user.id),
        )
        test_db.add(outline)
        test_db.flush()

        topic = WeeklyTopic(
            unit_outline_id=str(outline.id),
            unit_id=str(unit.id),
            week_number=1,
            topic_title="H5P Week",
            created_by_id=str(test_user.id),
        )
        test_db.add(topic)
        test_db.flush()

        # Material with quiz questions in content_json AND export_format=h5p
        mat = WeeklyMaterial(
            unit_id=str(unit.id),
            week_number=1,
            title="Interactive Quiz",
            type="lecture",
            description="<p>Quiz material</p>",
            order_index=0,
            export_format="h5p_question_set",
            content_json={
                "type": "doc",
                "content": [
                    {
                        "type": "quizQuestion",
                        "attrs": {
                            "questionType": "multiple_choice",
                            "questionText": "What is 2+2?",
                            "options": [
                                {"text": "3", "isCorrect": False},
                                {"text": "4", "isCorrect": True},
                            ],
                            "explanation": "Basic arithmetic",
                        },
                    }
                ],
            },
        )
        test_db.add(mat)
        test_db.commit()

        service = IMSCCExportService()
        buf, _ = service.export_unit(str(unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            # Should have H5P file, not QTI
            h5p_files = [n for n in names if n.startswith("h5p/") and n.endswith(".h5p")]
            qti_mat_files = [n for n in names if "qti_mat_" in n]
            assert len(h5p_files) == 1, f"Expected 1 H5P file, got: {h5p_files}"
            assert len(qti_mat_files) == 0, f"Expected no QTI mat files, got: {qti_mat_files}"

            # H5P file should be a valid ZIP itself
            h5p_data = zf.read(h5p_files[0])
            assert zipfile.is_zipfile(BytesIO(h5p_data))

            # Manifest should reference H5P resource as webcontent
            root = ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))
            h5p_resources = [
                r
                for r in root.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("h5p_")
            ]
            assert len(h5p_resources) == 1
            assert h5p_resources[0].get("type") == "webcontent"
