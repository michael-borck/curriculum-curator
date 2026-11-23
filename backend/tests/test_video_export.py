"""Local narrated-video export helpers."""

from __future__ import annotations

import pytest

from app.services.video_export_service import (
    VideoExportUnavailableError,
    _notes_text,
    _slide_text,
    _title_for,
    build_video,
    capabilities,
)


def test_slide_text_and_notes_are_separated() -> None:
    segment = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Title"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Visible body"}],
            },
            {
                "type": "speakerNotes",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Say this"}],
                    }
                ],
            },
        ],
    }
    assert _title_for(segment, 0, "Deck") == "Title"
    assert "Visible body" in _slide_text(segment)
    assert "Say this" not in _slide_text(segment)
    assert _notes_text(segment) == "Say this"


def test_no_segments_is_unavailable() -> None:
    with pytest.raises(VideoExportUnavailableError):
        build_video("Empty", {}, "/tmp/never.mp4")


def test_capabilities_shape() -> None:
    result = capabilities()
    assert "available" in result
    assert isinstance(result["available"], bool)
