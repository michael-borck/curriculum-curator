"""
IMS Common Cartridge v1.2 export service.

Exports a Unit as a valid .imscc ZIP archive containing:
- imsmanifest.xml (CC v1.2 manifest)
- HTML resource files for weekly materials and assessments
- Overview pages (learning outcomes, accreditation)
- curriculum_curator_meta.json (round-trip metadata)
"""

import json
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from io import BytesIO, StringIO

from sqlalchemy.orm import Session

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

# CC v1.2 namespaces
NS_CP = "http://www.imsglobal.org/xsd/imsccv1p2/imscp_v1p1"
NS_LOM = "http://ltsc.ieee.org/xsd/imsccv1p2/LOM/manifest"
NS_LOMIMSCC = "http://ltsc.ieee.org/xsd/imsccv1p2/LOM/resource"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
    h1, h2, h3 {{ color: #1a1a2e; }}
    code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
    pre {{ background: #f4f4f4; padding: 1rem; overflow-x: auto; border-radius: 6px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f0f0f0; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  {content}
</body>
</html>"""


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug[:60]


class IMSCCExportService:
    """Exports a Unit as an IMS Common Cartridge v1.2 package."""

    def export_unit(self, unit_id: str, db: Session) -> tuple[BytesIO, str]:
        """Export a unit as .imscc ZIP. Returns (BytesIO, filename)."""
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            msg = f"Unit {unit_id} not found"
            raise ValueError(msg)

        outline = db.query(UnitOutline).filter(UnitOutline.unit_id == unit_id).first()

        weekly_topics = (
            db.query(WeeklyTopic)
            .filter(WeeklyTopic.unit_id == unit_id)
            .order_by(WeeklyTopic.week_number)
            .all()
        )

        weekly_materials = (
            db.query(WeeklyMaterial)
            .filter(WeeklyMaterial.unit_id == unit_id)
            .order_by(WeeklyMaterial.week_number, WeeklyMaterial.order_index)
            .all()
        )

        assessments = (
            db.query(Assessment)
            .filter(Assessment.unit_id == unit_id)
            .order_by(Assessment.due_week)
            .all()
        )

        learning_outcomes = (
            db.query(UnitLearningOutcome)
            .filter(UnitLearningOutcome.unit_id == unit_id)
            .order_by(UnitLearningOutcome.sequence_order)
            .all()
        )

        aol_mappings = (
            db.query(UnitAoLMapping)
            .filter(UnitAoLMapping.unit_id == unit_id)
            .all()
        )

        sdg_mappings = (
            db.query(UnitSDGMapping)
            .filter(UnitSDGMapping.unit_id == unit_id)
            .all()
        )

        gc_mappings: list[ULOGraduateCapabilityMapping] = []
        for ulo in learning_outcomes:
            gc_maps = (
                db.query(ULOGraduateCapabilityMapping)
                .filter(ULOGraduateCapabilityMapping.ulo_id == ulo.id)
                .all()
            )
            gc_mappings.extend(gc_maps)

        # Group materials by week
        materials_by_week: dict[int, list[WeeklyMaterial]] = {}
        for mat in weekly_materials:
            week = int(mat.week_number)
            materials_by_week.setdefault(week, []).append(mat)

        # Build all resources: list of (identifier, href, title)
        resources: list[tuple[str, str, str]] = []
        file_contents: dict[str, str] = {}

        # Overview pages
        lo_html = self._build_learning_outcomes_html(learning_outcomes)
        resources.append(("overview_learning_outcomes", "overview/learning_outcomes.html", "Learning Outcomes"))
        file_contents["overview/learning_outcomes.html"] = lo_html

        accred_html = self._build_accreditation_html(
            aol_mappings, sdg_mappings, gc_mappings, learning_outcomes
        )
        resources.append(("overview_accreditation", "overview/accreditation.html", "Accreditation Mapping"))
        file_contents["overview/accreditation.html"] = accred_html

        # Weekly material pages
        for week_num, mats in sorted(materials_by_week.items()):
            week_dir = f"week{week_num:02d}"
            for mat in mats:
                slug = _slugify(mat.title)
                mat_type = str(mat.type)
                filename = f"{mat_type}_{slug}.html"
                href = f"{week_dir}/{filename}"
                identifier = f"mat_{mat.id}"

                content = str(mat.description or "")
                html = self._material_to_html(str(mat.title), content)

                resources.append((identifier, href, str(mat.title)))
                file_contents[href] = html

        # Assessment pages
        for i, assessment in enumerate(assessments, 1):
            href = f"assessments/assessment_{i}.html"
            identifier = f"assessment_{assessment.id}"
            html = self._assessment_to_html(assessment)
            resources.append((identifier, href, str(assessment.title)))
            file_contents[href] = html

        # Build manifest XML
        manifest_xml = self._build_manifest(unit, outline, weekly_topics, resources, materials_by_week)

        # Build metadata JSON
        meta_json = self._build_meta_json(
            unit, learning_outcomes, aol_mappings, sdg_mappings, gc_mappings
        )

        # Package into ZIP
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("imsmanifest.xml", manifest_xml)
            zf.writestr("curriculum_curator_meta.json", meta_json)
            for href, content in file_contents.items():
                zf.writestr(href, content)

        buf.seek(0)
        title_slug = _slugify(str(unit.title))
        filename = f"{unit.code}_{title_slug}.imscc"
        return buf, filename

    def _build_manifest(
        self,
        unit: Unit,
        outline: UnitOutline | None,
        weekly_topics: list[WeeklyTopic],
        resources: list[tuple[str, str, str]],
        materials_by_week: dict[int, list[WeeklyMaterial]],
    ) -> str:
        """Build imsmanifest.xml content."""
        # Register namespaces to avoid ns0: prefixes
        ET.register_namespace("", NS_CP)
        ET.register_namespace("lom", NS_LOM)
        ET.register_namespace("lomimscc", NS_LOMIMSCC)

        manifest = ET.Element(
            f"{{{NS_CP}}}manifest",
            identifier=f"curriculum_curator_{unit.id}",
        )

        # Metadata
        metadata = ET.SubElement(manifest, f"{{{NS_CP}}}metadata")
        schema = ET.SubElement(metadata, f"{{{NS_CP}}}schema")
        schema.text = "IMS Common Cartridge"
        schema_version = ET.SubElement(metadata, f"{{{NS_CP}}}schemaversion")
        schema_version.text = "1.2.0"

        # LOM metadata
        lom = ET.SubElement(metadata, f"{{{NS_LOM}}}lom")
        general = ET.SubElement(lom, f"{{{NS_LOM}}}general")
        title_elem = ET.SubElement(general, f"{{{NS_LOM}}}title")
        title_string = ET.SubElement(title_elem, f"{{{NS_LOM}}}string", language="en")
        title_string.text = f"{unit.title} ({unit.code})"

        if unit.description:
            desc_elem = ET.SubElement(general, f"{{{NS_LOM}}}description")
            desc_string = ET.SubElement(desc_elem, f"{{{NS_LOM}}}string", language="en")
            desc_string.text = str(unit.description)

        # Organizations
        organizations = ET.SubElement(manifest, f"{{{NS_CP}}}organizations")
        org = ET.SubElement(
            organizations,
            f"{{{NS_CP}}}organization",
            identifier="org_1",
            structure="rooted-hierarchy",
        )
        root_item = ET.SubElement(org, f"{{{NS_CP}}}item", identifier="root")

        # Overview folder
        overview_item = ET.SubElement(root_item, f"{{{NS_CP}}}item", identifier="overview")
        overview_title = ET.SubElement(overview_item, f"{{{NS_CP}}}title")
        overview_title.text = "Overview"
        for res_id, _href, res_title in resources:
            if res_id.startswith("overview_"):
                item = ET.SubElement(overview_item, f"{{{NS_CP}}}item", identifier=f"item_{res_id}", identifierref=res_id)
                t = ET.SubElement(item, f"{{{NS_CP}}}title")
                t.text = res_title

        # Weekly folders
        topic_map: dict[int, WeeklyTopic] = {int(t.week_number): t for t in weekly_topics}
        for week_num in sorted(materials_by_week.keys()):
            topic = topic_map.get(week_num)
            week_title = f"Week {week_num}"
            if topic and topic.topic_title:
                week_title = f"Week {week_num}: {topic.topic_title}"

            week_item = ET.SubElement(root_item, f"{{{NS_CP}}}item", identifier=f"week_{week_num:02d}")
            week_title_elem = ET.SubElement(week_item, f"{{{NS_CP}}}title")
            week_title_elem.text = week_title

            for res_id, _href, res_title in resources:
                if res_id.startswith("mat_") and _href.startswith(f"week{week_num:02d}/"):
                    item = ET.SubElement(week_item, f"{{{NS_CP}}}item", identifier=f"item_{res_id}", identifierref=res_id)
                    t = ET.SubElement(item, f"{{{NS_CP}}}title")
                    t.text = res_title

        # Assessments folder
        assessment_resources = [(r_id, r_href, r_title) for r_id, r_href, r_title in resources if r_id.startswith("assessment_")]
        if assessment_resources:
            assess_item = ET.SubElement(root_item, f"{{{NS_CP}}}item", identifier="assessments")
            assess_title = ET.SubElement(assess_item, f"{{{NS_CP}}}title")
            assess_title.text = "Assessments"
            for res_id, _href, res_title in assessment_resources:
                item = ET.SubElement(assess_item, f"{{{NS_CP}}}item", identifier=f"item_{res_id}", identifierref=res_id)
                t = ET.SubElement(item, f"{{{NS_CP}}}title")
                t.text = res_title

        # Resources section
        resources_elem = ET.SubElement(manifest, f"{{{NS_CP}}}resources")
        for res_id, href, _title in resources:
            res = ET.SubElement(
                resources_elem,
                f"{{{NS_CP}}}resource",
                identifier=res_id,
                type="webcontent",
                href=href,
            )
            ET.SubElement(res, f"{{{NS_CP}}}file", href=href)

        # Serialize
        tree = ET.ElementTree(manifest)
        xml_buf = StringIO()
        tree.write(xml_buf, encoding="unicode", xml_declaration=True)
        return xml_buf.getvalue()

    def _material_to_html(self, title: str, content: str) -> str:
        """Convert material content to standalone HTML page."""
        return HTML_TEMPLATE.format(title=_escape_html(title), content=content or "<p>No content available.</p>")

    def _assessment_to_html(self, assessment: Assessment) -> str:
        """Convert an assessment to a standalone HTML page."""
        parts: list[str] = []

        if assessment.description:
            parts.append(f"<p>{assessment.description}</p>")

        parts.append("<table>")
        parts.append("<tr><th>Property</th><th>Value</th></tr>")
        parts.append(f"<tr><td>Type</td><td>{assessment.type}</td></tr>")
        parts.append(f"<tr><td>Category</td><td>{assessment.category}</td></tr>")
        parts.append(f"<tr><td>Weight</td><td>{assessment.weight}%</td></tr>")

        if assessment.due_week:
            parts.append(f"<tr><td>Due Week</td><td>{assessment.due_week}</td></tr>")
        if assessment.duration:
            parts.append(f"<tr><td>Duration</td><td>{assessment.duration}</td></tr>")
        if assessment.submission_type:
            parts.append(f"<tr><td>Submission</td><td>{assessment.submission_type}</td></tr>")
        if assessment.group_work:
            parts.append("<tr><td>Group Work</td><td>Yes</td></tr>")

        parts.append("</table>")

        if assessment.specification:
            parts.append(f"<h2>Specification</h2>\n{assessment.specification}")

        content = "\n".join(parts)
        return HTML_TEMPLATE.format(title=_escape_html(str(assessment.title)), content=content)

    def _build_learning_outcomes_html(
        self, outcomes: list[UnitLearningOutcome]
    ) -> str:
        """Generate learning outcomes HTML page."""
        if not outcomes:
            return HTML_TEMPLATE.format(title="Learning Outcomes", content="<p>No learning outcomes defined.</p>")

        rows: list[str] = []
        rows.append("<table>")
        rows.append("<tr><th>Code</th><th>Description</th><th>Bloom's Level</th></tr>")
        for lo in outcomes:
            code = lo.outcome_code or ""
            rows.append(
                f"<tr><td>{_escape_html(code)}</td>"
                f"<td>{_escape_html(str(lo.outcome_text))}</td>"
                f"<td>{_escape_html(str(lo.bloom_level))}</td></tr>"
            )
        rows.append("</table>")
        return HTML_TEMPLATE.format(title="Learning Outcomes", content="\n".join(rows))

    def _build_accreditation_html(
        self,
        aol_mappings: list[UnitAoLMapping],
        sdg_mappings: list[UnitSDGMapping],
        gc_mappings: list[ULOGraduateCapabilityMapping],
        outcomes: list[UnitLearningOutcome],
    ) -> str:
        """Generate accreditation mapping HTML page."""
        parts: list[str] = []

        # AoL mappings
        if aol_mappings:
            parts.append("<h2>Assurance of Learning (AoL) Mappings</h2>")
            parts.append("<table>")
            parts.append("<tr><th>Competency</th><th>Level</th><th>Notes</th></tr>")
            parts.extend(
                f"<tr><td>{_escape_html(str(m.competency_code))}</td>"
                f"<td>{_escape_html(str(m.level))}</td>"
                f"<td>{_escape_html(str(m.notes or ''))}</td></tr>"
                for m in aol_mappings
            )
            parts.append("</table>")

        # Graduate Capability mappings
        if gc_mappings:
            outcome_map = {str(o.id): o for o in outcomes}
            parts.append("<h2>Graduate Capability Mappings</h2>")
            parts.append("<table>")
            parts.append("<tr><th>ULO</th><th>Capability</th></tr>")
            for gc in gc_mappings:
                ulo = outcome_map.get(str(gc.ulo_id))
                ulo_code = ulo.outcome_code if ulo and ulo.outcome_code else str(gc.ulo_id)
                parts.append(
                    f"<tr><td>{_escape_html(ulo_code)}</td>"
                    f"<td>{_escape_html(str(gc.capability_code))}</td></tr>"
                )
            parts.append("</table>")

        # SDG mappings
        if sdg_mappings:
            parts.append("<h2>UN Sustainable Development Goals</h2>")
            parts.append("<table>")
            parts.append("<tr><th>SDG</th><th>Notes</th></tr>")
            parts.extend(
                f"<tr><td>{_escape_html(str(s.sdg_code))}</td>"
                f"<td>{_escape_html(str(s.notes or ''))}</td></tr>"
                for s in sdg_mappings
            )
            parts.append("</table>")

        if not parts:
            parts.append("<p>No accreditation mappings defined.</p>")

        return HTML_TEMPLATE.format(title="Accreditation Mapping", content="\n".join(parts))

    def _build_meta_json(
        self,
        unit: Unit,
        outcomes: list[UnitLearningOutcome],
        aol_mappings: list[UnitAoLMapping],
        sdg_mappings: list[UnitSDGMapping],
        gc_mappings: list[ULOGraduateCapabilityMapping],
    ) -> str:
        """Build the curriculum_curator_meta.json for round-trip."""
        # Build GC lookup: ulo_id -> list of capability codes
        gc_by_ulo: dict[str, list[str]] = {}
        for gc in gc_mappings:
            gc_by_ulo.setdefault(str(gc.ulo_id), []).append(str(gc.capability_code))

        meta = {
            "version": "1.0",
            "exported_from": "curriculum-curator",
            "exported_at": datetime.now(UTC).isoformat(),
            "unit": {
                "id": str(unit.id),
                "code": str(unit.code),
                "title": str(unit.title),
                "pedagogy_type": str(unit.pedagogy_type),
                "difficulty_level": str(unit.difficulty_level),
                "year": int(unit.year),
                "semester": str(unit.semester),
                "duration_weeks": int(unit.duration_weeks),
                "credit_points": int(unit.credit_points),
            },
            "learning_outcomes": [
                {
                    "code": lo.outcome_code or "",
                    "description": str(lo.outcome_text),
                    "bloom_level": str(lo.bloom_level),
                    "graduate_capabilities": gc_by_ulo.get(str(lo.id), []),
                }
                for lo in outcomes
            ],
            "aol_mappings": [
                {
                    "competency_code": str(m.competency_code),
                    "level": str(m.level),
                }
                for m in aol_mappings
            ],
            "sdg_mappings": [
                {"sdg_code": str(s.sdg_code)}
                for s in sdg_mappings
            ],
        }
        return json.dumps(meta, indent=2)


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# Module-level singleton
imscc_export_service = IMSCCExportService()
