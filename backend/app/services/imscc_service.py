"""
IMS Common Cartridge v1.1 export service.

Exports a Unit as a valid .imscc ZIP archive containing:
- imsmanifest.xml (CC v1.1 manifest)
- HTML resource files for weekly materials and assessments
- Overview pages (learning outcomes, accreditation)
- curriculum_curator_meta.json (round-trip metadata)

CC v1.1 chosen for maximum LMS compatibility (Moodle, Canvas, Blackboard).
"""

import json
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
from app.services.h5p_service import h5p_builder
from app.services.lms_terminology import LMSTerminology, TargetLMS, get_terminology
from app.services.qti_service import qti_exporter
from app.services.unit_export_data import (
    HTML_TEMPLATE,
    UnitExportData,
    escape_html,
    gather_unit_export_data,
    render_material_html,
    slugify,
)

# CC v1.1 namespaces (v1.1 for broadest LMS compatibility — Moodle only supports up to 1.1)
NS_CP = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
NS_LOM = "http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest"
NS_LOMIMSCC = "http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource"


class IMSCCExportService:
    """Exports a Unit as an IMS Common Cartridge v1.1 package."""

    def export_unit(  # noqa: PLR0912
        self,
        unit_id: str,
        db: Session,
        *,
        target_lms: TargetLMS = TargetLMS.GENERIC,
    ) -> tuple[BytesIO, str]:
        """Export a unit as .imscc ZIP. Returns (BytesIO, filename)."""
        data = gather_unit_export_data(unit_id, db)
        terms = get_terminology(target_lms)

        # Build provenance reverse maps for identifier reuse on re-export
        # If provenance exists and target LMS matches source, reuse original CC identifiers
        mat_reverse: dict[str, str] = {}  # current_db_id -> original_cc_identifier
        assess_reverse: dict[str, str] = {}
        prov = data.unit.import_provenance
        if prov and prov.get("source_lms") == target_lms.value:
            id_map = prov.get("identifier_map", {})
            # Reverse: original_cc_key -> new_db_id  =>  new_db_id -> original_cc_key
            for orig_key, db_id in id_map.get("materials", {}).items():
                mat_reverse[str(db_id)] = orig_key
            for orig_key, db_id in id_map.get("assessments", {}).items():
                assess_reverse[str(db_id)] = orig_key

        # Build all resources: list of (identifier, href, title)
        resources: list[tuple[str, str, str]] = []
        file_contents: dict[str, str | bytes] = {}

        # Overview pages
        lo_html = self._build_learning_outcomes_html(data.learning_outcomes)
        resources.append(
            (
                "overview_learning_outcomes",
                "overview/learning_outcomes.html",
                "Learning Outcomes",
            )
        )
        file_contents["overview/learning_outcomes.html"] = lo_html

        accred_html = self._build_accreditation_html(
            data.aol_mappings,
            data.sdg_mappings,
            data.gc_mappings,
            data.learning_outcomes,
        )
        resources.append(
            (
                "overview_accreditation",
                "overview/accreditation.html",
                "Accreditation Mapping",
            )
        )
        file_contents["overview/accreditation.html"] = accred_html

        # Weekly material pages
        for week_num, mats in sorted(data.materials_by_week.items()):
            week_dir = f"week{week_num:02d}"
            for mat in mats:
                slug = slugify(mat.title)
                mat_type = str(mat.type)
                filename = f"{mat_type}_{slug}.html"
                href = f"{week_dir}/{filename}"
                # Reuse original CC identifier if available, else fresh
                identifier = mat_reverse.get(str(mat.id), f"mat_{mat.id}")

                content = render_material_html(mat)
                html = self._material_to_html(str(mat.title), content)

                resources.append((identifier, href, str(mat.title)))
                file_contents[href] = html

        # Assessment pages
        for i, assessment in enumerate(data.assessments, 1):
            href = f"assessments/assessment_{i}.html"
            # Reuse original CC identifier if available, else fresh
            identifier = assess_reverse.get(
                str(assessment.id), f"assessment_{assessment.id}"
            )
            html = self._assessment_to_html(assessment)
            resources.append((identifier, href, str(assessment.title)))
            file_contents[href] = html

        # QTI quiz resources (embedded QTI 1.2 for LMS import)
        qti_resources: list[tuple[str, str, str]] = []
        for content_id, questions in data.quiz_questions_by_content.items():
            if not questions:
                continue
            quiz_title = f"Quiz {content_id[:8]}"
            qti_ident = f"qti_{content_id[:8]}"
            qti_href = f"quizzes/{qti_ident}/assessment.xml"
            qti_xml = qti_exporter.export_qti12(questions, quiz_title)
            file_contents[qti_href] = qti_xml
            qti_resources.append((qti_ident, qti_href, quiz_title))

        # Quiz from editor content_json (quizQuestion TipTap nodes)
        # Route to H5P or QTI based on per-material export_format
        mat_by_id = {str(m.id): m for m in data.weekly_materials}
        h5p_resources: list[tuple[str, str, str]] = []
        for material_id, questions in data.quiz_questions_by_material.items():
            if not questions:
                continue
            mat_obj = mat_by_id.get(material_id)
            use_h5p = mat_obj and str(mat_obj.export_format) == "h5p_question_set"
            quiz_title = f"Quiz {material_id[:8]}"

            if use_h5p:
                h5p_ident = f"h5p_mat_{material_id[:8]}"
                h5p_href = f"h5p/{h5p_ident}.h5p"
                h5p_buf = h5p_builder.build(questions, quiz_title)
                file_contents[h5p_href] = h5p_buf.getvalue()  # type: ignore[assignment]
                h5p_resources.append((h5p_ident, h5p_href, quiz_title))
            else:
                qti_ident = f"qti_mat_{material_id[:8]}"
                qti_href = f"quizzes/{qti_ident}/assessment.xml"
                qti_xml = qti_exporter.export_qti12(questions, quiz_title)
                file_contents[qti_href] = qti_xml
                qti_resources.append((qti_ident, qti_href, quiz_title))

        # Build manifest XML
        manifest_xml = self._build_manifest(
            data.unit,
            data.outline,
            data.weekly_topics,
            resources,
            data.materials_by_week,
            qti_resources=qti_resources,
            h5p_resources=h5p_resources,
            terms=terms,
        )

        # Build metadata JSON
        meta_json = self._build_meta_json(data, resources, target_lms=target_lms)

        # Package into ZIP
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("imsmanifest.xml", manifest_xml)
            zf.writestr("curriculum_curator_meta.json", meta_json)
            for href, content in file_contents.items():
                zf.writestr(href, content)  # type: ignore[arg-type]

        buf.seek(0)
        title_slug = slugify(str(data.unit.title))
        filename = f"{data.unit.code}_{title_slug}.imscc"
        return buf, filename

    def _build_manifest(  # noqa: PLR0912
        self,
        unit: Unit,
        outline: UnitOutline | None,
        weekly_topics: list[WeeklyTopic],
        resources: list[tuple[str, str, str]],
        materials_by_week: dict[int, list[WeeklyMaterial]],
        *,
        qti_resources: list[tuple[str, str, str]] | None = None,
        h5p_resources: list[tuple[str, str, str]] | None = None,
        terms: LMSTerminology | None = None,
    ) -> str:
        """Build imsmanifest.xml content."""
        if terms is None:
            terms = get_terminology()

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
        schema_version.text = "1.1.0"

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
        overview_item = ET.SubElement(
            root_item, f"{{{NS_CP}}}item", identifier="overview"
        )
        overview_title = ET.SubElement(overview_item, f"{{{NS_CP}}}title")
        overview_title.text = terms.overview_label
        for res_id, _href, res_title in resources:
            if res_id.startswith("overview_"):
                item = ET.SubElement(
                    overview_item,
                    f"{{{NS_CP}}}item",
                    identifier=f"item_{res_id}",
                    identifierref=res_id,
                )
                t = ET.SubElement(item, f"{{{NS_CP}}}title")
                t.text = res_title

        # Weekly folders
        topic_map: dict[int, WeeklyTopic] = {
            int(t.week_number): t for t in weekly_topics
        }
        for week_num in sorted(materials_by_week.keys()):
            topic = topic_map.get(week_num)
            label = (
                terms.module_label
                if terms.lms != TargetLMS.GENERIC
                else unit.topic_label
            )
            week_title = f"{label} {week_num}"
            if topic and topic.topic_title:
                week_title = f"{label} {week_num}: {topic.topic_title}"

            week_item = ET.SubElement(
                root_item, f"{{{NS_CP}}}item", identifier=f"week_{week_num:02d}"
            )
            week_title_elem = ET.SubElement(week_item, f"{{{NS_CP}}}title")
            week_title_elem.text = week_title

            # Build resource lookup for this week
            week_prefix = f"week{week_num:02d}/"
            week_resources = [
                (res_id, _href, res_title)
                for res_id, _href, res_title in resources
                if res_id.startswith("mat_") and _href.startswith(week_prefix)
            ]

            # Check if materials have multiple categories
            week_mats = materials_by_week.get(week_num, [])
            unique_cats = {str(m.category) for m in week_mats}
            has_categories = unique_cats != {"general"} and len(unique_cats) > 0

            if has_categories:
                # Group by category with sub-headers
                cat_order = [
                    "pre_class",
                    "in_class",
                    "post_class",
                    "resources",
                    "general",
                ]
                cat_labels = {
                    "pre_class": "Pre-class",
                    "in_class": "In-class",
                    "post_class": "Post-class",
                    "resources": "Resources",
                    "general": "General",
                }
                # Build mat_id -> resource mapping
                mat_res_map: dict[str, tuple[str, str, str]] = {}
                for res_id, _href, res_title in week_resources:
                    mat_res_map[res_id] = (res_id, _href, res_title)

                for cat in cat_order:
                    cat_mats = [m for m in week_mats if str(m.category) == cat]
                    if not cat_mats:
                        continue
                    # Insert sub-header item
                    cat_item = ET.SubElement(
                        week_item,
                        f"{{{NS_CP}}}item",
                        identifier=f"cat_{week_num:02d}_{cat}",
                    )
                    cat_title = ET.SubElement(cat_item, f"{{{NS_CP}}}title")
                    cat_title.text = cat_labels.get(cat, cat.replace("_", " ").title())
                    for m in cat_mats:
                        res_key = f"mat_{m.id}"
                        if res_key in mat_res_map:
                            r_id, _r_href, r_title = mat_res_map[res_key]
                            item = ET.SubElement(
                                cat_item,
                                f"{{{NS_CP}}}item",
                                identifier=f"item_{r_id}",
                                identifierref=r_id,
                            )
                            t = ET.SubElement(item, f"{{{NS_CP}}}title")
                            t.text = r_title
                        else:
                            # Check provenance-aware identifiers (title fallback)
                            for r_id, _r_href, r_title in week_resources:
                                existing_ids = {
                                    el.get("identifier", "")
                                    for el in week_item.iter(f"{{{NS_CP}}}item")
                                }
                                if (
                                    _r_href.startswith(week_prefix)
                                    and r_title == str(m.title)
                                    and f"item_{r_id}" not in existing_ids
                                ):
                                    item = ET.SubElement(
                                        cat_item,
                                        f"{{{NS_CP}}}item",
                                        identifier=f"item_{r_id}",
                                        identifierref=r_id,
                                    )
                                    t = ET.SubElement(item, f"{{{NS_CP}}}title")
                                    t.text = r_title
                                    break
            else:
                # Flat structure (all general or single category)
                for res_id, _href, res_title in week_resources:
                    item = ET.SubElement(
                        week_item,
                        f"{{{NS_CP}}}item",
                        identifier=f"item_{res_id}",
                        identifierref=res_id,
                    )
                    t = ET.SubElement(item, f"{{{NS_CP}}}title")
                    t.text = res_title

        # Assessments folder
        assessment_resources = [
            (r_id, r_href, r_title)
            for r_id, r_href, r_title in resources
            if r_id.startswith("assessment_")
        ]
        if assessment_resources:
            assess_item = ET.SubElement(
                root_item, f"{{{NS_CP}}}item", identifier="assessments"
            )
            assess_title = ET.SubElement(assess_item, f"{{{NS_CP}}}title")
            assess_title.text = terms.assessment_label
            for res_id, _href, res_title in assessment_resources:
                item = ET.SubElement(
                    assess_item,
                    f"{{{NS_CP}}}item",
                    identifier=f"item_{res_id}",
                    identifierref=res_id,
                )
                t = ET.SubElement(item, f"{{{NS_CP}}}title")
                t.text = res_title

        # Quizzes folder (QTI + H5P resources)
        all_quiz_resources = list(qti_resources or []) + list(h5p_resources or [])
        if all_quiz_resources:
            quiz_item = ET.SubElement(
                root_item, f"{{{NS_CP}}}item", identifier="quizzes"
            )
            quiz_title_elem = ET.SubElement(quiz_item, f"{{{NS_CP}}}title")
            quiz_title_elem.text = terms.quiz_label
            for q_id, _q_href, q_title in all_quiz_resources:
                item = ET.SubElement(
                    quiz_item,
                    f"{{{NS_CP}}}item",
                    identifier=f"item_{q_id}",
                    identifierref=q_id,
                )
                t = ET.SubElement(item, f"{{{NS_CP}}}title")
                t.text = q_title

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

        # QTI resources (CC v1.1 assessment type)
        if qti_resources:
            for qti_id, qti_href, _qti_title in qti_resources:
                res = ET.SubElement(
                    resources_elem,
                    f"{{{NS_CP}}}resource",
                    identifier=qti_id,
                    type="imsqti_xmlv1p2/imscc_xmlv1p1/assessment",
                    href=qti_href,
                )
                ET.SubElement(res, f"{{{NS_CP}}}file", href=qti_href)

        # H5P resources (webcontent — LMSs with H5P plugins can import these)
        if h5p_resources:
            for h5p_id, h5p_href, _h5p_title in h5p_resources:
                res = ET.SubElement(
                    resources_elem,
                    f"{{{NS_CP}}}resource",
                    identifier=h5p_id,
                    type="webcontent",
                    href=h5p_href,
                )
                ET.SubElement(res, f"{{{NS_CP}}}file", href=h5p_href)

        # Serialize
        tree = ET.ElementTree(manifest)
        xml_buf = StringIO()
        tree.write(xml_buf, encoding="unicode", xml_declaration=True)
        return xml_buf.getvalue()

    def _material_to_html(self, title: str, content: str) -> str:
        """Convert material content to standalone HTML page."""
        return HTML_TEMPLATE.format(
            title=escape_html(title),
            content=content or "<p>No content available.</p>",
            extra_head="",
        )

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
            parts.append(
                f"<tr><td>Submission</td><td>{assessment.submission_type}</td></tr>"
            )
        if assessment.group_work:
            parts.append("<tr><td>Group Work</td><td>Yes</td></tr>")

        parts.append("</table>")

        if assessment.specification:
            parts.append(f"<h2>Specification</h2>\n{assessment.specification}")

        content = "\n".join(parts)
        return HTML_TEMPLATE.format(
            title=escape_html(str(assessment.title)), content=content, extra_head=""
        )

    def _build_learning_outcomes_html(self, outcomes: list[UnitLearningOutcome]) -> str:
        """Generate learning outcomes HTML page."""
        if not outcomes:
            return HTML_TEMPLATE.format(
                title="Learning Outcomes",
                content="<p>No learning outcomes defined.</p>",
                extra_head="",
            )

        rows: list[str] = []
        rows.append("<table>")
        rows.append("<tr><th>Code</th><th>Description</th><th>Bloom's Level</th></tr>")
        for lo in outcomes:
            code = lo.outcome_code or ""
            rows.append(
                f"<tr><td>{escape_html(code)}</td>"
                f"<td>{escape_html(str(lo.outcome_text))}</td>"
                f"<td>{escape_html(str(lo.bloom_level))}</td></tr>"
            )
        rows.append("</table>")
        return HTML_TEMPLATE.format(
            title="Learning Outcomes", content="\n".join(rows), extra_head=""
        )

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
                f"<tr><td>{escape_html(str(m.competency_code))}</td>"
                f"<td>{escape_html(str(m.level))}</td>"
                f"<td>{escape_html(str(m.notes or ''))}</td></tr>"
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
                ulo_code = (
                    ulo.outcome_code if ulo and ulo.outcome_code else str(gc.ulo_id)
                )
                parts.append(
                    f"<tr><td>{escape_html(ulo_code)}</td>"
                    f"<td>{escape_html(str(gc.capability_code))}</td></tr>"
                )
            parts.append("</table>")

        # SDG mappings
        if sdg_mappings:
            parts.append("<h2>UN Sustainable Development Goals</h2>")
            parts.append("<table>")
            parts.append("<tr><th>SDG</th><th>Notes</th></tr>")
            parts.extend(
                f"<tr><td>{escape_html(str(s.sdg_code))}</td>"
                f"<td>{escape_html(str(s.notes or ''))}</td></tr>"
                for s in sdg_mappings
            )
            parts.append("</table>")

        if not parts:
            parts.append("<p>No accreditation mappings defined.</p>")

        return HTML_TEMPLATE.format(
            title="Accreditation Mapping", content="\n".join(parts), extra_head=""
        )

    def _build_meta_json(
        self,
        data: UnitExportData,
        resources: list[tuple[str, str, str]],
        *,
        target_lms: TargetLMS = TargetLMS.GENERIC,
    ) -> str:
        """Build the curriculum_curator_meta.json for round-trip (v2)."""
        unit = data.unit
        # Build GC lookup: ulo_id -> list of capability codes
        gc_by_ulo: dict[str, list[str]] = {}
        for gc in data.gc_mappings:
            gc_by_ulo.setdefault(str(gc.ulo_id), []).append(str(gc.capability_code))

        # Build href lookup from resources: identifier -> href
        href_map = {res_id: href for res_id, href, _title in resources}

        meta: dict[str, object] = {
            "version": "1.0",
            "meta_version": "2.0",
            "exported_from": "curriculum-curator",
            "exported_at": datetime.now(UTC).isoformat(),
            "target_lms": target_lms.value,
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
                for lo in data.learning_outcomes
            ],
            "aol_mappings": [
                {
                    "competency_code": str(m.competency_code),
                    "level": str(m.level),
                }
                for m in data.aol_mappings
            ],
            "sdg_mappings": [{"sdg_code": str(s.sdg_code)} for s in data.sdg_mappings],
            # v2 fields: per-material, per-assessment, per-topic data
            "materials": [
                {
                    "id": str(mat.id),
                    "week_number": int(mat.week_number),
                    "title": str(mat.title),
                    "type": str(mat.type),
                    "category": str(mat.category),
                    "order_index": int(mat.order_index),
                    "href": href_map.get(f"mat_{mat.id}", ""),
                }
                for mat in data.weekly_materials
            ],
            "assessments": [
                {
                    "id": str(a.id),
                    "title": str(a.title),
                    "type": str(a.type),
                    "category": str(a.category),
                    "weight": float(a.weight) if a.weight else 0.0,
                    "due_week": int(a.due_week) if a.due_week else None,
                    "href": href_map.get(f"assessment_{a.id}", ""),
                }
                for a in data.assessments
            ],
            "weekly_topics": [
                {
                    "week_number": int(t.week_number),
                    "topic_title": str(t.topic_title) if t.topic_title else "",
                    "week_type": str(t.week_type)
                    if hasattr(t, "week_type") and t.week_type
                    else "standard",
                }
                for t in data.weekly_topics
            ],
        }
        return json.dumps(meta, indent=2)


# Module-level singleton
imscc_export_service = IMSCCExportService()
