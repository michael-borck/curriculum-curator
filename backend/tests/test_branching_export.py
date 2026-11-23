"""Branching story health and export."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.branching_export_service import (
    build_ink_source,
    build_playable_html,
    extract_cards,
    story_health,
)


def _material() -> SimpleNamespace:
    content = {
        "type": "doc",
        "content": [
            {
                "type": "branchingCard",
                "attrs": {
                    "cardId": "c1",
                    "cardType": "content",
                    "cardTitle": "Start",
                    "cardContent": "A tricky situation.",
                    "choices": [
                        {"id": "a", "text": "Act", "targetCardId": "c2", "feedback": "ok"},
                        {"id": "b", "text": "Wait", "targetCardId": "missing", "feedback": ""},
                    ],
                    "endScore": 0,
                    "endMessage": "",
                },
            },
            {
                "type": "branchingCard",
                "attrs": {
                    "cardId": "c2",
                    "cardType": "ending",
                    "cardTitle": "Done",
                    "cardContent": "You acted.",
                    "choices": [],
                    "endScore": 2,
                    "endMessage": "Good choice.",
                },
            },
        ],
    }
    return SimpleNamespace(title="Case", content_json=content)


def test_story_health_flags_broken_targets() -> None:
    cards = extract_cards(_material().content_json)
    health = story_health(cards)
    assert health["cards"] == 2
    assert health["endings"] == 1
    assert health["broken_targets"]
    assert not health["ok"]


def test_exports_contain_choices() -> None:
    material = _material()
    html = build_playable_html(material)
    ink = build_ink_source(material)
    assert "tricky situation" in html
    assert "Act" in html
    assert "-> c1" in ink
    assert "+ [Act] -> c2" in ink
    assert "-> END" in ink
