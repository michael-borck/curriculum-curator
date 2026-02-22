"""
Unified import service — handles IMSCC, SCORM, and plain ZIP files.

Combines PackageImportService (manifest parsing, HTML extraction) with
FileImportService (PDF, DOCX, PPTX, MD, TXT processing) so that ALL
file types inside a package are processed, not just HTML.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import zipfile
from io import BytesIO
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from app.models.assessment import Assessment
from app.models.unit import Unit
from app.models.unit_outline import UnitOutline
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic
from app.schemas.package_import import (
    FilePreviewItem,
    SkippedFile,
    UnifiedImportPreview,
    UnifiedImportResult,
)
from app.services.file_import_service import FileImportService
from app.services.import_task_store import ImportTask, create_task
from app.services.package_import_service import (
    UNIT_CODE_RE,
    PackageImportError,
    PackageImportService,
    classify_item,
    detect_format_from_manifest,
    detect_source_lms,
    has_meta,
    parse_manifest,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Extensions we can extract text from
PROCESSABLE_EXTENSIONS = {".pdf", ".docx", ".pptx", ".md", ".txt", ".html", ".htm"}

# Max individual file size (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Files/dirs to always skip
_SKIP_PREFIXES = (".", "__", "__MACOSX")

_JUNK_BASENAMES = {"Thumbs.db", ".DS_Store"}


def _should_skip_entry(name: str) -> bool:
    """Return True for OS junk files and directories."""
    basename = PurePosixPath(name).name
    return (
        basename.startswith(_SKIP_PREFIXES)
        or name.endswith("/")
        or basename in _JUNK_BASENAMES
    )


def _title_from_filename(filename: str) -> str:
    """Derive a human-readable title from a filename."""
    stem = PurePosixPath(filename).stem
    title = re.sub(r"[_\-]+", " ", stem).strip()
    if title == title.lower():
        title = title.title()
    return title


class UnifiedImportService:
    """Coordinator that combines package + file import services."""

    def __init__(self) -> None:
        self._pkg_svc = PackageImportService()
        self._file_svc = FileImportService()

    # ------------------------------------------------------------------
    # Analyze
    # ------------------------------------------------------------------

    def analyze(self, zip_bytes: bytes) -> UnifiedImportPreview:
        """Inspect a ZIP and return a preview of every file inside it."""
        try:
            zf = zipfile.ZipFile(BytesIO(zip_bytes), "r")
        except zipfile.BadZipFile as e:
            raise PackageImportError(f"Invalid ZIP file: {e}") from e

        package_type = self._detect_package_type(zf)
        source_lms = self.detect_source_lms(zf)

        manifest_titles, manifest_types, unit_code, unit_title, duration_weeks = (
            self._extract_package_metadata(zf, package_type)
        )

        files, skipped = self._walk_files(zf, manifest_titles, manifest_types)

        material_count = sum(1 for f in files if f.detected_type == "material")
        assessment_count = sum(1 for f in files if f.detected_type == "assessment")

        return UnifiedImportPreview(
            package_type=package_type,
            source_lms=source_lms,
            is_round_trip=package_type == "round_trip",
            unit_code=unit_code,
            unit_title=unit_title,
            duration_weeks=duration_weeks,
            files=files,
            skipped_files=skipped,
            material_count=material_count,
            assessment_count=assessment_count,
            total_processable=len(files),
            total_skipped=len(skipped),
        )

    @staticmethod
    def _detect_package_type(zf: zipfile.ZipFile) -> str:
        if has_meta(zf):
            return "round_trip"
        if "imsmanifest.xml" in zf.namelist():
            fmt = detect_format_from_manifest(zf)
            return "scorm" if fmt == "scorm_1.2" else "imscc"
        return "plain_zip"

    @staticmethod
    def detect_source_lms(zf: zipfile.ZipFile) -> str | None:
        if "imsmanifest.xml" in zf.namelist():
            manifest_text = zf.read("imsmanifest.xml").decode("utf-8", errors="replace")
            return detect_source_lms(manifest_text)
        return None

    def _extract_package_metadata(
        self,
        zf: zipfile.ZipFile,
        package_type: str,
    ) -> tuple[dict[str, str], dict[str, str | None], str, str, int]:
        """Return (manifest_titles, manifest_types, unit_code, unit_title, duration_weeks)."""
        manifest_titles: dict[str, str] = {}
        manifest_types: dict[str, str | None] = {}
        unit_code = ""
        unit_title = ""
        duration_weeks = 12

        if package_type in ("imscc", "scorm"):
            manifest = parse_manifest(zf)
            unit_title = manifest.title or "Imported Unit"
            code_match = UNIT_CODE_RE.search(manifest.title) or UNIT_CODE_RE.search(
                manifest.raw_text[:2000]
            )
            if code_match:
                unit_code = code_match.group(1)
            duration_weeks = len(manifest.top_items) or 12

            for _item_title, children in manifest.top_items:
                for child_title, href, rtype in children:
                    if href:
                        manifest_titles[href] = child_title
                        manifest_types[href] = rtype
        elif package_type == "round_trip":
            meta_raw = zf.read("curriculum_curator_meta.json").decode("utf-8")
            meta = json.loads(meta_raw)
            unit_meta = meta.get("unit", {})
            unit_code = unit_meta.get("code", "")
            unit_title = unit_meta.get("title", "Imported Unit")
            duration_weeks = unit_meta.get("duration_weeks", 12)
        else:
            names = [n for n in zf.namelist() if not _should_skip_entry(n)]
            if names:
                top_folder = names[0].split("/")[0]
                code_match = UNIT_CODE_RE.search(top_folder)
                if code_match:
                    unit_code = code_match.group(1)
                unit_title = (
                    _title_from_filename(top_folder) if top_folder else "Imported Unit"
                )

        return manifest_titles, manifest_types, unit_code, unit_title, duration_weeks

    def _walk_files(
        self,
        zf: zipfile.ZipFile,
        manifest_titles: dict[str, str],
        manifest_types: dict[str, str | None],
    ) -> tuple[list[FilePreviewItem], list[SkippedFile]]:
        """Walk every entry in the ZIP, classifying each file."""
        files: list[FilePreviewItem] = []
        skipped: list[SkippedFile] = []

        for info in zf.infolist():
            name = info.filename
            if _should_skip_entry(name):
                continue

            basename = PurePosixPath(name).name
            ext = PurePosixPath(basename).suffix.lower()
            size = info.file_size
            folder_path = str(PurePosixPath(name).parent)

            if ext not in PROCESSABLE_EXTENSIONS:
                if ext:
                    skipped.append(
                        SkippedFile(
                            path=name, filename=basename, reason="unsupported_format"
                        )
                    )
                continue

            if size > MAX_FILE_SIZE:
                skipped.append(
                    SkippedFile(path=name, filename=basename, reason="too_large")
                )
                continue

            week_number = self._file_svc.detect_week_number(basename, folder_path)
            name_type = self._file_svc.detect_content_type_from_name(
                basename, folder_path
            )
            title = manifest_titles.get(name, "") or _title_from_filename(basename)

            if self._file_svc.is_unit_outline(basename):
                detected_type = "outline"
                material_type = None
            else:
                manifest_rtype = manifest_types.get(name)
                kind, category = classify_item(title, manifest_rtype)
                detected_type = kind
                material_type = category
                if kind == "material" and name_type != "general":
                    material_type = name_type

            files.append(
                FilePreviewItem(
                    path=name,
                    filename=basename,
                    extension=ext,
                    size_bytes=size,
                    detected_type=detected_type,
                    material_type=material_type,
                    week_number=week_number,
                    title=title,
                    processable=True,
                )
            )

        return files, skipped

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def apply(
        self,
        zip_bytes: bytes,
        *,
        user_id: str,
        db: Session,
        unit_code: str = "",
        unit_title: str = "",
        duration_weeks: int = 12,
        file_edits: list[dict[str, object]] | None = None,
    ) -> UnifiedImportResult:
        """Kick off import and return immediately with a task_id.

        ``file_edits`` is an optional list of per-file overrides from the
        preview UI (each dict has ``path``, and optional ``title``,
        ``week_number``, ``material_type``, ``detected_type``).
        """
        task = create_task()

        edits: dict[str, dict[str, object]] = {}
        if file_edits:
            for e in file_edits:
                path = str(e.get("path", ""))
                if path:
                    edits[path] = e

        # Keep a reference so the task isn't garbage-collected
        self._bg_task: asyncio.Task[None] = asyncio.ensure_future(
            self._run_import(
                task,
                zip_bytes,
                user_id=user_id,
                db=db,
                unit_code=unit_code,
                unit_title=unit_title,
                duration_weeks=duration_weeks,
                edits=edits,
            )
        )

        return UnifiedImportResult(
            unit_id="",
            unit_code=unit_code,
            unit_title=unit_title,
            task_id=task.task_id,
        )

    # ------------------------------------------------------------------
    # Background worker
    # ------------------------------------------------------------------

    async def _run_import(
        self,
        task: ImportTask,
        zip_bytes: bytes,
        *,
        user_id: str,
        db: Session,
        unit_code: str,
        unit_title: str,
        duration_weeks: int,
        edits: dict[str, dict[str, object]],
    ) -> None:
        """Background coroutine that processes every file in the ZIP."""
        task.status = "processing"

        try:
            zf = zipfile.ZipFile(BytesIO(zip_bytes), "r")
        except zipfile.BadZipFile as e:
            task.status = "failed"
            task.errors.append(f"Invalid ZIP: {e}")
            return

        try:
            preview = self.analyze(zip_bytes)
            task.total_files = preview.total_processable

            if preview.is_round_trip:
                self._import_round_trip(
                    task, zip_bytes, user_id, db, unit_code, unit_title
                )
                return

            unit, outline = self._create_unit_and_outline(
                db,
                user_id,
                code=unit_code or preview.unit_code or "IMPORT001",
                title=unit_title or preview.unit_title or "Imported Unit",
                weeks=duration_weeks or preview.duration_weeks or 12,
            )

            task.unit_id = str(unit.id)
            task.unit_code = unit.code
            task.unit_title = unit.title

            await self._process_files(task, zf, preview, outline, unit, db, edits)

            db.commit()
            task.current_file = None
            task.status = "completed"

        except Exception as exc:
            logger.exception("Unified import failed")
            task.status = "failed"
            task.errors.append(str(exc))
            db.rollback()

    def _import_round_trip(
        self,
        task: ImportTask,
        zip_bytes: bytes,
        user_id: str,
        db: Session,
        unit_code: str,
        unit_title: str,
    ) -> None:
        result = self._pkg_svc.create_unit_from_package(
            zip_bytes,
            user_id,
            db,
            unit_code_override=unit_code or None,
            unit_title_override=unit_title or None,
        )
        task.unit_id = result.unit_id
        task.unit_code = result.unit_code
        task.unit_title = result.unit_title
        task.processed_files = task.total_files
        task.status = "completed"

    @staticmethod
    def _create_unit_and_outline(
        db: Session,
        user_id: str,
        *,
        code: str,
        title: str,
        weeks: int,
    ) -> tuple[Unit, UnitOutline]:
        unit = Unit(
            title=title,
            code=code,
            description="Imported from package",
            pedagogy_type="inquiry-based",
            difficulty_level="intermediate",
            year=2026,
            semester="semester_1",
            duration_weeks=weeks,
            credit_points=6,
            status="draft",
            owner_id=user_id,
            created_by_id=user_id,
        )
        db.add(unit)
        db.flush()

        outline = UnitOutline(
            unit_id=str(unit.id),
            title=title,
            description="Imported from package",
            duration_weeks=weeks,
            credit_points=6,
            status="planning",
            created_by_id=user_id,
        )
        db.add(outline)
        db.flush()
        return unit, outline

    async def _process_files(
        self,
        task: ImportTask,
        zf: zipfile.ZipFile,
        preview: UnifiedImportPreview,
        outline: UnitOutline,
        unit: Unit,
        db: Session,
        edits: dict[str, dict[str, object]],
    ) -> None:
        """Process each file in the preview, creating DB records."""
        mat_order = 0
        week_numbers_seen: set[int] = set()

        for file_item in preview.files:
            task.current_file = file_item.filename

            edit = edits.get(file_item.path, {})
            file_title = str(edit.get("title", file_item.title))
            file_week: int | None = (
                int(edit["week_number"])  # type: ignore[arg-type]
                if "week_number" in edit and edit["week_number"] is not None
                else file_item.week_number
            )
            file_type = str(edit.get("detected_type", file_item.detected_type))
            mat_type = str(
                edit.get("material_type", file_item.material_type or "resource")
            )

            try:
                raw_bytes = zf.read(file_item.path)
            except KeyError:
                task.errors.append(f"File not found in ZIP: {file_item.path}")
                task.processed_files += 1
                continue

            content_html, file_title = await self._extract_content(
                raw_bytes, file_item, file_title, task
            )
            if content_html is None:
                task.processed_files += 1
                continue

            week = file_week or 1
            if file_type == "outline":
                outline.description = content_html[:10000]
            elif file_type == "assessment":
                db.add(
                    Assessment(
                        unit_id=str(unit.id),
                        title=file_title,
                        type="summative",
                        category=mat_type or "other",
                        weight=0.0,
                        description=content_html or None,
                        due_week=week,
                        status="draft",
                    )
                )
            else:
                db.add(
                    WeeklyMaterial(
                        unit_id=str(unit.id),
                        week_number=week,
                        title=file_title,
                        type=mat_type,
                        description=content_html,
                        order_index=mat_order,
                        status="draft",
                    )
                )
                mat_order += 1
                week_numbers_seen.add(week)

            task.processed_files += 1

        for week_num in sorted(week_numbers_seen):
            db.add(
                WeeklyTopic(
                    unit_outline_id=str(outline.id),
                    unit_id=str(unit.id),
                    week_number=week_num,
                    topic_title=f"Week {week_num}",
                    created_by_id=str(unit.created_by_id),
                )
            )

    async def _extract_content(
        self,
        raw_bytes: bytes,
        file_item: FilePreviewItem,
        file_title: str,
        task: ImportTask,
    ) -> tuple[str | None, str]:
        """Extract text/HTML from a single file. Returns (content, title) or (None, title) on error."""
        ext = file_item.extension.lower()
        try:
            if ext in (".html", ".htm"):
                html_text = raw_bytes.decode("utf-8", errors="replace")
                _title, body = PackageImportService.extract_html_content(html_text)
                if not file_title or file_title == _title_from_filename(
                    file_item.filename
                ):
                    file_title = _title or file_title
                return body, file_title

            if ext in (".pdf", ".docx", ".pptx", ".md", ".txt"):
                result = await self._file_svc.process_file(
                    raw_bytes, file_item.filename
                )
                if result.get("success"):
                    return result.get("content", ""), file_title
                task.errors.append(
                    f"Failed to process {file_item.filename}: {result.get('error', 'unknown')}"
                )
                return None, file_title
        except Exception as exc:
            task.errors.append(f"Error processing {file_item.filename}: {exc}")
            return None, file_title

        return "", file_title


# Module-level singleton
unified_import_service = UnifiedImportService()
