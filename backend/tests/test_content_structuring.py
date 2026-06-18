"""Tests for content structuring helpers (story 6.16)."""

from app.schemas.ai import StructuredBlock, StructuredDocument
from app.services.content_structuring import (
    flatten_content_to_text,
    structured_document_to_content_json,
)


def _para(text: str) -> dict:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


class TestFlatten:
    def test_flattens_paragraphs_to_lines(self):
        doc = {"type": "doc", "content": [_para("One"), _para("Two")]}
        assert flatten_content_to_text(doc) == "One\nTwo"

    def test_flattens_list_items_to_separate_lines(self):
        doc = {
            "type": "doc",
            "content": [
                _para("Intro"),
                {
                    "type": "bulletList",
                    "content": [
                        {"type": "listItem", "content": [_para("first")]},
                        {"type": "listItem", "content": [_para("second")]},
                    ],
                },
            ],
        }
        assert flatten_content_to_text(doc) == "Intro\nfirst\nsecond"

    def test_drops_empty_blocks(self):
        doc = {"type": "doc", "content": [_para("Keep"), _para("   ")]}
        assert flatten_content_to_text(doc) == "Keep"

    def test_handles_missing_content(self):
        assert flatten_content_to_text(None) == ""
        assert flatten_content_to_text({}) == ""


class TestConvert:
    def test_maps_block_kinds_to_nodes(self):
        doc = StructuredDocument(
            blocks=[
                StructuredBlock(kind="heading", level=1, text="Title"),
                StructuredBlock(kind="paragraph", text="Body text"),
                StructuredBlock(kind="bullet_list", items=["a", "b"]),
                StructuredBlock(kind="ordered_list", items=["1", "2"]),
            ]
        )
        content, headings, lists, paragraphs = (
            structured_document_to_content_json(doc)
        )
        types = [n["type"] for n in content["content"]]
        assert types == ["heading", "paragraph", "bulletList", "orderedList"]
        assert content["content"][0]["attrs"]["level"] == 1
        assert headings == 1
        assert lists == 2
        assert paragraphs == 1

    def test_unknown_kind_degrades_to_paragraph(self):
        doc = StructuredDocument(
            blocks=[StructuredBlock(kind="weird", text="still kept")]
        )
        content, _, _, paragraphs = structured_document_to_content_json(doc)
        assert content["content"][0]["type"] == "paragraph"
        assert paragraphs == 1

    def test_skips_empty_blocks(self):
        doc = StructuredDocument(
            blocks=[
                StructuredBlock(kind="heading", text="   "),
                StructuredBlock(kind="bullet_list", items=["", "  "]),
                StructuredBlock(kind="paragraph", text="real"),
            ]
        )
        _content, headings, lists, paragraphs = (
            structured_document_to_content_json(doc)
        )
        assert headings == 0
        assert lists == 0
        assert paragraphs == 1

    def test_never_returns_empty_document(self):
        doc = StructuredDocument(blocks=[])
        content, _, _, _ = structured_document_to_content_json(doc)
        assert len(content["content"]) == 1
        assert content["content"][0]["type"] == "paragraph"
