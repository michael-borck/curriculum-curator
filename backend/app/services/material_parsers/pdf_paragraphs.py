"""
Plain-paragraph PDF parser — converts a PDF into flat paragraph nodes.

Phase 2 default for ``.pdf`` files. PDF structure (headings, lists,
tables) is fundamentally unrecoverable from the underlying text stream
without heuristics that fail unpredictably on real-world documents.
This parser is honest about that limit: it extracts the text via
``pdf_parser_service`` (which already chooses the best of PyPDF2 /
pdfplumber / PyMuPDF per document), splits it into paragraphs on
double newlines, and emits ``paragraph`` nodes only.

A single warning is emitted so the user knows what was lost. The
opt-in ``pdf_llm`` parser (Phase 4 of docs/structured-import-plan.md)
will offer an LLM-assisted second pass that recovers structure when
AI is enabled, but the default remains plain paragraphs because PDF
imports must work without AI.

Per ADR-038 the parser deliberately discards positioning, fonts, and
visual decoration. Per ADR-061 the warning makes the lossy nature of
PDF import explicit rather than silently producing low-fidelity output.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, ClassVar

from app.services.material_parsers.base import (
    MaterialParser,
    MaterialParseResult,
)

logger = logging.getLogger(__name__)


# Regex to split on double-newline (one or more blank lines between blocks)
_PARAGRAPH_SEPARATOR = re.compile(r"\n\s*\n+")


class PdfParagraphsParser(MaterialParser):
    """Convert a PDF into flat paragraph nodes (no structure recovery)."""

    name: ClassVar[str] = "pdf_paragraphs"
    display_name: ClassVar[str] = "PDF (plain paragraphs)"
    description: ClassVar[str] = (
        "Default PDF importer. Extracts text and emits flat paragraphs — "
        "PDF structure (headings, lists, tables) is not recovered. Use the "
        "AI-assisted PDF parser to attempt structural recovery when AI is "
        "available."
    )
    supported_formats: ClassVar[list[str]] = ["pdf"]
    requires_ai: ClassVar[bool] = False

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> MaterialParseResult:
        _ = user_context

        # Lazy import to avoid pulling pdf_parser_service into the registry
        # at module-load time (it has heavy optional dependencies)
        from app.services.pdf_parser_service import (  # noqa: PLC0415
            pdf_parser_service,
        )

        document = await pdf_parser_service.extract_from_bytes(file_content)

        # Title preference: PDF metadata title → first non-empty paragraph
        # → filename stem
        doc_title: str | None = None
        if document.metadata and document.metadata.title:
            doc_title = document.metadata.title.strip() or None

        nodes: list[dict[str, Any]] = []
        paragraphs = self._split_paragraphs(document.full_text)

        for para_text in paragraphs:
            cleaned = para_text.strip()
            if not cleaned:
                continue
            # Collapse internal whitespace runs to a single space — PDF
            # text often has odd line-wrapping artefacts mid-paragraph
            normalised = re.sub(r"\s+", " ", cleaned)
            nodes.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": normalised}],
                }
            )
            # Use the first paragraph as title if metadata didn't give one
            if doc_title is None:
                doc_title = normalised[:100]

        if not doc_title:
            doc_title = Path(filename).stem or "Untitled"

        warnings: list[str] = [
            "PDF imported as plain paragraphs. Structure (headings, lists, "
            "tables, images) was not recovered. Edit in the editor to add "
            "structure, or re-import with the AI-assisted PDF parser when "
            "available."
        ]

        # Surface any extraction errors from pdf_parser_service as warnings
        if document.extraction_errors:
            warnings.extend(
                f"PDF extraction warning: {err}"
                for err in document.extraction_errors
            )

        return MaterialParseResult(
            title=doc_title,
            content_json={"type": "doc", "content": nodes},
            images=[],  # v1: no image extraction from PDFs
            warnings=warnings,
            parser_used=self.name,
        )

    @staticmethod
    def _split_paragraphs(text: str) -> list[str]:
        """Split a flat text blob into paragraph candidates.

        We split on runs of blank lines (one or more newline-only lines
        between non-blank content). Single newlines within a paragraph
        are normalised to spaces by the caller.
        """
        if not text:
            return []
        return _PARAGRAPH_SEPARATOR.split(text)
