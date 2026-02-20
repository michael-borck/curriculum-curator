"""
Document export service using Pandoc + Typst.

Converts Markdown content to HTML, PDF, DOCX, and PPTX formats.
PDF rendering uses the Pandoc → Typst pipeline (no LaTeX required).
All other formats use Pandoc directly.

See ADR-0033 for the decision to replace Quarto with Pandoc + Typst.
"""

import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.unit import Unit

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""

    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"


# Map formats to file extensions
FORMAT_EXTENSIONS: dict[ExportFormat, str] = {
    ExportFormat.HTML: ".html",
    ExportFormat.PDF: ".pdf",
    ExportFormat.DOCX: ".docx",
    ExportFormat.PPTX: ".pptx",
}

# Map formats to MIME types
FORMAT_MEDIA_TYPES: dict[ExportFormat, str] = {
    ExportFormat.HTML: "text/html",
    ExportFormat.PDF: "application/pdf",
    ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ExportFormat.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


class ExportService:
    """
    Export service using Pandoc for format conversion and Typst for PDF rendering.

    Binary resolution order:
    1. Environment variable (PANDOC_PATH / TYPST_PATH)
    2. RESOURCES_PATH/<name>/<binary> (Electron extraResources)
    3. System PATH (shutil.which)
    """

    def __init__(self) -> None:
        self._pandoc_path: str | None = None
        self._typst_path: str | None = None
        self.output_dir = Path(tempfile.gettempdir()) / "curriculum_curator_exports"
        self.output_dir.mkdir(exist_ok=True)

    @property
    def pandoc_path(self) -> str:
        if self._pandoc_path is None:
            self._pandoc_path = self._resolve_binary("pandoc", "PANDOC_PATH")
        return self._pandoc_path

    @property
    def typst_path(self) -> str:
        if self._typst_path is None:
            self._typst_path = self._resolve_binary("typst", "TYPST_PATH")
        return self._typst_path

    @staticmethod
    def _resolve_binary(name: str, env_var: str) -> str:
        """Resolve binary path from env var, Electron resources, or system PATH."""
        # 1. Explicit env var
        env_path = os.getenv(env_var)
        if env_path and Path(env_path).is_file():
            return env_path

        # 2. Electron extraResources path
        resources_path = os.getenv("RESOURCES_PATH")
        if resources_path:
            electron_path = Path(resources_path) / name / name
            if electron_path.is_file():
                return str(electron_path)

        # 3. System PATH
        system_path = shutil.which(name)
        if system_path:
            return system_path

        msg = (
            f"{name} binary not found. Set {env_var} environment variable, "
            f"install {name}, or ensure it is on the system PATH."
        )
        raise FileNotFoundError(msg)

    def check_availability(self) -> dict[str, Any]:
        """Check whether Pandoc and Typst are available."""
        result: dict[str, Any] = {"pandoc": False, "typst": False}

        try:
            pandoc = self.pandoc_path
            version = subprocess.run(
                [pandoc, "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if version.returncode == 0:
                first_line = version.stdout.split("\n")[0]
                result["pandoc"] = True
                result["pandoc_version"] = first_line
        except FileNotFoundError:
            pass

        try:
            typst = self.typst_path
            version = subprocess.run(
                [typst, "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if version.returncode == 0:
                result["typst"] = True
                result["typst_version"] = version.stdout.strip()
        except FileNotFoundError:
            pass

        result["pdf_available"] = result["pandoc"] and result["typst"]
        result["html_available"] = result["pandoc"]
        result["docx_available"] = result["pandoc"]
        result["pptx_available"] = result["pandoc"]

        return result

    async def export_content(
        self,
        content_id: str,
        db: Session,
        fmt: ExportFormat,
        title: str | None = None,
        author: str | None = None,
    ) -> tuple[BytesIO, str, str]:
        """
        Export a single content item to the specified format.

        Args:
            content_id: The content ID to export.
            db: Database session.
            fmt: Target export format.
            title: Optional title override (uses content.title if not provided).
            author: Optional author name for the document metadata.

        Returns:
            Tuple of (BytesIO buffer, filename, media_type).

        Raises:
            ValueError: If the content is not found.
            FileNotFoundError: If required binaries are not available.
            RuntimeError: If the conversion fails.
        """
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            msg = f"Content {content_id} not found"
            raise ValueError(msg)

        doc_title = title or content.title or "Untitled"
        markdown = content.content_markdown or content.content_html or ""

        buf = self._convert(
            markdown=markdown,
            fmt=fmt,
            title=doc_title,
            author=author,
        )

        slug = self._slugify(doc_title)
        ext = FORMAT_EXTENSIONS[fmt]
        filename = f"{slug}{ext}"
        media_type = FORMAT_MEDIA_TYPES[fmt]

        return buf, filename, media_type

    async def export_unit(
        self,
        unit_id: str,
        db: Session,
        fmt: ExportFormat,
        title: str | None = None,
        author: str | None = None,
    ) -> tuple[BytesIO, str, str]:
        """
        Export an entire unit (all contents, ordered by week and order_index)
        as a single document.

        Args:
            unit_id: The unit ID to export.
            db: Database session.
            fmt: Target export format.
            title: Optional title override (uses unit title if not provided).
            author: Optional author name for the document metadata.

        Returns:
            Tuple of (BytesIO buffer, filename, media_type).
        """
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            msg = f"Unit {unit_id} not found"
            raise ValueError(msg)

        # Build combined markdown from all contents
        contents = (
            db.query(Content)
            .filter(Content.unit_id == unit_id)
            .order_by(Content.week_number, Content.order_index)
            .all()
        )

        sections: list[str] = []

        # Unit header
        doc_title = title or unit.title or "Untitled Unit"
        if unit.code:
            doc_title = f"{unit.code} — {doc_title}"

        if unit.description:
            sections.append(unit.description)
            sections.append("")

        # Group by week
        current_week: int | None = None
        for c in contents:
            week = c.week_number
            if week is not None and week != current_week:
                current_week = week
                sections.append(f"# Week {week}")
                sections.append("")

            # Content title as heading
            heading_level = "##" if week is not None else "#"
            sections.append(f"{heading_level} {c.title or 'Untitled'}")
            sections.append("")

            body = c.content_markdown or c.content_html or ""
            if body.strip():
                sections.append(body.strip())
                sections.append("")

        markdown = "\n".join(sections)

        buf = self._convert(
            markdown=markdown,
            fmt=fmt,
            title=doc_title,
            author=author,
        )

        slug = self._slugify(doc_title)
        ext = FORMAT_EXTENSIONS[fmt]
        filename = f"{slug}{ext}"
        media_type = FORMAT_MEDIA_TYPES[fmt]

        return buf, filename, media_type

    def _convert(
        self,
        markdown: str,
        fmt: ExportFormat,
        title: str | None = None,
        author: str | None = None,
    ) -> BytesIO:
        """
        Convert markdown to the target format using Pandoc (+ Typst for PDF).

        Returns a BytesIO buffer containing the output file.
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="cc_export_"))

        try:
            # Write markdown source
            input_file = temp_dir / "input.md"
            input_file.write_text(markdown, encoding="utf-8")

            if fmt == ExportFormat.PDF:
                return self._convert_pdf(input_file, temp_dir, title, author)
            return self._convert_pandoc(
                input_file, temp_dir, fmt, title, author
            )
        finally:
            # Clean up temp dir
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _convert_pandoc(
        self,
        input_file: Path,
        temp_dir: Path,
        fmt: ExportFormat,
        title: str | None,
        author: str | None,
    ) -> BytesIO:
        """Convert using Pandoc directly (HTML, DOCX, PPTX)."""
        ext = FORMAT_EXTENSIONS[fmt]
        output_file = temp_dir / f"output{ext}"

        cmd = [
            self.pandoc_path,
            str(input_file),
            "-o",
            str(output_file),
            "--standalone",
        ]

        if title:
            cmd.extend(["--metadata", f"title={title}"])
        if author:
            cmd.extend(["--metadata", f"author={author}"])

        # Format-specific options
        if fmt == ExportFormat.HTML:
            cmd.extend(["--self-contained", "--embed-resources"])

        logger.info(f"Running Pandoc: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            cwd=temp_dir,
        )

        if result.returncode != 0:
            logger.error(f"Pandoc failed: {result.stderr}")
            msg = f"Pandoc conversion to {fmt.value} failed: {result.stderr}"
            raise RuntimeError(msg)

        buf = BytesIO(output_file.read_bytes())
        buf.seek(0)
        return buf

    def _convert_pdf(
        self,
        input_file: Path,
        temp_dir: Path,
        title: str | None,
        author: str | None,
    ) -> BytesIO:
        """Convert to PDF via Pandoc → Typst pipeline."""
        typst_file = temp_dir / "output.typ"
        pdf_file = temp_dir / "output.pdf"

        # Step 1: Markdown → Typst markup via Pandoc
        pandoc_cmd = [
            self.pandoc_path,
            str(input_file),
            "-o",
            str(typst_file),
            "--to",
            "typst",
        ]

        if title:
            pandoc_cmd.extend(["--metadata", f"title={title}"])
        if author:
            pandoc_cmd.extend(["--metadata", f"author={author}"])

        logger.info(f"Running Pandoc (→ Typst): {' '.join(pandoc_cmd)}")
        result = subprocess.run(
            pandoc_cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            cwd=temp_dir,
        )

        if result.returncode != 0:
            logger.error(f"Pandoc → Typst failed: {result.stderr}")
            msg = f"Pandoc → Typst conversion failed: {result.stderr}"
            raise RuntimeError(msg)

        # Step 2: Typst markup → PDF
        typst_cmd = [
            self.typst_path,
            "compile",
            str(typst_file),
            str(pdf_file),
        ]

        logger.info(f"Running Typst: {' '.join(typst_cmd)}")
        result = subprocess.run(
            typst_cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            cwd=temp_dir,
        )

        if result.returncode != 0:
            logger.error(f"Typst compile failed: {result.stderr}")
            msg = f"Typst PDF compilation failed: {result.stderr}"
            raise RuntimeError(msg)

        buf = BytesIO(pdf_file.read_bytes())
        buf.seek(0)
        return buf

    @staticmethod
    def _slugify(text: str) -> str:
        """Create a safe filename slug from text."""
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug[:80].strip("-") or "export"

    def cleanup_old_outputs(self, max_age_hours: int = 24) -> int:
        """Clean up old output files. Returns count of files removed."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        removed = 0

        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    removed += 1

        return removed


# Singleton instance
export_service = ExportService()
