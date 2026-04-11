"""
Tests for the structural Markdown material parser.

The md parser delegates to the html parser via the markdown library, so
these tests focus on the markdown-specific transformations: front-matter
stripping, --- thematic breaks → slideBreak, and end-to-end conversion
of common markdown constructs.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.material_parsers.md_structural import MdStructuralParser


@pytest.fixture
def parser() -> MdStructuralParser:
    return MdStructuralParser()


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


def _find_first(content: list[dict[str, Any]], node_type: str) -> dict[str, Any] | None:
    for n in content:
        if n.get("type") == node_type:
            return n
        children = n.get("content", [])
        if isinstance(children, list):
            found = _find_first(children, node_type)
            if found:
                return found
    return None


# ---------------------------------------------------------------------------
# Basic markdown
# ---------------------------------------------------------------------------


class TestBasicMarkdown:
    @pytest.mark.asyncio
    async def test_paragraph(self, parser: MdStructuralParser) -> None:
        result = await parser.parse(b"Hello world", "p.md")
        assert result.parser_used == "md_structural"
        nodes = result.content_json["content"]
        assert _node_types(nodes) == ["paragraph"]
        assert _all_text(nodes[0]) == "Hello world"

    @pytest.mark.asyncio
    async def test_headings(self, parser: MdStructuralParser) -> None:
        md = b"# Heading 1\n\n## Heading 2\n\n### Heading 3\n"
        result = await parser.parse(md, "h.md")
        nodes = result.content_json["content"]
        types = _node_types(nodes)
        assert types == ["heading", "heading", "heading"]
        assert nodes[0]["attrs"]["level"] == 1
        assert nodes[1]["attrs"]["level"] == 2
        assert nodes[2]["attrs"]["level"] == 3

    @pytest.mark.asyncio
    async def test_bullet_list(self, parser: MdStructuralParser) -> None:
        md = b"- one\n- two\n- three\n"
        result = await parser.parse(md, "list.md")
        ul = _find_first(result.content_json["content"], "bulletList")
        assert ul is not None
        assert len(ul["content"]) == 3

    @pytest.mark.asyncio
    async def test_ordered_list(self, parser: MdStructuralParser) -> None:
        md = b"1. first\n2. second\n3. third\n"
        result = await parser.parse(md, "ol.md")
        ol = _find_first(result.content_json["content"], "orderedList")
        assert ol is not None
        assert len(ol["content"]) == 3

    @pytest.mark.asyncio
    async def test_inline_marks(self, parser: MdStructuralParser) -> None:
        md = b"This is **bold** and *italic* text"
        result = await parser.parse(md, "marks.md")
        para = _find_first(result.content_json["content"], "paragraph")
        assert para is not None
        marks_seen: list[str] = []
        for node in para["content"]:
            if node.get("type") == "text":
                marks_seen.extend(m.get("type", "") for m in node.get("marks", []))
        assert "bold" in marks_seen
        assert "italic" in marks_seen

    @pytest.mark.asyncio
    async def test_link(self, parser: MdStructuralParser) -> None:
        md = b"[click here](https://example.com)"
        result = await parser.parse(md, "link.md")
        # Find a text node with a link mark
        para = _find_first(result.content_json["content"], "paragraph")
        assert para is not None
        text = para["content"][0]
        assert text["type"] == "text"
        assert any(m.get("type") == "link" for m in text.get("marks", []))


# ---------------------------------------------------------------------------
# Code blocks
# ---------------------------------------------------------------------------


class TestCodeBlocks:
    @pytest.mark.asyncio
    async def test_fenced_code_with_language(
        self, parser: MdStructuralParser
    ) -> None:
        md = b"```python\nprint('hi')\n```\n"
        result = await parser.parse(md, "code.md")
        cb = _find_first(result.content_json["content"], "codeBlock")
        assert cb is not None
        assert cb["attrs"]["language"] == "python"
        assert "print('hi')" in _all_text(cb)

    @pytest.mark.asyncio
    async def test_fenced_code_no_language(
        self, parser: MdStructuralParser
    ) -> None:
        md = b"```\nplain code\n```\n"
        result = await parser.parse(md, "code.md")
        cb = _find_first(result.content_json["content"], "codeBlock")
        assert cb is not None
        assert "plain code" in _all_text(cb)


# ---------------------------------------------------------------------------
# Tables (GFM extension)
# ---------------------------------------------------------------------------


class TestTables:
    @pytest.mark.asyncio
    async def test_gfm_table(self, parser: MdStructuralParser) -> None:
        md = b"""
| Name  | Score |
|-------|-------|
| Alice | 90    |
| Bob   | 85    |
"""
        result = await parser.parse(md, "table.md")
        table = _find_first(result.content_json["content"], "table")
        assert table is not None
        # Header row + 2 data rows
        assert len(table["content"]) == 3
        # First row should be header cells
        assert all(c["type"] == "tableHeader" for c in table["content"][0]["content"])
        assert "Alice" in _all_text(table)


# ---------------------------------------------------------------------------
# Slide breaks: top-level --- becomes a slideBreak node
# ---------------------------------------------------------------------------


class TestSlideBreaks:
    @pytest.mark.asyncio
    async def test_thematic_break_becomes_slide_break(
        self, parser: MdStructuralParser
    ) -> None:
        md = b"""# Slide 1

Body 1

---

# Slide 2

Body 2
"""
        result = await parser.parse(md, "deck.md")
        types = _node_types(result.content_json["content"])
        assert "slideBreak" in types
        # And no leftover horizontalRule (it was rewritten)
        assert "horizontalRule" not in types


# ---------------------------------------------------------------------------
# Front-matter stripping
# ---------------------------------------------------------------------------


class TestFrontMatter:
    @pytest.mark.asyncio
    async def test_front_matter_stripped(
        self, parser: MdStructuralParser
    ) -> None:
        md = b"""---
title: My Document
author: Someone
---

# Real Heading

Body content
"""
        result = await parser.parse(md, "fm.md")
        # The front-matter should not appear as content
        all_text = "".join(
            _all_text(n) for n in result.content_json["content"]
        )
        assert "title:" not in all_text
        assert "author:" not in all_text
        # But the real content should
        assert "Real Heading" in all_text
        assert "Body content" in all_text

    @pytest.mark.asyncio
    async def test_no_front_matter_passes_through(
        self, parser: MdStructuralParser
    ) -> None:
        md = b"# Just a heading\n\nNo front matter here.\n"
        result = await parser.parse(md, "plain.md")
        assert "Just a heading" in _all_text(result.content_json)
        assert "No front matter" in _all_text(result.content_json)


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------


class TestTitle:
    @pytest.mark.asyncio
    async def test_title_from_first_heading(
        self, parser: MdStructuralParser
    ) -> None:
        md = b"# My Document\n\nBody"
        result = await parser.parse(md, "doc.md")
        assert result.title == "My Document"

    @pytest.mark.asyncio
    async def test_title_falls_back_to_filename(
        self, parser: MdStructuralParser
    ) -> None:
        result = await parser.parse(b"just text, no heading", "fallback.md")
        assert result.title == "fallback"
