"""
Mode B import service — multi-file zip → existing unit with multi-format
grouping (Phase 3 of the structured-import plan).

A lecturer uploads a zip of materials into an existing unit. The service:

1. Lists supported files in the zip (skipping hidden/system paths and
   unsupported extensions, which surface as warnings).
2. Groups files by (directory, filename stem) via ``grouping.group_files``.
3. Picks a canonical file per group (PPTX > DOCX > HTML > MD > PDF) and
   parses it into an editable ``WeeklyMaterial`` content_json.
4. Writes the non-canonical originals into the material's git content
   directory under ``source_files/`` and records them in
   ``material_metadata["attached_source_files"]``.
5. Detects each material's week from the canonical filename + folder path
   via ``file_import_service.detect_week_number``.

The apply path is async, mirroring ``unified_import_service``: it creates
an ``ImportTask`` via the shared task store, kicks off a background
coroutine with ``asyncio.ensure_future`` (kept on ``self._bg_task`` so it
isn't garbage-collected), and returns a ``task_id`` the caller polls.

Analysis (preview) is pure read-only computation over the zip — no DB or
git writes.
"""

from __future__ import annotations

import asyncio
import logging
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from app.models.weekly_material import WeeklyMaterial
from app.services.file_import_service import FileImportService
from app.services.import_task_store import ImportTask, create_task
from app.services.material_parsers import autodetect, get_default_for_format
from app.services.material_parsers.grouping import FileGroup, group_files
from app.services.material_parsers.persistence import (
    persist_extracted_images,
    persist_source_files,
    rewrite_image_src,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit

logger = logging.getLogger(__name__)

# Extensions Mode B knows how to parse into content_json. Files with any
# other extension are skipped with a warning (per ADR-061 transparency).
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {"pptx", "docx", "html", "htm", "md", "pdf"}
)


def _is_hidden_or_system(path: str) -> bool:
    """True if any path component starts with '.' or '__' (e.g. __MACOSX)."""
    return any(part.startswith((".", "__")) for part in PurePosixPath(path).parts)


def _ext(path: str) -> str:
    return PurePosixPath(path).suffix.lower().lstrip(".")


def _resolve_parser_id(content: bytes, filename: str) -> str:
    """Resolve the parser id for a file: auto-detect → format default."""
    detected = autodetect(content, filename)
    if detected:
        return detected
    return get_default_for_format(_ext(filename)).name


@dataclass
class _GroupPlan:
    """Resolved plan for one group — what preview and apply both need."""

    group: FileGroup
    detected_week: int | None
    parser_id: str


@dataclass
class BatchAnalysis:
    """Read-only analysis of a batch zip (the preview payload, pre-schema)."""

    group_plans: list[_GroupPlan]
    """Multi-format groups (more than one member)."""

    standalone_plans: list[_GroupPlan]
    """Singleton groups (one member each)."""

    warnings: list[str]


class BatchImportService:
    """Mode B: multi-file zip → existing unit with multi-format grouping."""

    def __init__(self) -> None:
        self._file_svc = FileImportService()
        # Held so the background task isn't garbage-collected mid-run.
        self._bg_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # Analysis (read-only — used by both preview and apply)
    # ------------------------------------------------------------------

    def analyze(self, zip_bytes: bytes) -> BatchAnalysis:
        """Group and plan every supported file in the zip. No side effects.

        Raises:
            zipfile.BadZipFile: if the bytes are not a valid zip.
        """
        warnings: list[str] = []
        usable_paths: list[str] = []

        with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                path = info.filename
                if _is_hidden_or_system(path):
                    continue
                ext = _ext(path)
                if ext not in SUPPORTED_EXTENSIONS:
                    warnings.append(
                        f"Skipped unsupported file: {path} (.{ext or 'no extension'})"
                    )
                    continue
                usable_paths.append(path)

            groups = group_files(usable_paths)
            group_plans: list[_GroupPlan] = []
            standalone_plans: list[_GroupPlan] = []

            for grp in groups:
                detected_week = self._file_svc.detect_week_number(
                    PurePosixPath(grp.canonical).name, grp.directory
                )
                content = zf.read(grp.canonical)
                parser_id = _resolve_parser_id(
                    content, PurePosixPath(grp.canonical).name
                )
                plan = _GroupPlan(
                    group=grp,
                    detected_week=detected_week,
                    parser_id=parser_id,
                )
                if grp.is_singleton:
                    standalone_plans.append(plan)
                else:
                    group_plans.append(plan)

        return BatchAnalysis(
            group_plans=group_plans,
            standalone_plans=standalone_plans,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Apply (async, mirrors unified_import_service)
    # ------------------------------------------------------------------

    def apply(
        self,
        zip_bytes: bytes,
        *,
        unit: Unit,
        user_email: str,
        db: Session,
        overrides: dict[str, dict[str, object]] | None = None,
    ) -> str:
        """Kick off the import in the background; return the task id.

        ``overrides`` maps group name → {canonical_filename?, week_number?}.
        The route layer validates unit ownership before calling this.
        """
        task = create_task()
        task.unit_id = str(unit.id)

        self._bg_task = asyncio.ensure_future(
            self._run(
                task,
                zip_bytes,
                unit=unit,
                user_email=user_email,
                db=db,
                overrides=overrides or {},
            )
        )
        return task.task_id

    async def _run(
        self,
        task: ImportTask,
        zip_bytes: bytes,
        *,
        unit: Unit,
        user_email: str,
        db: Session,
        overrides: dict[str, dict[str, object]],
    ) -> None:
        """Background worker: create one material per group + standalone."""
        task.status = "processing"

        try:
            analysis = self.analyze(zip_bytes)
        except zipfile.BadZipFile as exc:
            task.status = "failed"
            task.errors.append(f"Invalid ZIP: {exc}")
            return

        for w in analysis.warnings:
            task.errors.append(w)

        all_plans = [*analysis.group_plans, *analysis.standalone_plans]
        task.total_files = len(all_plans)

        try:
            with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zf:
                for plan in all_plans:
                    await self._apply_plan(
                        task, plan, zf, unit, db, user_email, overrides
                    )
            db.commit()
            task.current_file = None
            task.status = "completed"
        except Exception as exc:
            logger.exception("Batch import failed")
            task.status = "failed"
            task.errors.append(str(exc))
            db.rollback()

    async def _apply_plan(
        self,
        task: ImportTask,
        plan: _GroupPlan,
        zf: zipfile.ZipFile,
        unit: Unit,
        db: Session,
        user_email: str,
        overrides: dict[str, dict[str, object]],
    ) -> None:
        """Parse + persist a single group/standalone into a WeeklyMaterial."""
        grp = plan.group
        override = overrides.get(grp.name, {})
        canonical = self._resolve_canonical_override(grp, override)
        week = self._resolve_week_override(plan, override)

        task.current_file = PurePosixPath(canonical).name

        try:
            from app.services.material_parsers import (  # noqa: PLC0415
                get_parser,
            )

            content = zf.read(canonical)
            parser = get_parser(
                _resolve_parser_id(content, PurePosixPath(canonical).name)
            )
            parsed = await parser.parse(content, PurePosixPath(canonical).name)
        except Exception as exc:
            task.errors.append(f"{PurePosixPath(canonical).name}: {exc}")
            task.processed_files += 1
            return

        for warning in parsed.warnings:
            task.errors.append(f"{PurePosixPath(canonical).name}: {warning}")

        material = WeeklyMaterial(
            unit_id=str(unit.id),
            week_number=week,
            title=parsed.title or PurePosixPath(canonical).stem,
            type="lecture",
            description=None,
            order_index=0,
            status="draft",
        )
        db.add(material)
        db.flush()  # populate material.id for git paths

        # Images
        try:
            rewrites = persist_extracted_images(
                images=parsed.images,
                unit_id=str(unit.id),
                material=material,
                user_email=user_email,
            )
        except Exception:
            logger.exception(
                "Failed to persist images for imported material %s", material.id
            )
            rewrites = {}
        material.content_json = rewrite_image_src(parsed.content_json, rewrites)

        # Source files (non-canonical members, in upload order)
        source_paths = [p for p in grp.members if p != canonical]
        if source_paths:
            files = [(PurePosixPath(p).name, zf.read(p)) for p in source_paths]
            try:
                records = persist_source_files(
                    files=files,
                    unit_id=str(unit.id),
                    material=material,
                    user_email=user_email,
                )
                material.material_metadata = {
                    **(material.material_metadata or {}),
                    "attached_source_files": records,
                }
            except Exception:
                logger.exception(
                    "Failed to persist source files for material %s", material.id
                )

        task.processed_files += 1

    @staticmethod
    def _resolve_canonical_override(grp: FileGroup, override: dict[str, object]) -> str:
        """Apply a canonical_filename override if it names a real member."""
        wanted = override.get("canonical_filename")
        if isinstance(wanted, str) and wanted:
            for member in grp.members:
                if PurePosixPath(member).name == wanted:
                    return member
        return grp.canonical

    @staticmethod
    def _resolve_week_override(plan: _GroupPlan, override: dict[str, object]) -> int:
        """Apply a week_number override; fall back to detected week, then 1."""
        raw = override.get("week_number")
        if isinstance(raw, (int, str, float)):
            try:
                wk = int(raw)
            except (ValueError, TypeError):
                wk = 0
            if 1 <= wk <= 52:
                return wk
        return plan.detected_week or 1


# Module-level singleton (mirrors unified_import_service). The route layer
# uses this instance so the background task reference on ``_bg_task``
# survives the request that started it.
batch_import_service = BatchImportService()


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "BatchAnalysis",
    "BatchImportService",
    "batch_import_service",
]
