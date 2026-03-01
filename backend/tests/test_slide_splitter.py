"""
Tests for the slide splitter utility.

Covers:
- No breaks → 1 segment
- 1 break → 2 segments
- N breaks → N+1 segments
- Leading break filtered (empty leading segment)
- Empty input → 1 segment
- Segments are valid docs with type="doc" and content list
- has_slide_breaks true/false cases
"""

from __future__ import annotations

from typing import Any

from app.services.slide_splitter import has_slide_breaks, split_at_slide_breaks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _para(text: str) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}],
    }


def _slide_break() -> dict[str, Any]:
    return {"type": "slideBreak"}


def _doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


# ─── split_at_slide_breaks ───────────────────────────────────────────


class TestSplitAtSlideBreaks:
    def test_no_breaks_single_segment(self) -> None:
        doc = _doc(_para("Hello"), _para("World"))
        result = split_at_slide_breaks(doc)
        assert len(result) == 1
        assert result[0]["type"] == "doc"
        assert len(result[0]["content"]) == 2

    def test_one_break_two_segments(self) -> None:
        doc = _doc(_para("Slide 1"), _slide_break(), _para("Slide 2"))
        result = split_at_slide_breaks(doc)
        assert len(result) == 2
        assert result[0]["content"][0]["content"][0]["text"] == "Slide 1"
        assert result[1]["content"][0]["content"][0]["text"] == "Slide 2"

    def test_multiple_breaks(self) -> None:
        doc = _doc(
            _para("A"),
            _slide_break(),
            _para("B"),
            _slide_break(),
            _para("C"),
            _slide_break(),
            _para("D"),
        )
        result = split_at_slide_breaks(doc)
        assert len(result) == 4

    def test_leading_break_filtered(self) -> None:
        doc = _doc(_slide_break(), _para("Content"))
        result = split_at_slide_breaks(doc)
        assert len(result) == 1
        assert result[0]["content"][0]["content"][0]["text"] == "Content"

    def test_trailing_break_no_empty_segment(self) -> None:
        doc = _doc(_para("Content"), _slide_break())
        result = split_at_slide_breaks(doc)
        assert len(result) == 1

    def test_empty_content(self) -> None:
        doc: dict[str, Any] = {"type": "doc", "content": []}
        result = split_at_slide_breaks(doc)
        assert len(result) == 0

    def test_no_content_key(self) -> None:
        doc: dict[str, Any] = {"type": "doc"}
        result = split_at_slide_breaks(doc)
        assert len(result) == 1
        assert result[0]["content"] == []

    def test_segments_are_valid_docs(self) -> None:
        doc = _doc(_para("A"), _slide_break(), _para("B"))
        result = split_at_slide_breaks(doc)
        for seg in result:
            assert seg["type"] == "doc"
            assert isinstance(seg["content"], list)
            assert len(seg["content"]) > 0


# ─── has_slide_breaks ────────────────────────────────────────────────


class TestHasSlideBreaks:
    def test_true_when_present(self) -> None:
        doc = _doc(_para("A"), _slide_break(), _para("B"))
        assert has_slide_breaks(doc) is True

    def test_false_when_absent(self) -> None:
        doc = _doc(_para("A"), _para("B"))
        assert has_slide_breaks(doc) is False

    def test_false_for_none(self) -> None:
        assert has_slide_breaks(None) is False

    def test_false_for_empty(self) -> None:
        assert has_slide_breaks({}) is False

    def test_false_for_no_content(self) -> None:
        assert has_slide_breaks({"type": "doc"}) is False
