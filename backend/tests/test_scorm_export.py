"""
Tests for SCORM 1.2 export service using in-memory SQLite.

Validates: ZIP structure, SCORM manifest XML, scorm_api.js presence,
HTML script injection, metadata JSON, and edge cases.
"""

from __future__ import annotations

import json
import uuid
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pytest

from app.services.scorm_service import SCORM_API_JS, SCORMExportService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit

NS_CP = "http://www.imsproject.org/xsd/imscp_rootv1p1p2"
NS_ADL = "http://www.adlnet.org/xsd/adlcp_rootv1p2"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportBasics:
    """Test ZIP structure and filename."""

    def test_export_returns_valid_zip(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, filename = service.export_unit(str(populated_unit.id), test_db)
        assert "test1001" in filename.lower()
        assert filename.endswith("_scorm12.zip")
        assert zipfile.is_zipfile(buf)

    def test_zip_contains_required_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            assert "scorm_api.js" in names
            assert "curriculum_curator_meta.json" in names
            assert "overview/learning_outcomes.html" in names
            assert "overview/accreditation.html" in names

    def test_zip_contains_weekly_material_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert any("week01" in n and "lecture" in n for n in names)

    def test_zip_contains_assessment_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert any("assessments/" in n for n in names)


class TestScormApiJs:
    """Test the SCORM API JavaScript file."""

    def test_scorm_api_js_present(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            js_content = zf.read("scorm_api.js").decode("utf-8")
            assert js_content == SCORM_API_JS

    def test_scorm_api_js_has_lms_calls(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            js_content = zf.read("scorm_api.js").decode("utf-8")
            assert "LMSInitialize" in js_content
            assert "LMSSetValue" in js_content
            assert "cmi.core.lesson_status" in js_content


class TestManifestXML:
    """Test SCORM 1.2 imsmanifest.xml content and structure."""

    def _get_root(self, buf: BytesIO) -> ET.Element:
        with zipfile.ZipFile(buf, "r") as zf:
            return ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))

    def test_manifest_is_valid_xml(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        root = self._get_root(buf)
        assert root.tag == f"{{{NS_CP}}}manifest"

    def test_manifest_schema_is_adl_scorm(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        root = self._get_root(buf)
        schema = root.find(f".//{{{NS_CP}}}schema")
        assert schema is not None
        assert schema.text == "ADL SCORM"
        schema_ver = root.find(f".//{{{NS_CP}}}schemaversion")
        assert schema_ver is not None
        assert schema_ver.text == "1.2"

    def test_manifest_has_organization_hierarchy(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        root = self._get_root(buf)
        org = root.find(f".//{{{NS_CP}}}organization")
        assert org is not None

        titles = [t.text for t in root.iter(f"{{{NS_CP}}}title") if t.text]
        assert "Overview" in titles
        assert any("Week 1" in t for t in titles)
        assert "Assessments" in titles

    def test_manifest_resources_have_scormtype(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        root = self._get_root(buf)
        resources = root.findall(f".//{{{NS_CP}}}resource")
        assert len(resources) > 0
        for res in resources:
            scormtype = res.get(f"{{{NS_ADL}}}scormtype")
            assert scormtype == "sco"

    def test_manifest_resources_match_zip_files(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            root = ET.fromstring(zf.read("imsmanifest.xml").decode("utf-8"))
            names = set(zf.namelist())
            resources = root.findall(f".//{{{NS_CP}}}resource")
            for res in resources:
                href = res.get("href")
                assert href in names


class TestHTMLScriptInjection:
    """Test that all HTML files include the SCORM API script tag."""

    def test_overview_html_has_scorm_script(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        with zipfile.ZipFile(buf, "r") as zf:
            for name in ["overview/learning_outcomes.html", "overview/accreditation.html"]:
                html = zf.read(name).decode("utf-8")
                assert 'src="../scorm_api.js"' in html


class TestMetaJSON:
    """Test curriculum_curator_meta.json content."""

    def _load_meta(self, buf: BytesIO) -> dict[str, Any]:
        with zipfile.ZipFile(buf, "r") as zf:
            return json.loads(zf.read("curriculum_curator_meta.json").decode("utf-8"))

    def test_meta_json_valid_structure(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        assert meta["version"] == "1.0"
        assert meta["exported_from"] == "curriculum-curator"
        assert meta["export_format"] == "scorm_1.2"
        assert "exported_at" in meta
        assert "unit" in meta
        assert "learning_outcomes" in meta

    def test_meta_json_unit_fields(
        self, test_db: Session, populated_unit: Unit
    ) -> None:
        service = SCORMExportService()
        buf, _ = service.export_unit(str(populated_unit.id), test_db)
        meta = self._load_meta(buf)
        unit_meta = meta["unit"]
        assert unit_meta["code"] == "TEST1001"
        assert "Introduction to Testing" in unit_meta["title"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_export_empty_unit(self, test_db: Session, test_unit: Unit) -> None:
        """Unit with no materials/outcomes still produces valid SCORM ZIP."""
        service = SCORMExportService()
        buf, _ = service.export_unit(str(test_unit.id), test_db)
        assert zipfile.is_zipfile(buf)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            assert "scorm_api.js" in names

    def test_export_nonexistent_unit_raises(self, test_db: Session) -> None:
        service = SCORMExportService()
        with pytest.raises(ValueError, match=r"Unit .* not found"):
            service.export_unit(str(uuid.uuid4()), test_db)
