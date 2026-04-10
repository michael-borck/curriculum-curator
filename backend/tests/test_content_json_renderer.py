"""
Tests for the content_json renderer (TipTap JSON → HTML).

Covers:
- Each node type renders correctly
- Text marks (bold, italic, code, link combinations)
- quizQuestion node renders as styled HTML block
- Empty/null content_json returns empty string
- Nested structures (list inside blockquote, table with formatted cells)
- render_material_html() fallback behaviour
"""

from __future__ import annotations

from typing import Any

from app.services.content_json_renderer import (
    render_content_json,
    strip_speaker_notes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


def _p(*content: dict[str, Any]) -> dict[str, Any]:
    return {"type": "paragraph", "content": list(content)}


def _text(text: str, marks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return node


# ---------------------------------------------------------------------------
# Basic node types
# ---------------------------------------------------------------------------


class TestBasicNodes:
    def test_empty_input(self) -> None:
        assert render_content_json({}) == ""
        assert render_content_json({"content": []}) == ""

    def test_none_content(self) -> None:
        assert render_content_json({"type": "doc"}) == ""

    def test_paragraph(self) -> None:
        doc = _doc(_p(_text("Hello world")))
        assert render_content_json(doc) == "<p>Hello world</p>"

    def test_heading_levels(self) -> None:
        for level in range(1, 7):
            doc = _doc(
                {"type": "heading", "attrs": {"level": level}, "content": [_text("Title")]}
            )
            assert f"<h{level}>Title</h{level}>" in render_content_json(doc)

    def test_bullet_list(self) -> None:
        doc = _doc(
            {
                "type": "bulletList",
                "content": [
                    {"type": "listItem", "content": [_p(_text("Item 1"))]},
                    {"type": "listItem", "content": [_p(_text("Item 2"))]},
                ],
            }
        )
        html = render_content_json(doc)
        assert "<ul>" in html
        assert "<li><p>Item 1</p></li>" in html
        assert "<li><p>Item 2</p></li>" in html

    def test_ordered_list(self) -> None:
        doc = _doc(
            {
                "type": "orderedList",
                "attrs": {"start": 1},
                "content": [
                    {"type": "listItem", "content": [_p(_text("First"))]},
                ],
            }
        )
        html = render_content_json(doc)
        assert "<ol>" in html
        assert "<li>" in html

    def test_ordered_list_custom_start(self) -> None:
        doc = _doc(
            {
                "type": "orderedList",
                "attrs": {"start": 5},
                "content": [
                    {"type": "listItem", "content": [_p(_text("Fifth"))]},
                ],
            }
        )
        html = render_content_json(doc)
        assert 'start="5"' in html

    def test_code_block(self) -> None:
        doc = _doc(
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [_text("print('hello')")],
            }
        )
        html = render_content_json(doc)
        assert '<pre><code class="language-python">' in html
        assert "print(&#x27;hello&#x27;)" in html

    def test_code_block_mermaid(self) -> None:
        doc = _doc(
            {
                "type": "codeBlock",
                "attrs": {"language": "mermaid"},
                "content": [_text("graph LR; A-->B")],
            }
        )
        html = render_content_json(doc)
        assert '<pre class="mermaid">' in html

    def test_blockquote(self) -> None:
        doc = _doc({"type": "blockquote", "content": [_p(_text("Quote text"))]})
        html = render_content_json(doc)
        assert html == "<blockquote><p>Quote text</p></blockquote>"

    def test_image(self) -> None:
        doc = _doc(
            {
                "type": "image",
                "attrs": {"src": "https://example.com/img.png", "alt": "A photo", "title": "My Image"},
            }
        )
        html = render_content_json(doc)
        assert 'src="https://example.com/img.png"' in html
        assert 'alt="A photo"' in html
        assert 'title="My Image"' in html

    def test_hard_break(self) -> None:
        doc = _doc(_p(_text("Line 1"), {"type": "hardBreak"}, _text("Line 2")))
        html = render_content_json(doc)
        assert "<br>" in html

    def test_horizontal_rule(self) -> None:
        doc = _doc({"type": "horizontalRule"})
        html = render_content_json(doc)
        assert "<hr>" in html

    def test_table(self) -> None:
        doc = _doc(
            {
                "type": "table",
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableHeader",
                                "content": [_p(_text("Header"))],
                            },
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableCell",
                                "content": [_p(_text("Cell"))],
                            },
                        ],
                    },
                ],
            }
        )
        html = render_content_json(doc)
        assert "<table>" in html
        assert "<th><p>Header</p></th>" in html
        assert "<td><p>Cell</p></td>" in html

    def test_table_cell_colspan(self) -> None:
        doc = _doc(
            {
                "type": "table",
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableCell",
                                "attrs": {"colspan": 2, "rowspan": 1},
                                "content": [_p(_text("Wide"))],
                            },
                        ],
                    },
                ],
            }
        )
        html = render_content_json(doc)
        assert 'colspan="2"' in html


# ---------------------------------------------------------------------------
# Text marks
# ---------------------------------------------------------------------------


class TestTextMarks:
    def test_bold(self) -> None:
        doc = _doc(_p(_text("bold", [{"type": "bold"}])))
        assert "<strong>bold</strong>" in render_content_json(doc)

    def test_italic(self) -> None:
        doc = _doc(_p(_text("italic", [{"type": "italic"}])))
        assert "<em>italic</em>" in render_content_json(doc)

    def test_code(self) -> None:
        doc = _doc(_p(_text("code", [{"type": "code"}])))
        assert "<code>code</code>" in render_content_json(doc)

    def test_underline(self) -> None:
        doc = _doc(_p(_text("underlined", [{"type": "underline"}])))
        assert "<u>underlined</u>" in render_content_json(doc)

    def test_strike(self) -> None:
        doc = _doc(_p(_text("struck", [{"type": "strike"}])))
        assert "<s>struck</s>" in render_content_json(doc)

    def test_highlight(self) -> None:
        doc = _doc(_p(_text("highlighted", [{"type": "highlight"}])))
        assert "<mark>highlighted</mark>" in render_content_json(doc)

    def test_link(self) -> None:
        doc = _doc(
            _p(_text("click here", [{"type": "link", "attrs": {"href": "https://example.com"}}]))
        )
        html = render_content_json(doc)
        assert '<a href="https://example.com">click here</a>' in html

    def test_combined_marks(self) -> None:
        doc = _doc(_p(_text("bold italic", [{"type": "bold"}, {"type": "italic"}])))
        html = render_content_json(doc)
        assert "<strong>" in html
        assert "<em>" in html

    def test_html_escaping(self) -> None:
        doc = _doc(_p(_text("<script>alert('xss')</script>")))
        html = render_content_json(doc)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


# ---------------------------------------------------------------------------
# Quiz question rendering
# ---------------------------------------------------------------------------


class TestQuizQuestionRendering:
    def test_multiple_choice(self) -> None:
        doc = _doc(
            {
                "type": "quizQuestion",
                "attrs": {
                    "questionText": "What is 2+2?",
                    "questionType": "multiple_choice",
                    "options": [
                        {"text": "3", "correct": False},
                        {"text": "4", "correct": True},
                    ],
                    "feedback": "Basic arithmetic",
                    "points": 1.0,
                },
            }
        )
        html = render_content_json(doc)
        assert "quiz-question" in html
        assert "What is 2+2?" in html
        assert "Multiple Choice" in html
        assert "&#10003;" in html  # checkmark for correct answer
        assert "Basic arithmetic" in html

    def test_quiz_inside_content(self) -> None:
        doc = _doc(
            _p(_text("Introduction")),
            {
                "type": "quizQuestion",
                "attrs": {
                    "questionText": "Is this a test?",
                    "questionType": "true_false",
                    "options": [
                        {"text": "True", "correct": True},
                        {"text": "False", "correct": False},
                    ],
                    "points": 1.0,
                },
            },
            _p(_text("Conclusion")),
        )
        html = render_content_json(doc)
        assert "<p>Introduction</p>" in html
        assert "Is this a test?" in html
        assert "<p>Conclusion</p>" in html


# ---------------------------------------------------------------------------
# Nested structures
# ---------------------------------------------------------------------------


class TestNestedStructures:
    def test_list_inside_blockquote(self) -> None:
        doc = _doc(
            {
                "type": "blockquote",
                "content": [
                    {
                        "type": "bulletList",
                        "content": [
                            {"type": "listItem", "content": [_p(_text("Nested item"))]},
                        ],
                    }
                ],
            }
        )
        html = render_content_json(doc)
        assert html == "<blockquote><ul><li><p>Nested item</p></li></ul></blockquote>"

    def test_table_with_formatted_cells(self) -> None:
        doc = _doc(
            {
                "type": "table",
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableCell",
                                "content": [
                                    _p(_text("bold text", [{"type": "bold"}]))
                                ],
                            },
                        ],
                    },
                ],
            }
        )
        html = render_content_json(doc)
        assert "<strong>bold text</strong>" in html

    def test_unknown_node_skipped(self) -> None:
        doc = _doc(
            {"type": "unknownWidget", "content": [_p(_text("inner"))]},
            _p(_text("after")),
        )
        html = render_content_json(doc)
        # Unknown nodes render their children
        assert "<p>inner</p>" in html
        assert "<p>after</p>" in html


# ---------------------------------------------------------------------------
# Speaker notes rendering
# ---------------------------------------------------------------------------


def _speaker_notes(*content: dict[str, Any]) -> dict[str, Any]:
    return {"type": "speakerNotes", "content": list(content)}


class TestSpeakerNotesRendering:
    def test_html_target_emits_aside(self) -> None:
        doc = _doc(_speaker_notes(_p(_text("Remember the framing here."))))
        html = render_content_json(doc)
        assert html == (
            '<aside data-type="speaker-notes">'
            "<p>Remember the framing here.</p>"
            "</aside>"
        )

    def test_pandoc_target_emits_fenced_div(self) -> None:
        doc = _doc(_speaker_notes(_p(_text("Pause for questions."))))
        out = render_content_json(doc, target="pandoc")
        # Pandoc fenced divs require blank lines around them
        assert "::: notes" in out
        assert ":::" in out
        assert "Pause for questions" in out
        # Verify the blank-line padding (Pandoc needs it to recognise the block)
        assert out.startswith("\n\n::: notes")
        assert out.endswith(":::\n\n")

    def test_pandoc_target_renders_inner_marks(self) -> None:
        # Notes should support the same marks as body content
        doc = _doc(
            _speaker_notes(_p(_text("emphasise", [{"type": "bold"}])))
        )
        out = render_content_json(doc, target="pandoc")
        assert "<strong>emphasise</strong>" in out

    def test_html_target_default(self) -> None:
        # Calling without target should default to html (backwards compat)
        doc = _doc(_speaker_notes(_p(_text("Note"))))
        out = render_content_json(doc)
        assert "<aside" in out
        assert "::: notes" not in out

    def test_notes_alongside_other_content(self) -> None:
        doc = _doc(
            _p(_text("Slide body")),
            _speaker_notes(_p(_text("Delivery prompt"))),
        )
        html = render_content_json(doc)
        assert "<p>Slide body</p>" in html
        assert "Delivery prompt" in html

    def test_empty_notes_node(self) -> None:
        # An empty notes node should still render — the user may scaffold
        # the block before typing content into it
        doc = _doc(_speaker_notes())
        html = render_content_json(doc)
        assert '<aside data-type="speaker-notes">' in html

    def test_notes_inside_doc_with_slide_break(self) -> None:
        # Notes adjacent to a slide break — both render (split is the
        # splitter's job, the renderer just walks the tree)
        doc = _doc(
            _p(_text("Slide 1 content")),
            _speaker_notes(_p(_text("Notes for slide 1"))),
            {"type": "slideBreak"},
            _p(_text("Slide 2 content")),
        )
        out = render_content_json(doc, target="pandoc")
        assert "Slide 1 content" in out
        assert "Notes for slide 1" in out
        assert "Slide 2 content" in out
        assert "::: notes" in out


# ---------------------------------------------------------------------------
# strip_speaker_notes
# ---------------------------------------------------------------------------


class TestStripSpeakerNotes:
    def test_removes_top_level_notes(self) -> None:
        doc = _doc(
            _p(_text("Body")),
            _speaker_notes(_p(_text("Hidden"))),
            _p(_text("More body")),
        )
        result = strip_speaker_notes(doc)
        types = [n["type"] for n in result["content"]]
        assert "speakerNotes" not in types
        assert types == ["paragraph", "paragraph"]

    def test_does_not_mutate_input(self) -> None:
        doc = _doc(_speaker_notes(_p(_text("Stay put"))))
        original_types = [n["type"] for n in doc["content"]]
        strip_speaker_notes(doc)
        # Original document is unchanged
        assert [n["type"] for n in doc["content"]] == original_types
        assert original_types == ["speakerNotes"]

    def test_removes_nested_notes(self) -> None:
        # Notes inside another block (e.g. inside a blockquote — unusual
        # but the schema allows block+ nesting). Strip should recurse.
        doc = _doc(
            {
                "type": "blockquote",
                "content": [
                    _p(_text("Quote")),
                    _speaker_notes(_p(_text("Hidden in quote"))),
                ],
            }
        )
        result = strip_speaker_notes(doc)
        # Walk the result tree manually to assert no speakerNotes anywhere
        def has_notes(nodes: list[dict[str, Any]]) -> bool:
            for node in nodes:
                if node.get("type") == "speakerNotes":
                    return True
                if (
                    "content" in node
                    and isinstance(node["content"], list)
                    and has_notes(node["content"])
                ):
                    return True
            return False

        assert not has_notes(result["content"])

    def test_empty_input(self) -> None:
        assert strip_speaker_notes({}) == {}
        # Doc with no content key passes through
        result = strip_speaker_notes({"type": "doc"})
        assert result == {"type": "doc"}

    def test_doc_without_notes_returns_equivalent(self) -> None:
        doc = _doc(_p(_text("No notes here")))
        result = strip_speaker_notes(doc)
        assert result["content"][0]["content"][0]["text"] == "No notes here"

    def test_preserves_slide_breaks(self) -> None:
        # Slide breaks must survive note stripping (they're a different
        # node type and the splitter still needs them)
        doc = _doc(
            _p(_text("Slide 1")),
            _speaker_notes(_p(_text("Hidden"))),
            {"type": "slideBreak"},
            _p(_text("Slide 2")),
        )
        result = strip_speaker_notes(doc)
        types = [n["type"] for n in result["content"]]
        assert "slideBreak" in types
        assert "speakerNotes" not in types


# ---------------------------------------------------------------------------
# render_material_html fallback
# ---------------------------------------------------------------------------


class TestRenderMaterialHtml:
    def test_prefers_content_json(self) -> None:
        from app.services.unit_export_data import render_material_html

        class FakeMaterial:
            content_json = _doc(_p(_text("From editor")))
            description = "Old description"

        html = render_material_html(FakeMaterial())  # type: ignore[arg-type]
        assert "From editor" in html
        assert "Old description" not in html

    def test_falls_back_to_description(self) -> None:
        from app.services.unit_export_data import render_material_html

        class FakeMaterial:
            content_json = None
            description = "<p>Legacy content</p>"

        html = render_material_html(FakeMaterial())  # type: ignore[arg-type]
        assert html == "<p>Legacy content</p>"

    def test_empty_material(self) -> None:
        from app.services.unit_export_data import render_material_html

        class FakeMaterial:
            content_json = None
            description = None

        html = render_material_html(FakeMaterial())  # type: ignore[arg-type]
        assert html == ""

    def test_strips_speaker_notes(self) -> None:
        # render_material_html is the central path for non-PPTX exports
        # (HTML, IMSCC, SCORM, DOCX, PDF). Per ADR-064, speaker notes must
        # not appear in any student-facing export.
        from app.services.unit_export_data import render_material_html

        class FakeMaterial:
            content_json = _doc(
                _p(_text("Visible body")),
                _speaker_notes(_p(_text("Hidden delivery prompt"))),
            )
            description = ""

        html = render_material_html(FakeMaterial())  # type: ignore[arg-type]
        assert "Visible body" in html
        assert "Hidden delivery prompt" not in html
        assert "speaker-notes" not in html
