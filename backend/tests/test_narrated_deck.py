"""Narrated HTML deck builder."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.narrated_deck_service import build_narrated_deck


def test_narrated_deck_uses_speaker_notes_and_splits_slides() -> None:
    content = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "First"}],
            },
            {"type": "paragraph", "content": [{"type": "text", "text": "Visible"}]},
            {
                "type": "speakerNotes",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Say this aloud."}],
                    }
                ],
            },
            {"type": "slideBreak"},
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Second"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Also visible"}],
            },
        ],
    }
    material = SimpleNamespace(title="Demo", content_json=content)
    html = build_narrated_deck(material)

    assert "Demo" in html
    assert "First" in html
    assert "Second" in html
    assert "Say this aloud." in html
    assert "speechSynthesis" in html
    # Notes must not leak into the visible slide body.
    slide_part = html.split("const DECK =", 1)[1]
    assert '"html": "<h1>First<\\/h1><p>Visible<\\/p>"' in slide_part
