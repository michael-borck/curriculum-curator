"""Tests for H5P Branching Scenario builder."""

import json
import zipfile
from typing import Any

import pytest

from app.services.h5p_branching_service import h5p_branching_builder


def _make_card(
    card_id: str = "card-1",
    card_type: str = "content",
    title: str = "Test Card",
    content: str = "Some content",
    choices: list[dict[str, Any]] | None = None,
    end_score: int = 0,
    end_message: str = "",
) -> dict[str, Any]:
    return {
        "cardId": card_id,
        "cardType": card_type,
        "cardTitle": title,
        "cardContent": content,
        "choices": choices or [],
        "endScore": end_score,
        "endMessage": end_message,
    }


def _build_and_parse(cards: list[dict[str, Any]], title: str = "Test Scenario") -> tuple[dict[str, Any], dict[str, Any]]:
    """Build H5P package and return (h5p_json, content_json)."""
    buf = h5p_branching_builder.build(cards, title)
    with zipfile.ZipFile(buf) as zf:
        h5p_json = json.loads(zf.read("h5p.json"))
        content_json = json.loads(zf.read("content/content.json"))
    return h5p_json, content_json


class TestPackageStructure:
    """Test that the generated ZIP has the expected structure."""

    def test_zip_contains_required_files(self) -> None:
        cards = [_make_card()]
        buf = h5p_branching_builder.build(cards, "Test")
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert "h5p.json" in names
            assert "content/content.json" in names

    def test_main_library_is_branching_scenario(self) -> None:
        cards = [_make_card()]
        h5p_json, _ = _build_and_parse(cards)
        assert h5p_json["mainLibrary"] == "H5P.BranchingScenario"

    def test_dependencies_include_all_libraries(self) -> None:
        cards = [_make_card()]
        h5p_json, _ = _build_and_parse(cards)
        dep_names = [d["machineName"] for d in h5p_json["preloadedDependencies"]]
        assert "H5P.BranchingScenario" in dep_names
        assert "H5P.AdvancedText" in dep_names
        assert "H5P.BranchingQuestion" in dep_names


class TestContentNodes:
    """Test content node generation."""

    def test_content_card_produces_advanced_text(self) -> None:
        cards = [_make_card(card_type="content", title="Intro")]
        _, content_json = _build_and_parse(cards)
        nodes = content_json["branchingScenario"]["content"]
        assert len(nodes) == 1
        assert nodes[0]["type"]["library"] == "H5P.AdvancedText 1.1"

    def test_branch_card_produces_branching_question(self) -> None:
        cards = [
            _make_card(
                card_id="branch-1",
                card_type="branch",
                title="Decision",
                choices=[
                    {"id": "c1", "text": "Option A", "targetCardId": "card-2", "feedback": ""},
                    {"id": "c2", "text": "Option B", "targetCardId": "card-3", "feedback": ""},
                ],
            ),
            _make_card(card_id="card-2", title="Path A"),
            _make_card(card_id="card-3", title="Path B"),
        ]
        _, content_json = _build_and_parse(cards)
        nodes = content_json["branchingScenario"]["content"]
        assert nodes[0]["type"]["library"] == "H5P.BranchingQuestion 1.0"

    def test_branch_alternatives_have_correct_targets(self) -> None:
        cards = [
            _make_card(
                card_id="branch-1",
                card_type="branch",
                choices=[
                    {"id": "c1", "text": "A", "targetCardId": "card-a", "feedback": ""},
                    {"id": "c2", "text": "B", "targetCardId": "card-b", "feedback": ""},
                ],
            ),
            _make_card(card_id="card-a", title="Card A"),
            _make_card(card_id="card-b", title="Card B"),
        ]
        _, content_json = _build_and_parse(cards)
        node = content_json["branchingScenario"]["content"][0]
        alts = node["type"]["params"]["branchingQuestion"]["alternatives"]
        assert alts[0]["nextContentId"] == 1  # card-a is at index 1
        assert alts[1]["nextContentId"] == 2  # card-b is at index 2


class TestNextContentId:
    """Test sequential chaining via nextContentId."""

    def test_sequential_chaining(self) -> None:
        cards = [
            _make_card(card_id="c1", title="First"),
            _make_card(card_id="c2", title="Second"),
            _make_card(card_id="c3", title="Third"),
        ]
        _, content_json = _build_and_parse(cards)
        nodes = content_json["branchingScenario"]["content"]
        assert nodes[0]["nextContentId"] == 1
        assert nodes[1]["nextContentId"] == 2
        assert nodes[2]["nextContentId"] == -1  # last card

    def test_single_card_points_to_end(self) -> None:
        cards = [_make_card()]
        _, content_json = _build_and_parse(cards)
        nodes = content_json["branchingScenario"]["content"]
        assert len(nodes) == 1
        assert nodes[0]["nextContentId"] == -1


class TestEndScreens:
    """Test end screen generation."""

    def test_ending_cards_create_end_screens(self) -> None:
        cards = [
            _make_card(card_id="c1", title="Content"),
            _make_card(
                card_id="end-1",
                card_type="ending",
                title="Good End",
                end_score=100,
                end_message="Well done!",
            ),
        ]
        _, content_json = _build_and_parse(cards)
        end_screens = content_json["branchingScenario"]["endScreens"]
        assert len(end_screens) == 1
        assert end_screens[0]["endScreenTitle"] == "Good End"
        assert end_screens[0]["endScreenScore"] == 100
        assert end_screens[0]["endScreenSubtitle"] == "Well done!"

    def test_no_ending_cards_creates_default(self) -> None:
        cards = [_make_card(card_id="c1")]
        _, content_json = _build_and_parse(cards)
        end_screens = content_json["branchingScenario"]["endScreens"]
        assert len(end_screens) == 1
        assert end_screens[0]["endScreenTitle"] == "Scenario Complete"

    def test_ending_cards_excluded_from_content(self) -> None:
        cards = [
            _make_card(card_id="c1"),
            _make_card(card_id="end-1", card_type="ending", title="End"),
        ]
        _, content_json = _build_and_parse(cards)
        nodes = content_json["branchingScenario"]["content"]
        # Only the content card should be in content nodes
        assert len(nodes) == 1

    def test_multiple_endings(self) -> None:
        cards = [
            _make_card(card_id="c1"),
            _make_card(card_id="end-1", card_type="ending", title="Good", end_score=100),
            _make_card(card_id="end-2", card_type="ending", title="Bad", end_score=20),
        ]
        _, content_json = _build_and_parse(cards)
        end_screens = content_json["branchingScenario"]["endScreens"]
        assert len(end_screens) == 2


class TestEdgeCases:
    """Test edge cases."""

    def test_circular_reference_produces_valid_indices(self) -> None:
        """Circular references should resolve to valid content indices."""
        cards = [
            _make_card(
                card_id="c1",
                card_type="branch",
                choices=[
                    {"id": "c", "text": "Loop", "targetCardId": "c2", "feedback": ""},
                ],
            ),
            _make_card(
                card_id="c2",
                card_type="branch",
                choices=[
                    {"id": "c", "text": "Back", "targetCardId": "c1", "feedback": ""},
                ],
            ),
        ]
        _, content_json = _build_and_parse(cards)
        nodes = content_json["branchingScenario"]["content"]
        # c1 → c2 (index 1), c2 → c1 (index 0)
        alts_0 = nodes[0]["type"]["params"]["branchingQuestion"]["alternatives"]
        alts_1 = nodes[1]["type"]["params"]["branchingQuestion"]["alternatives"]
        assert alts_0[0]["nextContentId"] == 1
        assert alts_1[0]["nextContentId"] == 0

    def test_all_ending_cards_produces_empty_content(self) -> None:
        cards = [
            _make_card(card_id="end-1", card_type="ending", title="End A"),
            _make_card(card_id="end-2", card_type="ending", title="End B"),
        ]
        _, content_json = _build_and_parse(cards)
        assert content_json["branchingScenario"]["content"] == []
        assert len(content_json["branchingScenario"]["endScreens"]) == 2

    def test_unknown_target_resolves_to_minus_one(self) -> None:
        """A choice targeting a non-existent card should get nextContentId -1."""
        cards = [
            _make_card(
                card_id="c1",
                card_type="branch",
                choices=[
                    {"id": "c", "text": "Go", "targetCardId": "nonexistent", "feedback": ""},
                ],
            ),
        ]
        _, content_json = _build_and_parse(cards)
        node = content_json["branchingScenario"]["content"][0]
        alts = node["type"]["params"]["branchingQuestion"]["alternatives"]
        assert alts[0]["nextContentId"] == -1

    def test_title_propagated(self) -> None:
        cards = [_make_card()]
        h5p_json, content_json = _build_and_parse(cards, "My Scenario")
        assert h5p_json["title"] == "My Scenario"
        assert content_json["branchingScenario"]["startScreen"]["startScreenTitle"] == "My Scenario"
