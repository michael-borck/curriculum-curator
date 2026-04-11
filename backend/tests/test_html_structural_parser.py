"""
Tests for the structural HTML material parser.

Each test feeds a real HTML string to the parser and asserts on the
resulting content_json structure. No mocks — BeautifulSoup parses real
markup, the parser walks the real DOM.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.material_parsers.html_structural import HtmlStructuralParser


@pytest.fixture
def parser() -> HtmlStructuralParser:
    return HtmlStructuralParser()


# ---------------------------------------------------------------------------
# Helpers for asserting on the content tree
# ---------------------------------------------------------------------------


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


def _all_marks(node: dict[str, Any]) -> list[str]:
    """Collect mark types from every text node in the tree."""
    out: list[str] = []
    if node.get("type") == "text":
        out.extend(m.get("type", "") for m in node.get("marks", []))
    for child in node.get("content", []):
        if isinstance(child, dict):
            out.extend(_all_marks(child))
    return out


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------


class TestBasicStructure:
    @pytest.mark.asyncio
    async def test_empty_html(self, parser: HtmlStructuralParser) -> None:
        result = await parser.parse(b"<html><body></body></html>", "empty.html")
        assert result.parser_used == "html_structural"
        assert result.content_json["type"] == "doc"
        assert result.content_json["content"] == []

    @pytest.mark.asyncio
    async def test_paragraph(self, parser: HtmlStructuralParser) -> None:
        result = await parser.parse(b"<p>Hello world</p>", "p.html")
        nodes = result.content_json["content"]
        assert _node_types(nodes) == ["paragraph"]
        assert _all_text(nodes[0]) == "Hello world"

    @pytest.mark.asyncio
    async def test_heading_levels(self, parser: HtmlStructuralParser) -> None:
        for level in range(1, 7):
            html = f"<h{level}>Title</h{level}>".encode()
            result = await parser.parse(html, f"h{level}.html")
            heading = _find_first(result.content_json["content"], "heading")
            assert heading is not None
            assert heading["attrs"]["level"] == level
            assert _all_text(heading) == "Title"

    @pytest.mark.asyncio
    async def test_title_extracted_from_title_tag(
        self, parser: HtmlStructuralParser
    ) -> None:
        html = b"<html><head><title>My Doc</title></head><body><p>Body</p></body></html>"
        result = await parser.parse(html, "doc.html")
        assert result.title == "My Doc"

    @pytest.mark.asyncio
    async def test_title_falls_back_to_first_heading(
        self, parser: HtmlStructuralParser
    ) -> None:
        result = await parser.parse(b"<h1>From H1</h1><p>x</p>", "doc.html")
        assert result.title == "From H1"

    @pytest.mark.asyncio
    async def test_title_falls_back_to_filename(
        self, parser: HtmlStructuralParser
    ) -> None:
        result = await parser.parse(b"<p>just paragraph</p>", "fallback.html")
        assert result.title == "fallback"


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------


class TestLists:
    @pytest.mark.asyncio
    async def test_bullet_list(self, parser: HtmlStructuralParser) -> None:
        html = b"<ul><li>One</li><li>Two</li></ul>"
        result = await parser.parse(html, "list.html")
        ul = _find_first(result.content_json["content"], "bulletList")
        assert ul is not None
        items = ul["content"]
        assert len(items) == 2
        assert all(item["type"] == "listItem" for item in items)
        assert "One" in _all_text(items[0])
        assert "Two" in _all_text(items[1])

    @pytest.mark.asyncio
    async def test_ordered_list(self, parser: HtmlStructuralParser) -> None:
        html = b"<ol><li>First</li><li>Second</li></ol>"
        result = await parser.parse(html, "ol.html")
        ol = _find_first(result.content_json["content"], "orderedList")
        assert ol is not None
        assert len(ol["content"]) == 2


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


class TestTables:
    @pytest.mark.asyncio
    async def test_table_with_header_row(
        self, parser: HtmlStructuralParser
    ) -> None:
        html = b"""
        <table>
          <thead>
            <tr><th>Name</th><th>Score</th></tr>
          </thead>
          <tbody>
            <tr><td>Alice</td><td>90</td></tr>
            <tr><td>Bob</td><td>85</td></tr>
          </tbody>
        </table>
        """
        result = await parser.parse(html, "table.html")
        table = _find_first(result.content_json["content"], "table")
        assert table is not None
        rows = table["content"]
        assert len(rows) == 3
        first_row_cells = rows[0]["content"]
        assert all(c["type"] == "tableHeader" for c in first_row_cells)
        assert "Name" in _all_text(table)
        assert "Bob" in _all_text(table)

    @pytest.mark.asyncio
    async def test_table_without_thead(
        self, parser: HtmlStructuralParser
    ) -> None:
        html = b"<table><tr><td>x</td><td>y</td></tr></table>"
        result = await parser.parse(html, "t.html")
        table = _find_first(result.content_json["content"], "table")
        assert table is not None
        assert len(table["content"]) == 1


class TestMarks:
    """Bold, italic, and link marks."""

    @pytest.mark.asyncio
    async def test_bold(self, parser: HtmlStructuralParser) -> None:
        result = await parser.parse(b"<p><strong>bold</strong></p>", "b.html")
        marks = _all_marks(result.content_json)
        assert "bold" in marks

    @pytest.mark.asyncio
    async def test_italic(self, parser: HtmlStructuralParser) -> None:
        result = await parser.parse(b"<p><em>italic</em></p>", "i.html")
        marks = _all_marks(result.content_json)
        assert "italic" in marks

    @pytest.mark.asyncio
    async def test_link(self, parser: HtmlStructuralParser) -> None:
        html = b'<p><a href="https://example.com">click</a></p>'
        result = await parser.parse(html, "link.html")
        # The link mark applies to text nodes; find one with a link mark
        para = _find_first(result.content_json["content"], "paragraph")
        assert para is not None
        text_node = para["content"][0]
        assert text_node["type"] == "text"
        assert any(m.get("type") == "link" for m in text_node.get("marks", []))
        link_mark = next(
            m for m in text_node["marks"] if m.get("type") == "link"
        )
        assert link_mark["attrs"]["href"] == "https://example.com"


# ---------------------------------------------------------------------------
# Code blocks
# ---------------------------------------------------------------------------


class TestCodeBlocks:
    @pytest.mark.asyncio
    async def test_code_block_with_language(
        self, parser: HtmlStructuralParser
    ) -> None:
        html = b'<pre><code class="language-python">print("hi")</code></pre>'
        result = await parser.parse(html, "code.html")
        cb = _find_first(result.content_json["content"], "codeBlock")
        assert cb is not None
        assert cb["attrs"]["language"] == "python"
        assert 'print("hi")' in _all_text(cb)


# ---------------------------------------------------------------------------
# Sanitisation: drop scripts, styles, iframes, forms
# ---------------------------------------------------------------------------


class TestSanitisation:
    @pytest.mark.asyncio
    async def test_script_dropped(self, parser: HtmlStructuralParser) -> None:
        html = b"<p>before</p><script>alert(1)</script><p>after</p>"
        result = await parser.parse(html, "x.html")
        text = "".join(_all_text(n) for n in result.content_json["content"])
        assert "alert" not in text
        assert "before" in text
        assert "after" in text

    @pytest.mark.asyncio
    async def test_style_dropped(self, parser: HtmlStructuralParser) -> None:
        html = b"<style>body { color: red }</style><p>visible</p>"
        result = await parser.parse(html, "x.html")
        text = "".join(_all_text(n) for n in result.content_json["content"])
        assert "color" not in text
        assert "visible" in text


# ---------------------------------------------------------------------------
# reveal.js conventions: section → slideBreak, aside.notes → speakerNotes
# ---------------------------------------------------------------------------


class TestRevealJsConventions:
    @pytest.mark.asyncio
    async def test_sections_become_slide_breaks(
        self, parser: HtmlStructuralParser
    ) -> None:
        html = b"""
        <div class="reveal">
          <div class="slides">
            <section><h2>Slide 1</h2><p>Body 1</p></section>
            <section><h2>Slide 2</h2><p>Body 2</p></section>
          </div>
        </div>
        """
        result = await parser.parse(html, "deck.html")
        types = _node_types(result.content_json["content"])
        # Two sections → at least one slideBreak between them
        assert "slideBreak" in types

    @pytest.mark.asyncio
    async def test_aside_notes_become_speaker_notes(
        self, parser: HtmlStructuralParser
    ) -> None:
        html = b"""
        <section>
          <h2>Slide</h2>
          <p>Visible body</p>
          <aside class="notes">Speaker prompt here</aside>
        </section>
        """
        result = await parser.parse(html, "deck.html")
        notes = _find_first(result.content_json["content"], "speakerNotes")
        assert notes is not None
        assert "Speaker prompt here" in _all_text(notes)


# ---------------------------------------------------------------------------
# Images: data URLs extracted to ExtractedImage entries
# ---------------------------------------------------------------------------


class TestImages:
    @pytest.mark.asyncio
    async def test_external_image_src_preserved(
        self, parser: HtmlStructuralParser
    ) -> None:
        html = b'<p><img src="https://example.com/foo.png" alt="A"></p>'
        result = await parser.parse(html, "img.html")
        img = _find_first(result.content_json["content"], "image")
        assert img is not None
        assert img["attrs"]["src"] == "https://example.com/foo.png"
        assert img["attrs"]["alt"] == "A"
        # External URLs are NOT extracted as bytes
        assert result.images == []

    @pytest.mark.asyncio
    async def test_data_url_image_extracted(
        self, parser: HtmlStructuralParser
    ) -> None:
        # 1x1 transparent PNG, base64-encoded
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
            "nGNgAAIAAAUAAen63NgAAAAASUVORK5CYII="
        )
        html = f'<p><img src="data:image/png;base64,{png_b64}" alt="X"></p>'
        result = await parser.parse(html.encode(), "img.html")
        # Image extracted as ExtractedImage, src rewritten to placeholder
        assert len(result.images) == 1
        assert result.images[0].mime_type == "image/png"
        assert result.images[0].data  # non-empty bytes
        img = _find_first(result.content_json["content"], "image")
        assert img is not None
        assert img["attrs"]["src"] == result.images[0].filename
        assert not img["attrs"]["src"].startswith("data:")
