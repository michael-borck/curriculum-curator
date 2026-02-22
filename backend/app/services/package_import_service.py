"""
Import service for IMSCC and SCORM packages.

Supports two modes:
1. **Round-trip** — packages exported by Curriculum Curator that contain
   ``curriculum_curator_meta.json`` with full pedagogy, ULO, and accreditation
   metadata.
2. **Generic** — packages exported from Canvas, Moodle, Blackboard, or other
   LMS platforms that only contain ``imsmanifest.xml``.  Structure, materials,
   and assessments are inferred from the manifest with sensible defaults.
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
import zipfile
from collections.abc import Callable
from io import BytesIO
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

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
from app.schemas.package_import import ImportPreview, ImportResult

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Regex to extract week number from folder names like "week01/", "week12/"
_WEEK_RE = re.compile(r"^week(\d{2})/")
# Regex to extract material type prefix from filenames like "lecture_foo.html"
_MAT_TYPE_RE = re.compile(r"^([a-z_]+?)_")
# Regex to guess a unit code pattern like "ICT100", "COMP2010"
UNIT_CODE_RE = re.compile(r"\b([A-Z]{2,6}\d{3,5})\b")

VALID_MATERIAL_TYPES = {
    "lecture",
    "handout",
    "quiz",
    "case_study",
    "resource",
    "notes",
    "video",
    "reading",
    "activity",
    "discussion",
}

# Keywords that indicate an assessment item (case-insensitive match on title)
ASSESSMENT_KEYWORDS = {
    "quiz",
    "exam",
    "test",
    "assignment",
    "midterm",
    "final",
    "assessment",
}

# Keyword → material type mapping for classification
MATERIAL_TYPE_KEYWORDS: dict[str, str] = {
    "lecture": "lecture",
    "reading": "reading",
    "video": "video",
    "discussion": "discussion",
    "activity": "activity",
    "handout": "handout",
    "case study": "case_study",
    "notes": "notes",
}

# Keyword → assessment category mapping
ASSESSMENT_CATEGORY_MAP: dict[str, str] = {
    "quiz": "quiz",
    "exam": "exam",
    "midterm": "exam",
    "final": "exam",
    "assignment": "project",
    "project": "project",
    "discussion": "discussion",
    "presentation": "presentation",
    "lab": "lab",
    "portfolio": "portfolio",
}

# IMS namespace URIs to try when parsing manifests
_IMS_NAMESPACES = [
    "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1",
    "http://www.imsglobal.org/xsd/imsccv1p2/imscp_v1p2",
    "http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p3",
    "http://www.imsglobal.org/xsd/imscp_v1p1",
    "http://www.adlnet.org/xsd/adlcp_rootv1p2",
]

# Type alias for the namespace-aware tag builder function
_TagFn = Callable[[str], str]


class PackageImportError(Exception):
    """Raised when a package cannot be imported."""


# ---------------------------------------------------------------------------
# Generic manifest parsing helpers (module-level)
# ---------------------------------------------------------------------------


def has_meta(zf: zipfile.ZipFile) -> bool:
    """Check whether the ZIP contains our round-trip metadata file."""
    return "curriculum_curator_meta.json" in zf.namelist()


def detect_format_from_manifest(zf: zipfile.ZipFile) -> str:
    """Detect IMSCC vs SCORM from the manifest XML."""
    if "imsmanifest.xml" not in zf.namelist():
        return "imscc"
    manifest_text = zf.read("imsmanifest.xml").decode("utf-8")
    if "adlnet.org" in manifest_text or "ADL SCORM" in manifest_text:
        return "scorm_1.2"
    return "imscc"


def detect_source_lms(manifest_text: str) -> str | None:
    """Keyword scan to detect which LMS generated the package."""
    lower = manifest_text.lower()
    if "canvas" in lower or "instructure" in lower:
        return "canvas"
    if "moodle" in lower:
        return "moodle"
    if "blackboard" in lower:
        return "blackboard"
    if "brightspace" in lower or "d2l" in lower:
        return "brightspace"
    return None


def classify_item(title: str, resource_type: str | None = None) -> tuple[str, str]:
    """Classify a manifest item as assessment or material.

    Returns ``("assessment", category)`` or ``("material", mat_type)``.
    """
    title_lower = title.lower()
    # Check assessment keywords first
    for kw in ASSESSMENT_KEYWORDS:
        if kw in title_lower:
            category = ASSESSMENT_CATEGORY_MAP.get(kw, "other")
            return ("assessment", category)

    # If the resource type hints at an assessment
    if resource_type and any(
        kw in resource_type.lower() for kw in ("assessment", "quiz", "test")
    ):
        return ("assessment", "other")

    # Try material type keywords
    for kw, mat_type in MATERIAL_TYPE_KEYWORDS.items():
        if kw in title_lower:
            return ("material", mat_type)

    return ("material", "resource")


def _read_resource_content(zf: zipfile.ZipFile, href: str) -> str:
    """Read HTML content from a ZIP entry, with path-resolution fallback."""
    # Try exact path first
    if href in zf.namelist():
        return zf.read(href).decode("utf-8", errors="replace")

    # Try without leading slash or with common prefixes
    clean = href.lstrip("/")
    if clean in zf.namelist():
        return zf.read(clean).decode("utf-8", errors="replace")

    # Search for the filename anywhere in the ZIP
    basename = href.rsplit("/", 1)[-1]
    for name in zf.namelist():
        if name.endswith("/" + basename) or name == basename:
            return zf.read(name).decode("utf-8", errors="replace")

    return ""


# ---------------------------------------------------------------------------
# Manifest parser
# ---------------------------------------------------------------------------


class _ManifestData:
    """Structured result from parsing imsmanifest.xml."""

    __slots__ = (
        "description",
        "raw_text",
        "resource_map",
        "title",
        "top_items",
    )

    def __init__(self) -> None:
        self.title: str = ""
        self.description: str = ""
        self.top_items: list[tuple[str, list[tuple[str, str | None, str | None]]]] = []
        # identifier -> (href, type)
        self.resource_map: dict[str, tuple[str, str | None]] = {}
        self.raw_text: str = ""


def _resolve_ns(tree: ET.Element) -> str:
    """Find the IMS namespace used in the manifest, or empty string."""
    for candidate in _IMS_NAMESPACES:
        if tree.find(f"{{{candidate}}}organizations") is not None:
            return candidate
    return ""


def _el_title(el: ET.Element, tag_fn: _TagFn) -> str:
    """Extract the <title> text of a manifest element, or 'Untitled'."""
    title_el = el.find(tag_fn("title"))
    if title_el is not None and title_el.text:
        return title_el.text.strip()
    return "Untitled"


def _resolve_ref(
    el: ET.Element,
    resource_map: dict[str, tuple[str, str | None]],
) -> tuple[str | None, str | None]:
    """Resolve an element's identifierref to (href, type)."""
    ref_id = el.get("identifierref", "")
    if ref_id and ref_id in resource_map:
        return resource_map[ref_id]
    return (None, None)


def _walk_items(
    tree: ET.Element,
    tag_fn: _TagFn,
    resource_map: dict[str, tuple[str, str | None]],
) -> list[tuple[str, list[tuple[str, str | None, str | None]]]]:
    """Walk organisations → items and return structured top-level items."""
    items: list[tuple[str, list[tuple[str, str | None, str | None]]]] = []
    for org in tree.findall(f".//{tag_fn('organization')}"):
        for item in org.findall(tag_fn("item")):
            item_title = _el_title(item, tag_fn)
            children: list[tuple[str, str | None, str | None]] = []
            for child in item.findall(tag_fn("item")):
                child_title = _el_title(child, tag_fn)
                href, rtype = _resolve_ref(child, resource_map)
                children.append((child_title, href, rtype))

            if not children:
                href_val, rtype_val = _resolve_ref(item, resource_map)
                children.append((item_title, href_val, rtype_val))

            items.append((item_title, children))
    return items


def parse_manifest(zf: zipfile.ZipFile) -> _ManifestData:
    """Parse ``imsmanifest.xml`` using ElementTree.

    Tries multiple IMS namespace URIs, then falls back to no namespace.
    """
    data = _ManifestData()
    if "imsmanifest.xml" not in zf.namelist():
        return data

    raw = zf.read("imsmanifest.xml").decode("utf-8")
    data.raw_text = raw
    tree = ET.fromstring(raw)

    ns = _resolve_ns(tree)

    def tag_fn(local: str) -> str:
        return f"{{{ns}}}{local}" if ns else local

    # Package title from <metadata><schema>
    meta_el = tree.find(f".//{tag_fn('metadata')}")
    if meta_el is not None:
        schema_el = meta_el.find(tag_fn("schema"))
        if schema_el is not None and schema_el.text:
            data.title = schema_el.text.strip()

    # Build resource map: identifier -> (href, type)
    for res in tree.findall(f".//{tag_fn('resource')}"):
        ident = res.get("identifier", "")
        if ident:
            data.resource_map[ident] = (
                res.get("href", ""),
                res.get("type") or None,
            )

    # Walk items
    data.top_items = _walk_items(tree, tag_fn, data.resource_map)

    # Better title from <organization>
    org_el = tree.find(f".//{tag_fn('organization')}")
    if org_el is not None:
        data.title = _el_title(org_el, tag_fn)
        if data.title == "Untitled":
            data.title = ""

    # Fallback title
    if not data.title:
        title_el = tree.find(tag_fn("title"))
        if title_el is not None and title_el.text:
            data.title = title_el.text.strip()

    return data


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class PackageImportService:
    """Handles importing IMSCC/SCORM packages (round-trip and generic)."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_package(self, zip_bytes: bytes) -> ImportPreview:
        """Analyze a package ZIP and return a preview without persisting."""
        zf = self._open_zip(zip_bytes)
        if has_meta(zf):
            return self._analyze_round_trip(zf)
        return self._analyze_generic(zf)

    def create_unit_from_package(
        self,
        zip_bytes: bytes,
        current_user_id: str,
        db: Session,
        *,
        unit_code_override: str | None = None,
        unit_title_override: str | None = None,
        pedagogy_type: str | None = None,
        difficulty_level: str | None = None,
    ) -> ImportResult:
        """Import a package, creating all DB records."""
        zf = self._open_zip(zip_bytes)
        if has_meta(zf):
            return self._create_round_trip(
                zf,
                current_user_id,
                db,
                unit_code_override=unit_code_override,
                unit_title_override=unit_title_override,
            )
        return self._create_generic(
            zf,
            current_user_id,
            db,
            unit_code_override=unit_code_override,
            unit_title_override=unit_title_override,
            pedagogy_type=pedagogy_type or "inquiry-based",
            difficulty_level=difficulty_level or "intermediate",
        )

    # ------------------------------------------------------------------
    # Round-trip analysis / creation (existing logic)
    # ------------------------------------------------------------------

    def _analyze_round_trip(self, zf: zipfile.ZipFile) -> ImportPreview:
        meta = self._read_meta(zf)
        fmt = self._detect_format(zf, meta)
        unit_meta = meta["unit"]

        material_count = 0
        assessment_count = 0
        for name in zf.namelist():
            if _WEEK_RE.match(name) and name.endswith(".html"):
                material_count += 1
            elif name.startswith("assessments/") and name.endswith(".html"):
                assessment_count += 1

        los = meta.get("learning_outcomes", [])
        gc_count = sum(len(lo.get("graduate_capabilities", [])) for lo in los)

        return ImportPreview(
            format=fmt,
            is_round_trip=True,
            unit_code=unit_meta["code"],
            unit_title=unit_meta["title"],
            pedagogy_type=unit_meta.get("pedagogy_type", "inquiry-based"),
            difficulty_level=unit_meta.get("difficulty_level", "intermediate"),
            year=unit_meta.get("year", 2026),
            semester=unit_meta.get("semester", "semester_1"),
            duration_weeks=unit_meta.get("duration_weeks", 12),
            credit_points=unit_meta.get("credit_points", 6),
            ulo_count=len(los),
            material_count=material_count,
            assessment_count=assessment_count,
            aol_mapping_count=len(meta.get("aol_mappings", [])),
            sdg_mapping_count=len(meta.get("sdg_mappings", [])),
            gc_mapping_count=gc_count,
        )

    def _create_round_trip(
        self,
        zf: zipfile.ZipFile,
        current_user_id: str,
        db: Session,
        *,
        unit_code_override: str | None = None,
        unit_title_override: str | None = None,
    ) -> ImportResult:
        meta = self._read_meta(zf)
        unit_meta = meta["unit"]

        code = unit_code_override or unit_meta["code"]
        title = unit_title_override or unit_meta["title"]

        unit = Unit(
            title=title,
            code=code,
            description=f"Imported from package ({unit_meta.get('code', '')})",
            pedagogy_type=unit_meta.get("pedagogy_type", "inquiry-based"),
            difficulty_level=unit_meta.get("difficulty_level", "intermediate"),
            year=unit_meta.get("year", 2026),
            semester=unit_meta.get("semester", "semester_1"),
            duration_weeks=unit_meta.get("duration_weeks", 12),
            credit_points=unit_meta.get("credit_points", 6),
            status="draft",
            owner_id=current_user_id,
            created_by_id=current_user_id,
        )
        db.add(unit)
        db.flush()

        outline = UnitOutline(
            unit_id=str(unit.id),
            title=title,
            description="Imported from package",
            duration_weeks=unit_meta.get("duration_weeks", 12),
            credit_points=unit_meta.get("credit_points", 6),
            status="planning",
            created_by_id=current_user_id,
        )
        db.add(outline)
        db.flush()

        ulo_count = 0
        gc_count = 0
        for i, lo_data in enumerate(meta.get("learning_outcomes", [])):
            ulo = UnitLearningOutcome(
                unit_id=str(unit.id),
                unit_outline_id=str(outline.id),
                outcome_type="ulo",
                outcome_code=lo_data.get("code", f"ULO{i + 1}"),
                outcome_text=lo_data["description"],
                bloom_level=lo_data.get("bloom_level", "understand"),
                sequence_order=i,
                created_by_id=current_user_id,
            )
            db.add(ulo)
            db.flush()
            ulo_count += 1

            for gc_code in lo_data.get("graduate_capabilities", []):
                gc_mapping = ULOGraduateCapabilityMapping(
                    ulo_id=str(ulo.id),
                    capability_code=gc_code,
                    is_ai_suggested=False,
                )
                db.add(gc_mapping)
                gc_count += 1

        aol_count = 0
        for aol_data in meta.get("aol_mappings", []):
            aol = UnitAoLMapping(
                unit_id=str(unit.id),
                competency_code=aol_data["competency_code"],
                level=aol_data["level"],
                is_ai_suggested=False,
            )
            db.add(aol)
            aol_count += 1

        sdg_count = 0
        for sdg_data in meta.get("sdg_mappings", []):
            sdg = UnitSDGMapping(
                unit_id=str(unit.id),
                sdg_code=sdg_data["sdg_code"],
                is_ai_suggested=False,
            )
            db.add(sdg)
            sdg_count += 1

        topic_titles = self._extract_week_titles_from_manifest(zf)

        material_count = 0
        week_numbers_seen: set[int] = set()
        for name in sorted(zf.namelist()):
            week_match = _WEEK_RE.match(name)
            if not week_match or not name.endswith(".html"):
                continue

            week_num = int(week_match.group(1))
            week_numbers_seen.add(week_num)

            html_content = zf.read(name).decode("utf-8")
            title_text, body_content = self.extract_html_content(html_content)

            filename = name.split("/")[-1]
            mat_type = self._extract_material_type(filename)

            mat = WeeklyMaterial(
                unit_id=str(unit.id),
                week_number=week_num,
                title=title_text or filename.replace(".html", "").replace("_", " "),
                type=mat_type,
                description=body_content,
                order_index=material_count,
                status="draft",
            )
            db.add(mat)
            material_count += 1

        topic_count = 0
        for week_num in sorted(week_numbers_seen):
            topic_title = topic_titles.get(week_num, f"Week {week_num}")
            topic = WeeklyTopic(
                unit_outline_id=str(outline.id),
                unit_id=str(unit.id),
                week_number=week_num,
                topic_title=topic_title,
                created_by_id=current_user_id,
            )
            db.add(topic)
            topic_count += 1

        assessment_count = 0
        for name in sorted(zf.namelist()):
            if not name.startswith("assessments/") or not name.endswith(".html"):
                continue

            html_content = zf.read(name).decode("utf-8")
            assessment_data = self._parse_assessment_html(html_content)
            assessment = Assessment(
                unit_id=str(unit.id),
                title=assessment_data["title"],
                type=assessment_data.get("type", "summative"),
                category=assessment_data.get("category", "other"),
                weight=assessment_data.get("weight", 0.0),
                description=assessment_data.get("description"),
                specification=assessment_data.get("specification"),
                due_week=assessment_data.get("due_week"),
                duration=assessment_data.get("duration"),
                submission_type=assessment_data.get("submission_type"),
                group_work=assessment_data.get("group_work", False),
                status="draft",
            )
            db.add(assessment)
            assessment_count += 1

        db.commit()

        return ImportResult(
            unit_id=str(unit.id),
            unit_code=code,
            unit_title=title,
            ulo_count=ulo_count,
            material_count=material_count,
            assessment_count=assessment_count,
            aol_mapping_count=aol_count,
            sdg_mapping_count=sdg_count,
            gc_mapping_count=gc_count,
            weekly_topic_count=topic_count,
        )

    # ------------------------------------------------------------------
    # Generic (non-round-trip) analysis / creation
    # ------------------------------------------------------------------

    def _analyze_generic(self, zf: zipfile.ZipFile) -> ImportPreview:
        """Analyze a generic IMSCC/SCORM package (no meta.json)."""
        if "imsmanifest.xml" not in zf.namelist():
            raise PackageImportError(
                "Package does not contain imsmanifest.xml or "
                "curriculum_curator_meta.json. Cannot determine structure."
            )

        manifest = parse_manifest(zf)
        fmt = detect_format_from_manifest(zf)
        source_lms = detect_source_lms(manifest.raw_text)

        # Try to extract a unit code from the title or manifest text
        unit_code = ""
        code_match = UNIT_CODE_RE.search(manifest.title) or UNIT_CODE_RE.search(
            manifest.raw_text[:2000]
        )
        if code_match:
            unit_code = code_match.group(1)

        unit_title = manifest.title or "Imported Unit"

        # Classify items
        material_count = 0
        assessment_count = 0
        for _item_title, children in manifest.top_items:
            for child_title, _href, rtype in children:
                kind, _cat = classify_item(child_title, rtype)
                if kind == "assessment":
                    assessment_count += 1
                else:
                    material_count += 1

        return ImportPreview(
            format=fmt,
            is_round_trip=False,
            unit_code=unit_code,
            unit_title=unit_title,
            pedagogy_type="inquiry-based",
            difficulty_level="intermediate",
            year=2026,
            semester="semester_1",
            duration_weeks=len(manifest.top_items) or 12,
            credit_points=6,
            ulo_count=0,
            material_count=material_count,
            assessment_count=assessment_count,
            aol_mapping_count=0,
            sdg_mapping_count=0,
            gc_mapping_count=0,
            source_lms=source_lms,
        )

    def _create_generic(
        self,
        zf: zipfile.ZipFile,
        current_user_id: str,
        db: Session,
        *,
        unit_code_override: str | None = None,
        unit_title_override: str | None = None,
        pedagogy_type: str = "inquiry-based",
        difficulty_level: str = "intermediate",
    ) -> ImportResult:
        """Create a unit from a generic IMSCC/SCORM package."""
        if "imsmanifest.xml" not in zf.namelist():
            raise PackageImportError(
                "Package does not contain imsmanifest.xml or "
                "curriculum_curator_meta.json."
            )

        manifest = parse_manifest(zf)
        source_lms = detect_source_lms(manifest.raw_text)

        # Resolve title and code
        raw_title = unit_title_override or manifest.title or "Imported Unit"
        raw_code = unit_code_override or ""
        if not raw_code:
            code_match = UNIT_CODE_RE.search(manifest.title) or UNIT_CODE_RE.search(
                manifest.raw_text[:2000]
            )
            raw_code = code_match.group(1) if code_match else "IMPORT001"

        duration_weeks = len(manifest.top_items) or 12

        # 1. Create Unit
        unit = Unit(
            title=raw_title,
            code=raw_code,
            description=f"Imported from {source_lms or 'LMS'} package",
            pedagogy_type=pedagogy_type,
            difficulty_level=difficulty_level,
            year=2026,
            semester="semester_1",
            duration_weeks=duration_weeks,
            credit_points=6,
            status="draft",
            owner_id=current_user_id,
            created_by_id=current_user_id,
        )
        db.add(unit)
        db.flush()

        # 2. Create UnitOutline (needed for WeeklyTopic FK)
        outline = UnitOutline(
            unit_id=str(unit.id),
            title=raw_title,
            description=f"Imported from {source_lms or 'LMS'} package",
            duration_weeks=duration_weeks,
            credit_points=6,
            status="planning",
            created_by_id=current_user_id,
        )
        db.add(outline)
        db.flush()

        # 3. Walk manifest: each top-level item = week, children = materials/assessments
        topic_count = 0
        material_count = 0
        assessment_count = 0
        mat_order = 0

        for week_idx, (item_title, children) in enumerate(manifest.top_items, start=1):
            # Create weekly topic
            topic = WeeklyTopic(
                unit_outline_id=str(outline.id),
                unit_id=str(unit.id),
                week_number=week_idx,
                topic_title=item_title,
                created_by_id=current_user_id,
            )
            db.add(topic)
            topic_count += 1

            for child_title, href, rtype in children:
                kind, category = classify_item(child_title, rtype)

                # Read HTML content if available
                body_html = ""
                if href:
                    raw_html = _read_resource_content(zf, href)
                    if raw_html:
                        _title_text, body_html = self.extract_html_content(raw_html)

                if kind == "assessment":
                    assessment = Assessment(
                        unit_id=str(unit.id),
                        title=child_title,
                        type="summative",
                        category=category,
                        weight=0.0,
                        description=body_html or None,
                        due_week=week_idx,
                        status="draft",
                    )
                    db.add(assessment)
                    assessment_count += 1
                else:
                    mat = WeeklyMaterial(
                        unit_id=str(unit.id),
                        week_number=week_idx,
                        title=child_title,
                        type=category,  # material type from _classify_item
                        description=body_html,
                        order_index=mat_order,
                        status="draft",
                    )
                    db.add(mat)
                    material_count += 1
                    mat_order += 1

        db.commit()

        return ImportResult(
            unit_id=str(unit.id),
            unit_code=raw_code,
            unit_title=raw_title,
            ulo_count=0,
            material_count=material_count,
            assessment_count=assessment_count,
            aol_mapping_count=0,
            sdg_mapping_count=0,
            gc_mapping_count=0,
            weekly_topic_count=topic_count,
            source_lms=source_lms,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _open_zip(self, zip_bytes: bytes) -> zipfile.ZipFile:
        """Open and validate a ZIP file from raw bytes."""
        try:
            return zipfile.ZipFile(BytesIO(zip_bytes), "r")
        except zipfile.BadZipFile as e:
            raise PackageImportError(f"Invalid ZIP file: {e}") from e

    def _read_meta(self, zf: zipfile.ZipFile) -> dict:
        """Read and parse curriculum_curator_meta.json from the ZIP."""
        meta_name = "curriculum_curator_meta.json"
        if meta_name not in zf.namelist():
            raise PackageImportError(
                "Package does not contain curriculum_curator_meta.json."
            )
        try:
            raw = zf.read(meta_name).decode("utf-8")
            meta: dict = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise PackageImportError(f"Failed to parse meta.json: {e}") from e

        if "unit" not in meta:
            raise PackageImportError("meta.json is missing 'unit' data.")
        return meta

    def _detect_format(self, zf: zipfile.ZipFile, meta: dict) -> str:
        """Detect whether this is IMSCC or SCORM from meta/manifest."""
        if meta.get("export_format") == "scorm_1.2":
            return "scorm_1.2"
        return detect_format_from_manifest(zf)

    @staticmethod
    def extract_html_content(html: str) -> tuple[str, str]:
        """Extract title (from h1) and body content from an HTML page."""
        soup = BeautifulSoup(html, "html.parser")

        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""

        body = soup.find("body")
        if body is None:
            return title, ""

        if h1:
            h1.decompose()

        for script in body.find_all("script"):
            script.decompose()

        inner_html = body.decode_contents().strip()
        return title, inner_html

    def _extract_material_type(self, filename: str) -> str:
        """Extract material type from filename like 'lecture_intro.html'."""
        name = filename.removesuffix(".html")
        match = _MAT_TYPE_RE.match(name)
        if match:
            candidate = match.group(1)
            if candidate in VALID_MATERIAL_TYPES:
                return candidate
        return "resource"

    def _extract_week_titles_from_manifest(self, zf: zipfile.ZipFile) -> dict[int, str]:
        """Parse imsmanifest.xml to get week folder titles."""
        result: dict[int, str] = {}
        if "imsmanifest.xml" not in zf.namelist():
            return result

        manifest_text = zf.read("imsmanifest.xml").decode("utf-8")

        week_pattern = re.compile(
            r'identifier="week_(\d+)"[^>]*>.*?<[^>]*title[^>]*>([^<]+)<',
            re.DOTALL,
        )
        for m in week_pattern.finditer(manifest_text):
            week_num = int(m.group(1))
            raw_title = m.group(2).strip()
            topic_match = re.match(r"Week\s+\d+:\s*(.+)", raw_title)
            result[week_num] = topic_match.group(1) if topic_match else raw_title

        return result

    def _parse_assessment_html(self, html: str) -> dict:
        """Parse an assessment HTML page back into a data dict."""
        soup = BeautifulSoup(html, "html.parser")
        data: dict = {}

        h1 = soup.find("h1")
        data["title"] = h1.get_text(strip=True) if h1 else "Untitled Assessment"

        body = soup.find("body")
        if body is None:
            return data

        first_p = body.find("p")
        table = body.find("table")
        if first_p and table and first_p.find_next("table") == table:
            data["description"] = first_p.get_text(strip=True)

        if table:
            self._parse_assessment_table(table, data)

        spec_h2 = body.find("h2", string=re.compile(r"Specification", re.IGNORECASE))  # type: ignore[call-overload]
        if spec_h2:
            spec_parts: list[str] = []
            for sibling in spec_h2.next_siblings:
                if hasattr(sibling, "name") and sibling.name == "h2":
                    break
                text = str(sibling).strip()
                if text:
                    spec_parts.append(text)
            if spec_parts:
                data["specification"] = "\n".join(spec_parts)

        return data

    @staticmethod
    def _parse_assessment_table(table: object, data: dict) -> None:
        """Extract assessment properties from the HTML property table."""
        prop_map: dict[str, str] = {
            "Type": "type",
            "Category": "category",
            "Duration": "duration",
            "Submission": "submission_type",
        }
        for row in table.find_all("tr"):  # type: ignore[union-attr]
            cells = row.find_all(["td", "th"])
            if len(cells) != 2:
                continue
            prop = cells[0].get_text(strip=True)
            val = cells[1].get_text(strip=True)

            if prop in prop_map:
                data[prop_map[prop]] = val
            elif prop == "Weight":
                try:
                    data["weight"] = float(val.rstrip("%"))
                except ValueError:
                    data["weight"] = 0.0
            elif prop == "Due Week":
                with contextlib.suppress(ValueError):
                    data["due_week"] = int(val)
            elif prop == "Group Work":
                data["group_work"] = val.lower() == "yes"


# Module-level singleton
package_import_service = PackageImportService()
