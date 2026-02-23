"""
Tests for Canvas-specific import enhancements.

Validates: Canvas detection via module_meta.xml, $IMS-CC-FILEBASE$ token
resolution, and Canvas module structure parsing.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

from app.services.package_import_service import (
    PackageImportService,
    detect_source_lms,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.user import User


def _build_canvas_zip(
    *,
    include_module_meta: bool = True,
    include_filebase_tokens: bool = False,
) -> bytes:
    """Build a minimal Canvas-style CC ZIP in memory."""
    manifest_xml = """<?xml version='1.0' encoding='UTF-8'?>
<manifest xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
          identifier="lms_test_pkg">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
  </metadata>
  <organizations>
    <organization identifier="org_1" structure="rooted-hierarchy">
      <item identifier="root">
        <item identifier="module_1">
          <title>Module 1: Getting Started</title>
          <item identifier="item_page1" identifierref="page1">
            <title>Welcome Page</title>
          </item>
        </item>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="page1" type="webcontent" href="wiki_content/welcome.html">
      <file href="wiki_content/welcome.html"/>
    </resource>
  </resources>
</manifest>"""

    if include_filebase_tokens:
        html_content = """<!DOCTYPE html>
<html><head><title>Welcome</title></head>
<body>
<h1>Welcome</h1>
<p>See the image: <img src="$IMS-CC-FILEBASE$/images/logo.png"/></p>
<p>Also: <img src="%24IMS-CC-FILEBASE%24/images/banner.jpg"/></p>
</body></html>"""
    else:
        html_content = """<!DOCTYPE html>
<html><head><title>Welcome</title></head>
<body><h1>Welcome</h1><p>Hello from Canvas.</p></body></html>"""

    module_meta_xml = """<?xml version='1.0' encoding='UTF-8'?>
<modules xmlns="http://canvas.instructure.com/xsd/cccv1p0">
  <module identifier="module_1">
    <title>Module 1: Getting Started</title>
    <position>1</position>
    <items>
      <item identifier="item_page1">
        <title>Welcome Page</title>
        <content_type>WikiPage</content_type>
        <identifierref>page1</identifierref>
        <position>1</position>
      </item>
      <item identifier="item_subheader">
        <title>Resources</title>
        <content_type>ContextModuleSubHeader</content_type>
        <position>2</position>
      </item>
    </items>
  </module>
</modules>"""

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("imsmanifest.xml", manifest_xml)
        zf.writestr("wiki_content/welcome.html", html_content)
        if include_module_meta:
            zf.writestr("course_settings/module_meta.xml", module_meta_xml)
        if include_filebase_tokens:
            # Add the referenced image files so resolution can work
            zf.writestr("web_resources/images/logo.png", b"PNG_DATA")
            zf.writestr("web_resources/images/banner.jpg", b"JPG_DATA")
    return buf.getvalue()


class TestCanvasDetection:
    """Test Canvas LMS detection."""

    def test_canvas_detected_by_module_meta(self) -> None:
        """module_meta.xml should trigger Canvas detection even without keyword."""
        zip_bytes = _build_canvas_zip(include_module_meta=True)
        zf = zipfile.ZipFile(BytesIO(zip_bytes))
        # Manifest doesn't mention "canvas" explicitly
        manifest_text = zf.read("imsmanifest.xml").decode("utf-8")
        assert "canvas" not in manifest_text.lower()
        # But detection should still find Canvas via module_meta
        result = detect_source_lms(manifest_text, zf)
        assert result == "canvas"

    def test_canvas_not_detected_without_module_meta(self) -> None:
        """Without module_meta.xml and no keywords, no LMS detected."""
        zip_bytes = _build_canvas_zip(include_module_meta=False)
        zf = zipfile.ZipFile(BytesIO(zip_bytes))
        manifest_text = zf.read("imsmanifest.xml").decode("utf-8")
        result = detect_source_lms(manifest_text, zf)
        assert result is None


class TestFilebaseTokens:
    """Test $IMS-CC-FILEBASE$ token resolution."""

    def test_filebase_tokens_resolved(self) -> None:
        """Both literal and URL-encoded tokens should be resolved."""
        zip_bytes = _build_canvas_zip(
            include_module_meta=True, include_filebase_tokens=True
        )
        zf = zipfile.ZipFile(BytesIO(zip_bytes))
        html = zf.read("wiki_content/welcome.html").decode("utf-8")

        svc = PackageImportService()
        resolved = svc._resolve_filebase_tokens(html, zf)

        # Tokens should be replaced with actual paths
        assert "$IMS-CC-FILEBASE$" not in resolved
        assert "%24IMS-CC-FILEBASE%24" not in resolved
        # The resolved paths should point to web_resources/
        assert "web_resources/images/logo.png" in resolved
        assert "web_resources/images/banner.jpg" in resolved


class TestCanvasModuleStructure:
    """Test Canvas module_meta.xml parsing."""

    def test_canvas_module_structure_parsed(self) -> None:
        """module_meta.xml should be parsed into structured module data."""
        zip_bytes = _build_canvas_zip(include_module_meta=True)
        zf = zipfile.ZipFile(BytesIO(zip_bytes))
        svc = PackageImportService()
        modules = svc._parse_canvas_module_meta(zf)

        assert len(modules) == 1
        mod = modules[0]
        assert mod["title"] == "Module 1: Getting Started"
        items = mod["items"]
        assert len(items) == 2
        assert items[0]["title"] == "Welcome Page"
        assert items[0]["content_type"] == "WikiPage"
        assert items[1]["content_type"] == "ContextModuleSubHeader"

    def test_canvas_import_stores_modules_in_provenance(
        self, test_db: Session, test_user: User
    ) -> None:
        """Full Canvas import should store module structure in provenance."""
        zip_bytes = _build_canvas_zip(include_module_meta=True)
        svc = PackageImportService()
        result = svc.create_unit_from_package(
            zip_bytes,
            str(test_user.id),
            test_db,
            unit_code_override="CANV001",
            unit_title_override="Canvas Test",
        )

        from app.models.unit import Unit

        imported = test_db.query(Unit).filter(Unit.id == result.unit_id).first()
        assert imported is not None
        prov = imported.import_provenance
        assert prov is not None
        assert prov["source_lms"] == "canvas"
        assert "canvas_modules" in prov
        assert len(prov["canvas_modules"]) == 1
