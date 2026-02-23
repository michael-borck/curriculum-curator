"""
Tests for IMSCC round-trip fidelity: export → import → re-export.

Validates: provenance storage, identifier preservation, category round-trip.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

import uuid

import pytest

from app.services.imscc_service import IMSCCExportService
from app.services.lms_terminology import TargetLMS
from app.services.package_import_service import PackageImportService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit
    from app.models.user import User

NS_CP = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"


class TestRoundTripProvenance:
    """Test that importing a CC package stores provenance on the unit."""

    def test_round_trip_import_stores_provenance(
        self, test_db: Session, populated_unit: Unit, test_user: User
    ) -> None:
        """Export a populated unit, import the ZIP, verify provenance is stored."""
        export_svc = IMSCCExportService()
        import_svc = PackageImportService()

        # Export
        buf, _ = export_svc.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.CANVAS
        )
        zip_bytes = buf.getvalue()

        # Import
        result = import_svc.create_unit_from_package(
            zip_bytes,
            str(test_user.id),
            test_db,
            unit_code_override="ROUND001",
        )
        assert result.material_count > 0

        # Check provenance on the imported unit
        from app.models.unit import Unit as UnitModel

        imported_unit = (
            test_db.query(UnitModel).filter(UnitModel.id == result.unit_id).first()
        )
        assert imported_unit is not None
        prov = imported_unit.import_provenance
        assert prov is not None
        assert prov["schema_version"] == "1.0"
        assert prov["source_lms"] == "canvas"
        assert prov["meta_version"] == "2.0"
        assert prov["original_unit_id"] == str(populated_unit.id)
        assert "identifier_map" in prov
        assert "materials" in prov["identifier_map"]
        assert "assessments" in prov["identifier_map"]
        # Should have entries for materials
        assert len(prov["identifier_map"]["materials"]) > 0

    def test_generic_import_stores_provenance(
        self, test_db: Session, test_user: User
    ) -> None:
        """Build a minimal generic CC ZIP, import, verify provenance."""
        import_svc = PackageImportService()

        # Build a minimal CC package (no meta.json)
        manifest_xml = """<?xml version='1.0' encoding='UTF-8'?>
<manifest xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
          identifier="test_generic">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
  </metadata>
  <organizations>
    <organization identifier="org_1" structure="rooted-hierarchy">
      <item identifier="root">
        <item identifier="week_01">
          <title>Week 1: Introduction</title>
          <item identifier="item_lecture_1" identifierref="lecture_1">
            <title>Intro Lecture</title>
          </item>
        </item>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="lecture_1" type="webcontent" href="week01/lecture_intro.html">
      <file href="week01/lecture_intro.html"/>
    </resource>
  </resources>
</manifest>"""

        html_content = """<!DOCTYPE html>
<html><head><title>Intro Lecture</title></head>
<body><h1>Intro Lecture</h1><p>Hello world.</p></body></html>"""

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("imsmanifest.xml", manifest_xml)
            zf.writestr("week01/lecture_intro.html", html_content)
        zip_bytes = buf.getvalue()

        result = import_svc.create_unit_from_package(
            zip_bytes,
            str(test_user.id),
            test_db,
            unit_code_override="GEN001",
            unit_title_override="Generic Test",
        )
        assert result.material_count >= 1

        from app.models.unit import Unit as UnitModel

        imported_unit = (
            test_db.query(UnitModel).filter(UnitModel.id == result.unit_id).first()
        )
        assert imported_unit is not None
        prov = imported_unit.import_provenance
        assert prov is not None
        assert prov["schema_version"] == "1.0"
        assert prov["source_lms"] is None  # no LMS detected
        assert prov["source_format"] == "imscc"
        assert "identifier_map" in prov
        assert "organization" in prov
        assert len(prov["organization"]) >= 1


class TestRoundTripV2MaterialCategories:
    """Test that v2 meta preserves material categories on round-trip."""

    def test_v2_round_trip_preserves_categories(
        self, test_db: Session, test_user: User
    ) -> None:
        """Export a unit with categorized materials, import, verify categories."""
        from app.models.assessment import Assessment
        from app.models.unit import Unit as UnitModel
        from app.models.unit_outline import UnitOutline
        from app.models.weekly_material import WeeklyMaterial
        from app.models.weekly_topic import WeeklyTopic

        import uuid

        # Create a unit with categorized materials
        unit = UnitModel(
            id=str(uuid.uuid4()),
            title="Category Test Unit",
            code="CAT001",
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
            title="Category Test",
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
            topic_title="Categorized Week",
            created_by_id=str(test_user.id),
        )
        test_db.add(topic)

        # Create materials with specific categories
        categories = ["pre_class", "in_class", "post_class"]
        for i, cat in enumerate(categories):
            mat = WeeklyMaterial(
                unit_id=str(unit.id),
                week_number=1,
                title=f"{cat.replace('_', ' ').title()} Material",
                type="lecture",
                category=cat,
                description=f"<p>Content for {cat}</p>",
                order_index=i,
            )
            test_db.add(mat)

        test_db.commit()

        # Export
        export_svc = IMSCCExportService()
        buf, _ = export_svc.export_unit(str(unit.id), test_db)

        # Verify meta.json has categories
        with zipfile.ZipFile(buf, "r") as zf:
            meta = json.loads(zf.read("curriculum_curator_meta.json"))
            for mat_meta in meta["materials"]:
                assert mat_meta["category"] in categories

        # Import
        buf.seek(0)
        import_svc = PackageImportService()
        result = import_svc.create_unit_from_package(
            buf.getvalue(),
            str(test_user.id),
            test_db,
            unit_code_override="CAT002",
        )

        # Verify imported materials have correct categories
        imported_mats = (
            test_db.query(WeeklyMaterial)
            .filter(WeeklyMaterial.unit_id == result.unit_id)
            .order_by(WeeklyMaterial.order_index)
            .all()
        )
        assert len(imported_mats) == 3
        imported_categories = [str(m.category) for m in imported_mats]
        assert imported_categories == categories


class TestProvenanceAwareExport:
    """Test that re-export reuses original CC identifiers when LMS matches."""

    def test_reexport_preserves_identifiers(
        self, test_db: Session, populated_unit: Unit, test_user: User
    ) -> None:
        """Import CC, re-export to same LMS, verify manifest identifiers match originals."""
        export_svc = IMSCCExportService()
        import_svc = PackageImportService()

        # First export to Canvas
        buf1, _ = export_svc.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.CANVAS
        )

        # Extract original material identifiers from manifest
        with zipfile.ZipFile(buf1, "r") as zf:
            root1 = ET.fromstring(zf.read("imsmanifest.xml"))
            original_mat_ids = {
                r.get("identifier")
                for r in root1.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("mat_")
            }
            original_assess_ids = {
                r.get("identifier")
                for r in root1.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("assessment_")
            }

        assert len(original_mat_ids) > 0
        assert len(original_assess_ids) > 0

        # Import the CC
        result = import_svc.create_unit_from_package(
            buf1.getvalue(),
            str(test_user.id),
            test_db,
            unit_code_override="REEX001",
        )

        # Re-export to same LMS (Canvas)
        buf2, _ = export_svc.export_unit(
            result.unit_id, test_db, target_lms=TargetLMS.CANVAS
        )

        # Extract re-exported identifiers
        with zipfile.ZipFile(buf2, "r") as zf:
            root2 = ET.fromstring(zf.read("imsmanifest.xml"))
            reexport_mat_ids = {
                r.get("identifier")
                for r in root2.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("mat_")
            }
            reexport_assess_ids = {
                r.get("identifier")
                for r in root2.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("assessment_")
            }

        # Original identifiers should be preserved
        assert original_mat_ids == reexport_mat_ids
        assert original_assess_ids == reexport_assess_ids

    def test_reexport_different_lms_uses_fresh_ids(
        self, test_db: Session, populated_unit: Unit, test_user: User
    ) -> None:
        """Import from Canvas, export as Moodle, verify new identifiers."""
        export_svc = IMSCCExportService()
        import_svc = PackageImportService()

        # Export to Canvas
        buf1, _ = export_svc.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.CANVAS
        )
        with zipfile.ZipFile(buf1, "r") as zf:
            root1 = ET.fromstring(zf.read("imsmanifest.xml"))
            original_mat_ids = {
                r.get("identifier")
                for r in root1.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("mat_")
            }

        # Import
        result = import_svc.create_unit_from_package(
            buf1.getvalue(),
            str(test_user.id),
            test_db,
            unit_code_override="DIFF001",
        )

        # Re-export to Moodle (different LMS)
        buf2, _ = export_svc.export_unit(
            result.unit_id, test_db, target_lms=TargetLMS.MOODLE
        )

        with zipfile.ZipFile(buf2, "r") as zf:
            root2 = ET.fromstring(zf.read("imsmanifest.xml"))
            reexport_mat_ids = {
                r.get("identifier")
                for r in root2.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("mat_")
            }

        # Should NOT match — different LMS means fresh identifiers
        assert original_mat_ids != reexport_mat_ids

    def test_reexport_with_new_material(
        self, test_db: Session, populated_unit: Unit, test_user: User
    ) -> None:
        """Add a material after import, verify it gets a fresh identifier."""
        from app.models.weekly_material import WeeklyMaterial

        export_svc = IMSCCExportService()
        import_svc = PackageImportService()

        # Export and import
        buf1, _ = export_svc.export_unit(
            str(populated_unit.id), test_db, target_lms=TargetLMS.CANVAS
        )
        result = import_svc.create_unit_from_package(
            buf1.getvalue(),
            str(test_user.id),
            test_db,
            unit_code_override="NEW001",
        )

        # Add a new material to the imported unit
        new_mat = WeeklyMaterial(
            id=str(uuid.uuid4()),
            unit_id=result.unit_id,
            week_number=1,
            title="Brand New Material",
            type="resource",
            description="<p>Fresh content</p>",
            order_index=99,
        )
        test_db.add(new_mat)
        test_db.commit()

        # Re-export
        buf2, _ = export_svc.export_unit(
            result.unit_id, test_db, target_lms=TargetLMS.CANVAS
        )

        with zipfile.ZipFile(buf2, "r") as zf:
            root2 = ET.fromstring(zf.read("imsmanifest.xml"))
            reexport_mat_ids = {
                r.get("identifier")
                for r in root2.findall(f".//{{{NS_CP}}}resource")
                if r.get("identifier", "").startswith("mat_")
            }

        # The new material should have a fresh identifier (mat_{uuid})
        assert any(str(new_mat.id) in mid for mid in reexport_mat_ids if mid)
