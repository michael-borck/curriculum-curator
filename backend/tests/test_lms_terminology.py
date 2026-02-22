"""
Tests for LMS terminology mapping, LMS-aware classification, and
LMS-targeted exports (stories 9.9, 9.10).
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

import pytest

from app.services.imscc_service import IMSCCExportService
from app.services.lms_terminology import (
    LMS_TERMINOLOGY,
    TargetLMS,
    detect_lms_to_target,
    get_terminology,
)
from app.services.package_import_service import classify_item
from app.services.scorm_service import SCORMExportService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit

# CC v1.1 namespace (used to query IMSCC manifest XML)
NS_CC = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
# SCORM 1.2 / IMS CP v1.1.2 namespace
NS_SCORM = "http://www.imsproject.org/xsd/imscp_rootv1p1p2"


# ---------------------------------------------------------------------------
# get_terminology
# ---------------------------------------------------------------------------


class TestGetTerminology:
    def test_returns_generic_for_none(self) -> None:
        terms = get_terminology(None)
        assert terms.lms == TargetLMS.GENERIC
        assert terms.module_label == "Week"

    def test_returns_correct_labels_for_canvas(self) -> None:
        terms = get_terminology(TargetLMS.CANVAS)
        assert terms.module_label == "Module"
        assert terms.overview_label == "Pages"
        assert terms.assessment_label == "Assignments"
        assert terms.quiz_label == "Quizzes"

    def test_returns_correct_labels_for_moodle(self) -> None:
        terms = get_terminology(TargetLMS.MOODLE)
        assert terms.module_label == "Topic"
        assert terms.overview_label == "Resources"
        assert terms.assessment_label == "Activities"
        assert terms.quiz_label == "Quiz"

    def test_returns_correct_labels_for_blackboard(self) -> None:
        terms = get_terminology(TargetLMS.BLACKBOARD)
        assert terms.module_label == "Content Area"
        assert terms.assessment_label == "Assignments"
        assert terms.quiz_label == "Tests"

    def test_returns_correct_labels_for_brightspace(self) -> None:
        terms = get_terminology(TargetLMS.BRIGHTSPACE)
        assert terms.module_label == "Module"
        assert terms.overview_label == "Topics"
        assert terms.assessment_label == "Assignments"

    def test_all_lms_values_have_terminology(self) -> None:
        for lms in TargetLMS:
            assert lms in LMS_TERMINOLOGY

    def test_frozen_dataclass_is_immutable(self) -> None:
        terms = get_terminology(TargetLMS.CANVAS)
        with pytest.raises(AttributeError):
            terms.module_label = "Something Else"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# detect_lms_to_target
# ---------------------------------------------------------------------------


class TestDetectLmsToTarget:
    def test_none_returns_generic(self) -> None:
        assert detect_lms_to_target(None) == TargetLMS.GENERIC

    def test_known_strings(self) -> None:
        assert detect_lms_to_target("canvas") == TargetLMS.CANVAS
        assert detect_lms_to_target("moodle") == TargetLMS.MOODLE
        assert detect_lms_to_target("blackboard") == TargetLMS.BLACKBOARD
        assert detect_lms_to_target("brightspace") == TargetLMS.BRIGHTSPACE

    def test_case_insensitive(self) -> None:
        assert detect_lms_to_target("Canvas") == TargetLMS.CANVAS
        assert detect_lms_to_target("MOODLE") == TargetLMS.MOODLE

    def test_unknown_returns_generic(self) -> None:
        assert detect_lms_to_target("unknown_lms") == TargetLMS.GENERIC


# ---------------------------------------------------------------------------
# classify_item with source_lms
# ---------------------------------------------------------------------------


class TestClassifyItemLmsAware:
    def test_generic_assessment_keywords(self) -> None:
        kind, cat = classify_item("Final Exam")
        assert kind == "assessment"
        assert cat == "exam"

    def test_generic_material_fallback(self) -> None:
        kind, cat = classify_item("Intro to Python")
        assert kind == "material"
        assert cat == "resource"

    def test_canvas_source_classifies_assignments(self) -> None:
        # "assignments" is in Canvas terms but not in generic ASSESSMENT_KEYWORDS
        kind, cat = classify_item("Week 3 Assignments Overview", source_lms="canvas")
        assert kind == "assessment"

    def test_blackboard_source_classifies_tests(self) -> None:
        # "tests" is in Blackboard terms
        kind, cat = classify_item("Unit Tests Review", source_lms="blackboard")
        assert kind == "assessment"

    def test_source_lms_none_uses_generic(self) -> None:
        kind, cat = classify_item("Some Lecture", source_lms=None)
        assert kind == "material"
        assert cat == "lecture"

    def test_resource_type_hint_still_works(self) -> None:
        kind, _cat = classify_item("Unknown Title", "imsqti_xmlv1p2/assessment")
        assert kind == "assessment"


# ---------------------------------------------------------------------------
# IMSCC export with target_lms
# ---------------------------------------------------------------------------


class TestIMSCCExportWithTargetLms:
    def _get_titles(self, buf: BytesIO) -> list[str]:
        with zipfile.ZipFile(buf, "r") as zf:
            root = ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))
        return [t.text for t in root.iter(f"{{{NS_CC}}}title") if t.text]

    def _get_meta(self, buf: BytesIO) -> dict:
        with zipfile.ZipFile(buf, "r") as zf:
            return json.loads(zf.read("curriculum_curator_meta.json").decode("utf-8"))

    def test_default_uses_generic_labels(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        titles = self._get_titles(buf)
        assert "Overview" in titles
        assert "Assessments" in titles
        # Default uses unit.topic_label ("Week")
        assert any("Week 1" in t for t in titles)

    def test_canvas_labels(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.CANVAS
        )
        titles = self._get_titles(buf)
        assert "Pages" in titles
        assert "Assignments" in titles
        assert any("Module 1" in t for t in titles)
        assert "Overview" not in titles

    def test_moodle_labels(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.MOODLE
        )
        titles = self._get_titles(buf)
        assert "Resources" in titles
        assert "Activities" in titles
        assert any("Topic 1" in t for t in titles)

    def test_blackboard_labels(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.BLACKBOARD
        )
        titles = self._get_titles(buf)
        assert "Assignments" in titles
        assert any("Content Area 1" in t for t in titles)

    def test_meta_json_includes_target_lms(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.CANVAS
        )
        meta = self._get_meta(buf)
        assert meta["target_lms"] == "canvas"

    def test_meta_json_default_target_lms(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = IMSCCExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._get_meta(buf)
        assert meta["target_lms"] == "generic"


# ---------------------------------------------------------------------------
# SCORM export with target_lms
# ---------------------------------------------------------------------------


class TestSCORMExportWithTargetLms:
    def _get_titles(self, buf: BytesIO) -> list[str]:
        with zipfile.ZipFile(buf, "r") as zf:
            root = ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))
        return [t.text for t in root.iter(f"{{{NS_SCORM}}}title") if t.text]

    def _get_meta(self, buf: BytesIO) -> dict:
        with zipfile.ZipFile(buf, "r") as zf:
            return json.loads(zf.read("curriculum_curator_meta.json").decode("utf-8"))

    def test_default_uses_generic_labels(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        titles = self._get_titles(buf)
        assert "Overview" in titles
        assert "Assessments" in titles

    def test_canvas_labels(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.CANVAS
        )
        titles = self._get_titles(buf)
        assert "Pages" in titles
        assert "Assignments" in titles
        assert any("Module 1" in t for t in titles)

    def test_meta_json_includes_target_lms(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.MOODLE
        )
        meta = self._get_meta(buf)
        assert meta["target_lms"] == "moodle"
