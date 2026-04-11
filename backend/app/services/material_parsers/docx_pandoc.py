"""
Pandoc-backed DOCX parser — converts Word documents into TipTap content_json.

Phase 2 default for ``.docx`` files. Implementation strategy: shell out to
the Pandoc binary to convert DOCX → Markdown (with embedded media extracted
to a temp directory), then run the Markdown through ``md_structural``.

Pandoc's DOCX reader is significantly more robust at heading detection,
list structures, table parsing, and image extraction than anything we
could write on top of python-docx ourselves. Reusing the binary we
already ship for export keeps the import path small.

Pandoc binary resolution mirrors the existing pattern from
``export_service`` (env var → Electron resources → system PATH). If
Pandoc is not available the parser raises a clear runtime error and the
route layer surfaces it as a 500.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, ClassVar

from app.services.material_parsers.base import (
    ExtractedImage,
    MaterialParser,
    MaterialParseResult,
)
from app.services.material_parsers.md_structural import MdStructuralParser

logger = logging.getLogger(__name__)


# Pandoc subprocess timeout — DOCX conversion is fast but very large
# documents with embedded media can take a few seconds
_PANDOC_TIMEOUT_SECONDS = 60


class DocxPandocParser(MaterialParser):
    """Convert a DOCX document into TipTap content_json via Pandoc."""

    name: ClassVar[str] = "docx_pandoc"
    display_name: ClassVar[str] = "Word (Pandoc-backed)"
    description: ClassVar[str] = (
        "Default DOCX importer. Uses Pandoc to convert Word documents to "
        "Markdown with embedded media extracted, then runs the result "
        "through the Markdown structural parser. Preserves headings, "
        "lists, tables, images, and inline formatting."
    )
    supported_formats: ClassVar[list[str]] = ["docx"]
    requires_ai: ClassVar[bool] = False

    def __init__(self) -> None:
        # Reuse the markdown parser for the second stage
        self._md_parser = MdStructuralParser()

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> MaterialParseResult:
        _ = user_context

        # Lazy import so the export service singleton isn't constructed
        # at module load time (and to avoid a circular import via
        # export_service → content_json_renderer → ...)
        from app.services.export_service import ExportService  # noqa: PLC0415

        try:
            pandoc_path = ExportService.resolve_binary("pandoc", "PANDOC_PATH")
        except FileNotFoundError as exc:
            msg = (
                "DOCX import requires Pandoc, which is not available. "
                "Install pandoc or set PANDOC_PATH."
            )
            raise RuntimeError(msg) from exc

        warnings: list[str] = []

        with tempfile.TemporaryDirectory(prefix="cc_docx_import_") as temp_str:
            temp_dir = Path(temp_str)
            input_path = temp_dir / "input.docx"
            output_path = temp_dir / "output.md"
            media_dir = temp_dir / "media"

            input_path.write_bytes(file_content)

            # Use GFM as the output format so tables come out as pipe
            # tables — the simple/grid table formats Pandoc emits by
            # default aren't parsed by the standard markdown library and
            # would silently lose table structure on the second pass.
            cmd = [
                pandoc_path,
                str(input_path),
                "-f",
                "docx",
                "-t",
                "gfm",
                "-o",
                str(output_path),
                f"--extract-media={media_dir}",
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=_PANDOC_TIMEOUT_SECONDS,
                    cwd=temp_dir,
                )
            except subprocess.TimeoutExpired as exc:
                msg = (
                    f"Pandoc DOCX conversion timed out after "
                    f"{_PANDOC_TIMEOUT_SECONDS}s"
                )
                raise RuntimeError(msg) from exc

            if result.returncode != 0:
                msg = f"Pandoc DOCX conversion failed: {result.stderr.strip()}"
                raise RuntimeError(msg)

            markdown_text = output_path.read_text(encoding="utf-8")

            # Collect any extracted media files into ExtractedImage entries.
            # Pandoc emits image references in the markdown like
            # ![alt](media/image1.png), and the persistence layer will
            # rewrite the src after the material is created.
            extracted_images: dict[str, ExtractedImage] = {}
            if media_dir.exists():
                for media_file in sorted(media_dir.rglob("*")):
                    if not media_file.is_file():
                        continue
                    rel = media_file.relative_to(temp_dir)
                    rel_posix = rel.as_posix()
                    safe_name = self._safe_image_name(media_file.name)
                    extracted_images[rel_posix] = ExtractedImage(
                        filename=safe_name,
                        data=media_file.read_bytes(),
                        mime_type=self._guess_mime(media_file.suffix),
                    )

        # Run the markdown through the md parser
        md_result = await self._md_parser.parse(
            markdown_text.encode("utf-8"), filename
        )

        # Rewrite the image src in content_json from Pandoc's relative
        # media paths to the placeholder filenames the persistence layer
        # expects. Pandoc's references look like "media/image1.png" or
        # "./media/image1.png" — match by suffix.
        content_json, src_rewrites_used = self._rewrite_pandoc_image_src(
            md_result.content_json, extracted_images
        )

        # Drop any extracted images that weren't actually referenced —
        # avoids persisting orphan files
        used_keys = {k for k, used in src_rewrites_used.items() if used}
        final_images = [
            img for k, img in extracted_images.items() if k in used_keys
        ]

        if extracted_images and len(final_images) < len(extracted_images):
            warnings.append(
                f"{len(extracted_images) - len(final_images)} extracted "
                "image(s) not referenced in document and skipped"
            )

        # Combine warnings: parser warnings + any from the md/html stages
        combined_warnings = warnings + md_result.warnings

        return MaterialParseResult(
            title=md_result.title,
            content_json=content_json,
            images=final_images,
            warnings=combined_warnings,
            parser_used=self.name,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_image_name(filename: str) -> str:
        """Strip directory parts and return a flat filename suitable for
        the persistence layer's collision-handling logic."""
        return Path(filename).name

    @staticmethod
    def _guess_mime(suffix: str) -> str | None:
        ext = suffix.lower().lstrip(".")
        return {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "webp": "image/webp",
            "bmp": "image/bmp",
        }.get(ext)

    def _rewrite_pandoc_image_src(
        self,
        content_json: dict[str, Any],
        extracted: dict[str, ExtractedImage],
    ) -> tuple[dict[str, Any], dict[str, bool]]:
        """Walk content_json and rewrite image src from Pandoc's media
        paths to the placeholder filenames the persistence layer expects.

        Returns the rewritten content_json and a {pandoc_path: was_used}
        map so the caller can drop unused extracted images.
        """
        used: dict[str, bool] = dict.fromkeys(extracted, False)

        # Build a lookup by basename so paths with or without ./ prefixes
        # all match. Different Pandoc versions emit slightly different
        # path conventions.
        by_basename: dict[str, str] = {}
        for path in extracted:
            basename = Path(path).name
            by_basename[basename] = path

        def _walk(node: dict[str, Any]) -> dict[str, Any]:
            new_node: dict[str, Any] = dict(node)
            if node.get("type") == "image":
                attrs = dict(node.get("attrs", {}))
                src = attrs.get("src", "")
                if src:
                    basename = Path(src).name
                    if basename in by_basename:
                        original_key = by_basename[basename]
                        attrs["src"] = extracted[original_key].filename
                        used[original_key] = True
                        new_node["attrs"] = attrs
            if "content" in node and isinstance(node["content"], list):
                new_node["content"] = [_walk(c) for c in node["content"]]
            return new_node

        return _walk(content_json), used

    @staticmethod
    def is_available() -> bool:
        """Cheap check used by tests to skip when Pandoc isn't installed."""
        return shutil.which("pandoc") is not None
