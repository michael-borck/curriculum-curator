"""Tests for the standalone interactive HTML export (story 19B.1)."""

import json
import re
from typing import Any

import pytest

from app.services.interactive_html_service import interactive_html_builder


def _card(
    card_id: str,
    *,
    card_type: str = "content",
    title: str = "",
    content: str = "",
    choices: list[dict[str, Any]] | None = None,
    end_message: str = "",
    end_score: int = 0,
) -> dict[str, Any]:
    return {
        "cardId": card_id,
        "cardType": card_type,
        "cardTitle": title,
        "cardContent": content,
        "choices": choices or [],
        "endMessage": end_message,
        "endScore": end_score,
    }


def _extract_scenario(html: str) -> dict[str, Any]:
    """Pull the embedded SCENARIO JSON back out of the page."""
    match = re.search(r"const SCENARIO = (\{.*?\});", html, re.DOTALL)
    assert match, "SCENARIO literal not found"
    # Reverse the </ → <\/ escaping applied at embed time
    return json.loads(match.group(1).replace("<\\/", "</"))


SCENARIO = [
    _card(
        "start",
        title="Start",
        content="You arrive at a fork.",
        choices=[
            {"id": "c1", "text": "Go left", "targetCardId": "left", "feedback": ""},
            {
                "id": "c2",
                "text": "Go right",
                "targetCardId": "end",
                "feedback": "Bold choice.",
            },
        ],
    ),
    _card(
        "left",
        title="Left path",
        content="A dead end.",
        choices=[
            {"id": "c3", "text": "Back", "targetCardId": "end", "feedback": ""}
        ],
    ),
    _card("end", card_type="ending", end_message="You made it.", end_score=10),
]


class TestInteractiveHtml:
    def test_single_self_contained_document(self) -> None:
        html = interactive_html_builder.build(SCENARIO, "Adventure")
        assert html.startswith("<!DOCTYPE html>")
        # No external dependencies
        assert "http://" not in html and "https://" not in html
        assert "<script" in html and "<style" in html

    def test_scenario_graph_embedded(self) -> None:
        html = interactive_html_builder.build(SCENARIO, "Adventure")
        scenario = _extract_scenario(html)
        assert scenario["startCardId"] == "start"
        assert set(scenario["cards"]) == {"start", "left", "end"}
        # A choice may target an ending card (choice → ending)
        targets = [c["target"] for c in scenario["cards"]["start"]["choices"]]
        assert "end" in targets
        # Convergence: both 'right' and 'left→back' reach 'end'
        assert scenario["cards"]["left"]["choices"][0]["target"] == "end"
        assert scenario["cards"]["end"]["type"] == "ending"
        assert scenario["cards"]["end"]["endMessage"] == "You made it."

    def test_script_close_is_escaped(self) -> None:
        # Author content containing </script> must not break out of the tag
        cards = [_card("a", content="evil </script> text")]
        html = interactive_html_builder.build(cards, "T")
        assert "</script> text" not in html  # raw sequence neutralised
        assert "<\\/script>" in html
        # Still recoverable as data
        scenario = _extract_scenario(html)
        assert scenario["cards"]["a"]["content"] == "evil </script> text"

    def test_title_html_escaped(self) -> None:
        html = interactive_html_builder.build([_card("a")], "<b>Hi</b>")
        assert "&lt;b&gt;Hi&lt;/b&gt;" in html

    def test_empty_cards_still_builds(self) -> None:
        html = interactive_html_builder.build([], "Empty")
        scenario = _extract_scenario(html)
        assert scenario["cards"] == {}
        assert scenario["startCardId"] == ""
