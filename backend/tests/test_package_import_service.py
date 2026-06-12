"""
Unit tests for PackageImportService pure-logic helpers and edge cases.

Complements the integration suites:
- tests/test_imscc_round_trip.py — export → import → re-export fidelity
- tests/test_canvas_import.py — Canvas detection, filebase tokens, module_meta

This file isolates manifest parsing, format detection, HTML extraction,
metadata inference, week-number detection, and malformed-package handling
using small in-memory ZIPs (no binary fixtures).
"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import ParseError

import pytest

from app.services.package_import_service import (
    PackageImportError,
    PackageImportService,
    _read_resource_content,
    classify_item,
    detect_blackboard_content_areas,
    detect_format_from_manifest,
    detect_source_lms,
    has_meta,
    parse_manifest,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.user import User

# ---------------------------------------------------------------------------
# In-memory package builders
# ---------------------------------------------------------------------------

IMS_NS = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"


def _zip_bytes(files: dict[str, str | bytes]) -> bytes:
    """Build an in-memory ZIP from a {path: content} mapping."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return buf.getvalue()


def _open_zip(files: dict[str, str | bytes]) -> zipfile.ZipFile:
    """Build an in-memory ZIP and return it opened for reading."""
    return zipfile.ZipFile(BytesIO(_zip_bytes(files)), "r")


GENERIC_MANIFEST = f"""<?xml version='1.0' encoding='UTF-8'?>
<manifest xmlns="{IMS_NS}" identifier="pkg_generic">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
  </metadata>
  <organizations>
    <organization identifier="org_1">
      <title>ICT2010 Web Development</title>
      <item identifier="week_1">
        <title>Week 1: Introduction</title>
        <item identifier="i1" identifierref="r1"><title>Lecture Slides</title></item>
        <item identifier="i2" identifierref="r2"><title>Quiz 1</title></item>
      </item>
      <item identifier="week_2">
        <title>Week 2: HTML</title>
        <item identifier="i3" identifierref="r3"><title>Reading: Chapter 2</title></item>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="r1" type="webcontent" href="week1/lecture.html"/>
    <resource identifier="r2" type="imsqti_xmlv1p2/imscc_xmlv1p1/assessment" href="quiz1/quiz.xml"/>
    <resource identifier="r3" type="webcontent" href="week2/reading.html"/>
  </resources>
</manifest>"""

CATEGORY_MANIFEST = f"""<?xml version='1.0' encoding='UTF-8'?>
<manifest xmlns="{IMS_NS}" identifier="pkg_cat">
  <organizations>
    <organization identifier="org_1">
      <title>Plain Course</title>
      <item identifier="week_1">
        <title>Week 1: Foundations</title>
        <item identifier="sub1">
          <title>Pre-Class</title>
          <item identifier="i1" identifierref="r1"><title>Reading: Chapter 1</title></item>
          <item identifier="i2" identifierref="r2"><title>Video Intro</title></item>
        </item>
        <item identifier="sub2">
          <title>In-Class</title>
          <item identifier="i3" identifierref="r3"><title>Lecture Notes</title></item>
        </item>
        <item identifier="i4" identifierref="r4"><title>Quiz 1</title></item>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="r1" type="webcontent" href="files/reading1.html"/>
    <resource identifier="r2" type="webcontent" href="files/video1.html"/>
    <resource identifier="r3" type="webcontent" href="files/lecture1.html"/>
    <resource identifier="r4" type="webcontent" href="files/quiz1.html"/>
  </resources>
</manifest>"""

# Manifest used by the v1 round-trip path: week titles are extracted via
# regex from `identifier="week_NN"` items.
WEEK_TITLE_MANIFEST = f"""<?xml version='1.0' encoding='UTF-8'?>
<manifest xmlns="{IMS_NS}" identifier="pkg_v1">
  <organizations>
    <organization identifier="org_1">
      <item identifier="week_01">
        <title>Week 1: HTML Basics</title>
      </item>
      <item identifier="week_02">
        <title>Advanced Topics</title>
      </item>
    </organization>
  </organizations>
  <resources/>
</manifest>"""

V1_META: dict[str, Any] = {
    "unit": {
        "code": "ICT100",
        "title": "Intro to ICT",
        "pedagogy_type": "flipped",
        "difficulty_level": "beginner",
        "year": 2025,
        "semester": "semester_2",
        "duration_weeks": 2,
        "credit_points": 12,
    },
    "learning_outcomes": [
        {
            "code": "ULO1",
            "description": "Explain core web concepts",
            "bloom_level": "understand",
            "graduate_capabilities": ["GC1", "GC2"],
        },
        {"description": "Build simple pages"},
    ],
    "aol_mappings": [{"competency_code": "AOL2", "level": "R"}],
    "sdg_mappings": [{"sdg_code": "SDG4"}],
}

LECTURE_HTML = """<!DOCTYPE html>
<html><head><title>HTML Lecture</title></head>
<body><h1>HTML Lecture</h1><p>Tags and structure.</p></body></html>"""

ASSESSMENT_HTML = """<!DOCTYPE html>
<html><head><title>HTML Quiz</title></head>
<body>
<h1>HTML Quiz</h1>
<p>Short quiz on fundamentals</p>
<table>
<tr><td>Type</td><td>formative</td></tr>
<tr><td>Category</td><td>quiz</td></tr>
<tr><td>Weight</td><td>20%</td></tr>
<tr><td>Due Week</td><td>4</td></tr>
<tr><td>Duration</td><td>30 minutes</td></tr>
<tr><td>Submission</td><td>online</td></tr>
<tr><td>Group Work</td><td>No</td></tr>
</table>
<h2>Specification</h2>
<p>Answer all ten questions.</p>
</body></html>"""


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------


class TestFormatDetection:
    def test_has_meta(self) -> None:
        with_meta = _open_zip({"curriculum_curator_meta.json": "{}"})
        without_meta = _open_zip({"imsmanifest.xml": GENERIC_MANIFEST})
        assert has_meta(with_meta) is True
        assert has_meta(without_meta) is False

    def test_scorm_detected_from_adlnet_namespace(self) -> None:
        scorm_manifest = """<?xml version='1.0'?>
<manifest xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2">
  <metadata><schema>ADL SCORM</schema></metadata>
</manifest>"""
        zf = _open_zip({"imsmanifest.xml": scorm_manifest})
        assert detect_format_from_manifest(zf) == "scorm_1.2"

    def test_imscc_default_without_scorm_markers(self) -> None:
        zf = _open_zip({"imsmanifest.xml": GENERIC_MANIFEST})
        assert detect_format_from_manifest(zf) == "imscc"

    def test_imscc_default_when_manifest_missing(self) -> None:
        zf = _open_zip({"week01/lecture_intro.html": LECTURE_HTML})
        assert detect_format_from_manifest(zf) == "imscc"


# ---------------------------------------------------------------------------
# Source LMS detection
# ---------------------------------------------------------------------------


class TestSourceLmsDetection:
    @pytest.mark.parametrize(
        ("manifest_text", "expected"),
        [
            ("<manifest>exported by Instructure Canvas</manifest>", "canvas"),
            ("<manifest>MOODLE backup</manifest>", "moodle"),
            ("<manifest>Blackboard Learn export</manifest>", "blackboard"),
            ("<manifest>D2L Brightspace</manifest>", "brightspace"),
            ("<manifest>generated by d2l tools</manifest>", "brightspace"),
            ("<manifest>plain vanilla cartridge</manifest>", None),
        ],
    )
    def test_keyword_detection(self, manifest_text: str, expected: str | None) -> None:
        assert detect_source_lms(manifest_text) == expected

    def test_blackboard_content_areas_detected(self) -> None:
        bb_manifest = f"""<?xml version='1.0'?>
<manifest xmlns="{IMS_NS}" identifier="bb">
  <organizations>
    <organization identifier="org_1">
      <title>BB Course</title>
      <item identifier="a1"><title>Course Information</title></item>
      <item identifier="a2"><title>Assignments</title></item>
      <item identifier="a3"><title>Week 1: Intro</title></item>
    </organization>
  </organizations>
  <resources/>
</manifest>"""
        manifest = parse_manifest(_open_zip({"imsmanifest.xml": bb_manifest}))
        areas = detect_blackboard_content_areas(manifest)
        assert areas == ["Course Information", "Assignments"]

    def test_no_blackboard_content_areas_returns_none(self) -> None:
        manifest = parse_manifest(_open_zip({"imsmanifest.xml": GENERIC_MANIFEST}))
        assert detect_blackboard_content_areas(manifest) is None


# ---------------------------------------------------------------------------
# Item classification
# ---------------------------------------------------------------------------


class TestClassifyItem:
    @pytest.mark.parametrize(
        ("title", "expected_category"),
        [
            ("Quiz 1", "quiz"),
            ("Final Exam", "exam"),
            ("Assignment 2", "project"),
            ("Midterm Review Session", "exam"),
        ],
    )
    def test_assessment_keywords(self, title: str, expected_category: str) -> None:
        assert classify_item(title) == ("assessment", expected_category)

    def test_resource_type_hint_marks_assessment(self) -> None:
        kind, category = classify_item(
            "Mystery Item", "imsqti_xmlv1p2/imscc_xmlv1p1/assessment"
        )
        assert kind == "assessment"
        assert category == "other"

    @pytest.mark.parametrize(
        ("title", "expected_type"),
        [
            ("Lecture Slides", "lecture"),
            ("Reading: Chapter 2", "reading"),
            ("Video Walkthrough", "video"),
            ("Case Study: Acme Corp", "case_study"),
            ("Some Random Page", "resource"),
        ],
    )
    def test_material_keywords_and_default(
        self, title: str, expected_type: str
    ) -> None:
        assert classify_item(title) == ("material", expected_type)


# ---------------------------------------------------------------------------
# Manifest parsing
# ---------------------------------------------------------------------------


class TestParseManifest:
    def test_namespaced_manifest_structure(self) -> None:
        manifest = parse_manifest(_open_zip({"imsmanifest.xml": GENERIC_MANIFEST}))

        assert manifest.title == "ICT2010 Web Development"
        assert manifest.resource_map == {
            "r1": ("week1/lecture.html", "webcontent"),
            "r2": ("quiz1/quiz.xml", "imsqti_xmlv1p2/imscc_xmlv1p1/assessment"),
            "r3": ("week2/reading.html", "webcontent"),
        }
        assert len(manifest.top_items) == 2
        week1_title, week1_children = manifest.top_items[0]
        assert week1_title == "Week 1: Introduction"
        assert week1_children == [
            ("Lecture Slides", "week1/lecture.html", "webcontent", None),
            (
                "Quiz 1",
                "quiz1/quiz.xml",
                "imsqti_xmlv1p2/imscc_xmlv1p1/assessment",
                None,
            ),
        ]
        week2_title, week2_children = manifest.top_items[1]
        assert week2_title == "Week 2: HTML"
        assert week2_children == [
            ("Reading: Chapter 2", "week2/reading.html", "webcontent", None)
        ]

    def test_manifest_without_namespace(self) -> None:
        plain_manifest = """<?xml version='1.0'?>
<manifest identifier="m1">
  <organizations>
    <organization identifier="org">
      <title>SCORM Course</title>
      <item identifier="i1">
        <title>Module 1</title>
        <item identifier="c1" identifierref="r1"><title>Content Page</title></item>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="r1" type="webcontent" href="content/page.html"/>
  </resources>
</manifest>"""
        manifest = parse_manifest(_open_zip({"imsmanifest.xml": plain_manifest}))
        assert manifest.title == "SCORM Course"
        assert manifest.top_items == [
            ("Module 1", [("Content Page", "content/page.html", "webcontent", None)])
        ]

    def test_category_subheaders_flattened(self) -> None:
        """Three-level nesting (week → category sub-header → material) flattens
        grandchildren into the week with the detected category."""
        manifest = parse_manifest(_open_zip({"imsmanifest.xml": CATEGORY_MANIFEST}))

        assert len(manifest.top_items) == 1
        title, children = manifest.top_items[0]
        assert title == "Week 1: Foundations"
        assert children == [
            ("Reading: Chapter 1", "files/reading1.html", "webcontent", "pre_class"),
            ("Video Intro", "files/video1.html", "webcontent", "pre_class"),
            ("Lecture Notes", "files/lecture1.html", "webcontent", "in_class"),
            ("Quiz 1", "files/quiz1.html", "webcontent", None),
        ]

    def test_missing_manifest_returns_empty_data(self) -> None:
        manifest = parse_manifest(_open_zip({"other.txt": "hi"}))
        assert manifest.title == ""
        assert manifest.top_items == []
        assert manifest.resource_map == {}


# ---------------------------------------------------------------------------
# HTML extraction and filename inference
# ---------------------------------------------------------------------------


class TestHtmlExtraction:
    def test_extract_title_strips_h1_and_sanitizes(self) -> None:
        html = """<html><body>
<h1>Lecture One</h1>
<script>alert("x")</script>
<p onclick="evil()">Hello <strong>world</strong></p>
<iframe src="http://evil.example"></iframe>
</body></html>"""
        title, body = PackageImportService.extract_html_content(html)

        assert title == "Lecture One"
        assert "Lecture One" not in body  # h1 removed from body
        assert "<script" not in body
        assert "alert" not in body
        assert "<iframe" not in body  # disallowed tag neutralised
        assert "onclick" not in body  # disallowed attribute stripped
        assert "<strong>world</strong>" in body

    def test_extract_without_body_returns_empty_content(self) -> None:
        title, body = PackageImportService.extract_html_content(
            "<h1>Just a heading</h1><p>floating</p>"
        )
        assert title == "Just a heading"
        assert body == ""

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("lecture_intro.html", "lecture"),
            ("tutorial_forms.html", "tutorial"),
            ("workshop_git.html", "workshop"),
            # "reading" is a material type but not a valid session format prefix
            ("reading_notes.html", "resource"),
            ("no_prefix_match.html", "resource"),
            ("plain.html", "resource"),
        ],
    )
    def test_extract_material_type_from_filename(
        self, filename: str, expected: str
    ) -> None:
        svc = PackageImportService()
        assert svc._extract_material_type(filename) == expected

    def test_extract_week_titles_from_manifest(self) -> None:
        svc = PackageImportService()
        zf = _open_zip({"imsmanifest.xml": WEEK_TITLE_MANIFEST})
        titles = svc._extract_week_titles_from_manifest(zf)
        # "Week N:" prefix is stripped; plain titles are kept verbatim
        assert titles == {1: "HTML Basics", 2: "Advanced Topics"}

    def test_parse_assessment_html_full_property_table(self) -> None:
        svc = PackageImportService()
        data = svc._parse_assessment_html(ASSESSMENT_HTML)

        assert data["title"] == "HTML Quiz"
        assert data["description"] == "Short quiz on fundamentals"
        assert data["type"] == "formative"
        assert data["category"] == "quiz"
        assert data["weight"] == 20.0
        assert data["due_week"] == 4
        assert data["duration"] == "30 minutes"
        assert data["submission_type"] == "online"
        assert data["group_work"] is False
        assert "Answer all ten questions." in data["specification"]

    def test_parse_assessment_html_tolerates_bad_values(self) -> None:
        html = """<html><body>
<h1>Vague Assessment</h1>
<table>
<tr><td>Weight</td><td>TBA</td></tr>
<tr><td>Due Week</td><td>week four</td></tr>
<tr><td>Group Work</td><td>Yes</td></tr>
<tr><td>only-one-cell</td></tr>
</table>
</body></html>"""
        svc = PackageImportService()
        data = svc._parse_assessment_html(html)

        assert data["title"] == "Vague Assessment"
        assert data["weight"] == 0.0  # unparseable percentage defaults to 0
        assert "due_week" not in data  # non-integer week suppressed
        assert data["group_work"] is True
        assert "description" not in data  # no <p> before the table

    def test_read_resource_content_path_fallbacks(self) -> None:
        zf = _open_zip({"web_resources/page.html": "<p>X</p>"})
        # Exact path
        assert _read_resource_content(zf, "web_resources/page.html") == "<p>X</p>"
        # Leading slash stripped
        assert _read_resource_content(zf, "/web_resources/page.html") == "<p>X</p>"
        # Basename fallback when directory differs
        assert _read_resource_content(zf, "wiki_content/page.html") == "<p>X</p>"
        # Missing file returns empty string
        assert _read_resource_content(zf, "missing.html") == ""


# ---------------------------------------------------------------------------
# analyze_package — previews and malformed packages
# ---------------------------------------------------------------------------


class TestAnalyzePackage:
    def test_invalid_zip_raises(self) -> None:
        svc = PackageImportService()
        with pytest.raises(PackageImportError, match="Invalid ZIP"):
            svc.analyze_package(b"this is not a zip archive")

    def test_zip_without_manifest_or_meta_raises(self) -> None:
        svc = PackageImportService()
        zip_bytes = _zip_bytes({"random.txt": "hello"})
        with pytest.raises(PackageImportError, match=r"imsmanifest\.xml"):
            svc.analyze_package(zip_bytes)

    def test_malformed_meta_json_raises(self) -> None:
        svc = PackageImportService()
        zip_bytes = _zip_bytes({"curriculum_curator_meta.json": "{not json"})
        with pytest.raises(PackageImportError, match=r"Failed to parse meta\.json"):
            svc.analyze_package(zip_bytes)

    def test_meta_missing_unit_section_raises(self) -> None:
        svc = PackageImportService()
        zip_bytes = _zip_bytes(
            {"curriculum_curator_meta.json": json.dumps({"foo": "bar"})}
        )
        with pytest.raises(PackageImportError, match="missing 'unit'"):
            svc.analyze_package(zip_bytes)

    def test_malformed_manifest_xml_raises_parse_error(self) -> None:
        """Documents current behavior: malformed manifest XML leaks a raw
        ParseError instead of being wrapped in PackageImportError."""
        svc = PackageImportService()
        zip_bytes = _zip_bytes({"imsmanifest.xml": "<manifest><unclosed"})
        with pytest.raises(ParseError):
            svc.analyze_package(zip_bytes)

    def test_round_trip_preview_counts_and_week_detection(self) -> None:
        svc = PackageImportService()
        zip_bytes = _zip_bytes(
            {
                "curriculum_curator_meta.json": json.dumps(V1_META),
                "week01/lecture_intro.html": LECTURE_HTML,
                "week02/tutorial_forms.html": LECTURE_HTML,
                # Single-digit week folder does not match weekNN detection
                "week1/skip_me.html": LECTURE_HTML,
                # Non-HTML files in week folders are not materials
                "week01/notes.txt": "plain text",
                "assessments/quiz1.html": ASSESSMENT_HTML,
                "assessments/data.json": "{}",
            }
        )

        preview = svc.analyze_package(zip_bytes)

        assert preview.is_round_trip is True
        assert preview.format == "imscc"
        assert preview.unit_code == "ICT100"
        assert preview.unit_title == "Intro to ICT"
        assert preview.pedagogy_type == "flipped"
        assert preview.difficulty_level == "beginner"
        assert preview.year == 2025
        assert preview.semester == "semester_2"
        assert preview.duration_weeks == 2
        assert preview.credit_points == 12
        assert preview.ulo_count == 2
        assert preview.gc_mapping_count == 2
        assert preview.aol_mapping_count == 1
        assert preview.sdg_mapping_count == 1
        assert preview.material_count == 2
        assert preview.assessment_count == 1

    def test_generic_preview_infers_metadata(self) -> None:
        svc = PackageImportService()
        zip_bytes = _zip_bytes({"imsmanifest.xml": GENERIC_MANIFEST})

        preview = svc.analyze_package(zip_bytes)

        assert preview.is_round_trip is False
        assert preview.format == "imscc"
        assert preview.source_lms is None
        # Unit code inferred from the organization title
        assert preview.unit_code == "ICT2010"
        assert preview.unit_title == "ICT2010 Web Development"
        # One week per top-level manifest item
        assert preview.duration_weeks == 2
        assert preview.material_count == 2
        assert preview.assessment_count == 1
        assert preview.ulo_count == 0


# ---------------------------------------------------------------------------
# create_unit_from_package — DB-backed paths not covered by round-trip tests
# ---------------------------------------------------------------------------


class TestCreateUnitFromPackage:
    def test_v1_round_trip_fallback_creates_full_unit(
        self, test_db: Session, test_user: User
    ) -> None:
        """v1 meta.json (no meta_version) falls back to scanning week folders
        and assessment HTML instead of reading materials from meta."""
        from app.models.accreditation_mappings import (
            ULOGraduateCapabilityMapping,
            UnitAoLMapping,
            UnitSDGMapping,
        )
        from app.models.assessment import Assessment
        from app.models.learning_outcome import UnitLearningOutcome
        from app.models.unit import Unit
        from app.models.weekly_material import WeeklyMaterial
        from app.models.weekly_topic import WeeklyTopic

        svc = PackageImportService()
        zip_bytes = _zip_bytes(
            {
                "curriculum_curator_meta.json": json.dumps(V1_META),
                "imsmanifest.xml": WEEK_TITLE_MANIFEST,
                "week01/lecture_intro.html": LECTURE_HTML,
                "week02/tutorial_forms.html": LECTURE_HTML,
                "assessments/quiz1.html": ASSESSMENT_HTML,
            }
        )

        result = svc.create_unit_from_package(zip_bytes, str(test_user.id), test_db)

        assert result.unit_code == "ICT100"
        assert result.unit_title == "Intro to ICT"
        assert result.ulo_count == 2
        assert result.gc_mapping_count == 2
        assert result.aol_mapping_count == 1
        assert result.sdg_mapping_count == 1
        assert result.material_count == 2
        assert result.assessment_count == 1
        assert result.weekly_topic_count == 2

        unit = test_db.query(Unit).filter(Unit.id == result.unit_id).first()
        assert unit is not None
        assert str(unit.pedagogy_type) == "flipped"
        assert unit.year == 2025
        assert str(unit.semester) == "semester_2"
        assert unit.credit_points == 12
        prov = unit.import_provenance
        assert prov is not None
        assert prov["meta_version"] == "1.0"
        assert prov["identifier_map"] == {"materials": {}, "assessments": {}}

        # Week topics get titles from the manifest, "Week N:" prefix stripped
        topics = (
            test_db.query(WeeklyTopic)
            .filter(WeeklyTopic.unit_id == result.unit_id)
            .order_by(WeeklyTopic.week_number)
            .all()
        )
        assert [(t.week_number, str(t.topic_title)) for t in topics] == [
            (1, "HTML Basics"),
            (2, "Advanced Topics"),
        ]

        # Materials: title from <h1>, type from filename prefix, body extracted
        mats = (
            test_db.query(WeeklyMaterial)
            .filter(WeeklyMaterial.unit_id == result.unit_id)
            .order_by(WeeklyMaterial.week_number)
            .all()
        )
        assert len(mats) == 2
        assert str(mats[0].title) == "HTML Lecture"
        assert str(mats[0].type) == "lecture"
        assert "Tags and structure." in str(mats[0].description)
        assert str(mats[1].type) == "tutorial"

        # Assessment reconstructed from the HTML property table
        assessment = (
            test_db.query(Assessment)
            .filter(Assessment.unit_id == result.unit_id)
            .first()
        )
        assert assessment is not None
        assert str(assessment.title) == "HTML Quiz"
        assert str(assessment.type) == "formative"
        assert str(assessment.category) == "quiz"
        assert float(assessment.weight) == 20.0
        assert assessment.due_week == 4
        assert str(assessment.duration) == "30 minutes"
        assert str(assessment.submission_type) == "online"
        assert bool(assessment.group_work) is False

        # ULOs and accreditation mappings
        ulos = (
            test_db.query(UnitLearningOutcome)
            .filter(UnitLearningOutcome.unit_id == result.unit_id)
            .order_by(UnitLearningOutcome.sequence_order)
            .all()
        )
        assert [str(u.outcome_code) for u in ulos] == ["ULO1", "ULO2"]
        gc_rows = (
            test_db.query(ULOGraduateCapabilityMapping)
            .filter(ULOGraduateCapabilityMapping.ulo_id == str(ulos[0].id))
            .all()
        )
        assert sorted(str(g.capability_code) for g in gc_rows) == ["GC1", "GC2"]
        assert (
            test_db.query(UnitAoLMapping)
            .filter(UnitAoLMapping.unit_id == result.unit_id)
            .count()
            == 1
        )
        assert (
            test_db.query(UnitSDGMapping)
            .filter(UnitSDGMapping.unit_id == result.unit_id)
            .count()
            == 1
        )

    def test_generic_create_with_category_subheaders(
        self, test_db: Session, test_user: User
    ) -> None:
        """Generic import maps category sub-headers onto material categories,
        classifies assessments, and falls back to the default unit code."""
        from app.models.assessment import Assessment
        from app.models.unit import Unit
        from app.models.weekly_material import WeeklyMaterial
        from app.models.weekly_topic import WeeklyTopic

        reading_html = (
            "<html><body><h1>Reading: Chapter 1</h1>"
            "<p>Chapter 1 content.</p></body></html>"
        )
        svc = PackageImportService()
        zip_bytes = _zip_bytes(
            {
                "imsmanifest.xml": CATEGORY_MANIFEST,
                "files/reading1.html": reading_html,
            }
        )

        result = svc.create_unit_from_package(zip_bytes, str(test_user.id), test_db)

        # No code in the manifest → fallback code
        assert result.unit_code == "IMPORT001"
        assert result.unit_title == "Plain Course"
        assert result.source_lms is None
        assert result.material_count == 3
        assert result.assessment_count == 1
        assert result.weekly_topic_count == 1

        unit = test_db.query(Unit).filter(Unit.id == result.unit_id).first()
        assert unit is not None
        assert unit.duration_weeks == 1  # one top-level item = one week
        prov = unit.import_provenance
        assert prov is not None
        assert "files/reading1.html" in prov["identifier_map"]["materials"]
        assert len(prov["organization"]) == 1

        topic = (
            test_db.query(WeeklyTopic)
            .filter(WeeklyTopic.unit_id == result.unit_id)
            .one()
        )
        assert str(topic.topic_title) == "Week 1: Foundations"

        mats = (
            test_db.query(WeeklyMaterial)
            .filter(WeeklyMaterial.unit_id == result.unit_id)
            .order_by(WeeklyMaterial.order_index)
            .all()
        )
        assert [(str(m.title), str(m.type), str(m.category)) for m in mats] == [
            ("Reading: Chapter 1", "reading", "pre_class"),
            ("Video Intro", "video", "pre_class"),
            ("Lecture Notes", "lecture", "in_class"),
        ]
        # HTML body extracted into the material description when present
        assert "Chapter 1 content." in str(mats[0].description)
        assert str(mats[1].description) == ""  # no file behind the href

        assessment = (
            test_db.query(Assessment).filter(Assessment.unit_id == result.unit_id).one()
        )
        assert str(assessment.title) == "Quiz 1"
        assert str(assessment.category) == "quiz"
        assert assessment.due_week == 1
