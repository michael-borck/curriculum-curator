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


def _notes(text: str) -> dict[str, Any]:
    return {
        "type": "speakerNotes",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


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


# ─── speaker notes attachment ────────────────────────────────────────


class TestSpeakerNotesAttachment:
    """Speaker notes must travel with the slide they describe.

    The author can place the notes node either before or after the
    slideBreak that closes a slide. The splitter normalises this by
    moving any leading speakerNotes nodes back to the previous segment.
    """

    def test_notes_before_break_stay_with_slide(self) -> None:
        # Canonical placement: notes before the slide break
        doc = _doc(
            _para("Slide 1"),
            _notes("Speaker prompt for slide 1"),
            _slide_break(),
            _para("Slide 2"),
        )
        result = split_at_slide_breaks(doc)
        assert len(result) == 2
        # Slide 1 segment contains both the paragraph and the notes
        seg1_types = [n["type"] for n in result[0]["content"]]
        assert seg1_types == ["paragraph", "speakerNotes"]
        # Slide 2 has only its paragraph
        assert [n["type"] for n in result[1]["content"]] == ["paragraph"]

    def test_notes_after_break_reattach_to_previous(self) -> None:
        # Defensive placement: notes immediately after the slide break
        # (where the editor cursor naturally lands when a break is inserted)
        doc = _doc(
            _para("Slide 1"),
            _slide_break(),
            _notes("Speaker prompt for slide 1"),
            _para("Slide 2"),
        )
        result = split_at_slide_breaks(doc)
        assert len(result) == 2
        # Notes should have been moved to the slide 1 segment
        seg1_types = [n["type"] for n in result[0]["content"]]
        assert seg1_types == ["paragraph", "speakerNotes"]
        # Slide 2 segment has only its paragraph (notes lifted out)
        assert [n["type"] for n in result[1]["content"]] == ["paragraph"]

    def test_multiple_notes_after_break_all_reattach(self) -> None:
        # Multiple consecutive notes blocks (unusual but possible) should
        # all migrate to the previous segment in order
        doc = _doc(
            _para("Slide 1"),
            _slide_break(),
            _notes("First note"),
            _notes("Second note"),
            _para("Slide 2"),
        )
        result = split_at_slide_breaks(doc)
        assert len(result) == 2
        seg1_types = [n["type"] for n in result[0]["content"]]
        assert seg1_types == ["paragraph", "speakerNotes", "speakerNotes"]
        # Order preserved
        assert (
            result[0]["content"][1]["content"][0]["content"][0]["text"]
            == "First note"
        )
        assert (
            result[0]["content"][2]["content"][0]["content"][0]["text"]
            == "Second note"
        )

    def test_notes_after_leading_break_become_first_slide(self) -> None:
        # If the document opens with a slideBreak followed by notes, the
        # leading empty segment is filtered out and the notes have nowhere
        # to migrate — they stay with the first real segment
        doc = _doc(
            _slide_break(),
            _notes("Notes for slide 1"),
            _para("Slide 1 body"),
        )
        result = split_at_slide_breaks(doc)
        assert len(result) == 1
        types = [n["type"] for n in result[0]["content"]]
        assert types == ["speakerNotes", "paragraph"]

    def test_notes_at_end_of_last_slide(self) -> None:
        # Notes after the last slide's content (no trailing break) stay put
        doc = _doc(
            _para("Slide 1"),
            _slide_break(),
            _para("Slide 2"),
            _notes("Notes for slide 2"),
        )
        result = split_at_slide_breaks(doc)
        assert len(result) == 2
        assert [n["type"] for n in result[1]["content"]] == [
            "paragraph",
            "speakerNotes",
        ]

    def test_notes_only_segment_does_not_create_phantom_slide(self) -> None:
        # If a segment between two breaks contains only notes (which then
        # migrate back), the now-empty segment should be filtered out
        doc = _doc(
            _para("Slide 1"),
            _slide_break(),
            _notes("Notes for slide 1"),
            _slide_break(),
            _para("Slide 2"),
        )
        result = split_at_slide_breaks(doc)
        # Two slides, not three
        assert len(result) == 2
        assert [n["type"] for n in result[0]["content"]] == [
            "paragraph",
            "speakerNotes",
        ]
        assert [n["type"] for n in result[1]["content"]] == ["paragraph"]


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
