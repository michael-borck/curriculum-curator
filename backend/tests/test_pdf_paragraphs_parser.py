"""
Tests for the plain-paragraph PDF material parser.

Generates real PDFs in memory using pymupdf (already a project dep) and
runs them through the parser. The parser is intentionally lossy — it
emits paragraph nodes only — so tests focus on text preservation,
title extraction, paragraph splitting, and the warnings contract.
"""

from __future__ import annotations

import io
from typing import Any

import fitz  # PyMuPDF — already a dep
import pytest

from app.services.material_parsers.pdf_paragraphs import PdfParagraphsParser


@pytest.fixture
def parser() -> PdfParagraphsParser:
    return PdfParagraphsParser()


# ---------------------------------------------------------------------------
# PDF builders
# ---------------------------------------------------------------------------


def _build_pdf(text_blocks: list[str], title: str | None = None) -> bytes:
    """Build a single-page PDF with the given text blocks separated by
    blank lines (so the parser sees them as distinct paragraphs)."""
    doc = fitz.open()
    if title:
        doc.set_metadata({"title": title})
    page = doc.new_page()

    # Insert each block as a separate paragraph by adding blank lines
    # between them. PyMuPDF's insert_text starts at the given point.
    y = 72.0  # 1 inch from top
    for block in text_blocks:
        page.insert_text((72, y), block, fontsize=12)
        y += 36  # ~half-inch gap creates a paragraph break

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return buf.read()


def _node_types(content: list[dict[str, Any]]) -> list[str]:
    return [n.get("type", "") for n in content]


def _all_text(node: dict[str, Any]) -> str:
    if node.get("type") == "text":
        return str(node.get("text", ""))
    return "".join(
        _all_text(child)
        for child in node.get("content", [])
        if isinstance(child, dict)
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPdfBasic:
    @pytest.mark.asyncio
    async def test_single_paragraph(self, parser: PdfParagraphsParser) -> None:
        result = await parser.parse(
            _build_pdf(["Hello world from a PDF"]),
            "doc.pdf",
        )
        assert result.parser_used == "pdf_paragraphs"
        assert result.content_json["type"] == "doc"
        # The parser should produce at least one paragraph containing the text
        all_text = "".join(
            _all_text(n) for n in result.content_json["content"]
        )
        assert "Hello world" in all_text

    @pytest.mark.asyncio
    async def test_multiple_paragraphs(self, parser: PdfParagraphsParser) -> None:
        result = await parser.parse(
            _build_pdf(
                ["First paragraph here.", "Second paragraph here.", "Third one."]
            ),
            "multi.pdf",
        )
        nodes = result.content_json["content"]
        assert all(n.get("type") == "paragraph" for n in nodes)
        all_text = " ".join(_all_text(n) for n in nodes)
        assert "First paragraph" in all_text
        assert "Second paragraph" in all_text
        assert "Third one" in all_text

    @pytest.mark.asyncio
    async def test_only_paragraph_nodes_emitted(
        self, parser: PdfParagraphsParser
    ) -> None:
        # The parser is honest about being structureless: no headings,
        # no lists, no tables, just paragraphs
        result = await parser.parse(
            _build_pdf(["Plain text", "Another block"]),
            "p.pdf",
        )
        types = set(_node_types(result.content_json["content"]))
        assert types == {"paragraph"}


class TestPdfTitle:
    @pytest.mark.asyncio
    async def test_title_from_pdf_metadata(
        self, parser: PdfParagraphsParser
    ) -> None:
        result = await parser.parse(
            _build_pdf(["Body content"], title="My PDF Title"),
            "doc.pdf",
        )
        assert result.title == "My PDF Title"

    @pytest.mark.asyncio
    async def test_title_falls_back_to_first_paragraph(
        self, parser: PdfParagraphsParser
    ) -> None:
        result = await parser.parse(
            _build_pdf(["This is the first paragraph and becomes the title"]),
            "untitled.pdf",
        )
        # Title should contain the first paragraph (truncated to 100 chars)
        assert result.title is not None
        assert "first paragraph" in result.title.lower()

    @pytest.mark.asyncio
    async def test_title_falls_back_to_filename(
        self, parser: PdfParagraphsParser
    ) -> None:
        # Empty PDF (no body text, no metadata title)
        doc = fitz.open()
        doc.new_page()  # blank page
        buf = io.BytesIO()
        doc.save(buf)
        doc.close()
        buf.seek(0)
        result = await parser.parse(buf.read(), "fallback.pdf")
        assert result.title == "fallback"


class TestPdfWarnings:
    @pytest.mark.asyncio
    async def test_lossy_warning_always_emitted(
        self, parser: PdfParagraphsParser
    ) -> None:
        result = await parser.parse(
            _build_pdf(["Some content"]),
            "doc.pdf",
        )
        assert len(result.warnings) >= 1
        first_warning = result.warnings[0]
        assert "plain paragraphs" in first_warning.lower()
        assert "structure" in first_warning.lower()

    @pytest.mark.asyncio
    async def test_no_images_extracted(
        self, parser: PdfParagraphsParser
    ) -> None:
        # v1 doesn't extract PDF images — confirmed by the empty list
        result = await parser.parse(_build_pdf(["text"]), "doc.pdf")
        assert result.images == []
