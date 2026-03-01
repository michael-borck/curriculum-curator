"""
H5P Branching Scenario package builder.

Generates .h5p (ZIP) archives containing a Branching Scenario from
branching card data extracted from TipTap content_json.

The package contains only content.json + h5p.json — the H5P player JS/CSS
is managed by the LMS (Moodle, WordPress, etc.).
"""

import json
import uuid
import zipfile
from io import BytesIO
from typing import Any

# H5P library version dicts
_BRANCHING_SCENARIO_LIB: dict[str, Any] = {
    "machineName": "H5P.BranchingScenario",
    "majorVersion": 1,
    "minorVersion": 8,
}
_ADVANCED_TEXT_LIB: dict[str, Any] = {
    "machineName": "H5P.AdvancedText",
    "majorVersion": 1,
    "minorVersion": 1,
}
_BRANCHING_QUESTION_LIB: dict[str, Any] = {
    "machineName": "H5P.BranchingQuestion",
    "majorVersion": 1,
    "minorVersion": 0,
}


class H5PBranchingScenarioBuilder:
    """Builds an H5P Branching Scenario package (.h5p ZIP) from branching cards."""

    def build(self, cards: list[dict[str, Any]], title: str) -> BytesIO:
        """Create .h5p ZIP with content.json + h5p.json.

        Args:
            cards: List of branching card attribute dicts (from extract_branching_cards).
            title: Title for the branching scenario.

        Returns:
            BytesIO containing the .h5p ZIP archive.
        """
        # Separate cards into content (non-ending) and ending
        content_cards = [c for c in cards if c.get("cardType") != "ending"]
        ending_cards = [c for c in cards if c.get("cardType") == "ending"]

        # Build cardId → content array index map
        card_index: dict[str, int] = {}
        for i, card in enumerate(content_cards):
            card_index[str(card.get("cardId", ""))] = i

        # Build content nodes
        content_nodes: list[dict[str, Any]] = []
        for i, card in enumerate(content_cards):
            card_type = str(card.get("cardType", "content"))
            if card_type == "branch":
                node = self._build_branching_question(card, card_index)
            else:
                node = self._build_advanced_text(card, i, content_cards, card_index)
            content_nodes.append(node)

        # Build end screens
        end_screens = self._build_end_screens(ending_cards)

        content_json = self._build_content_json(title, content_nodes, end_screens)
        h5p_json = self._build_h5p_json(title)

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("h5p.json", json.dumps(h5p_json, indent=2))
            zf.writestr("content/content.json", json.dumps(content_json, indent=2))
        buf.seek(0)
        return buf

    def _build_advanced_text(
        self,
        card: dict[str, Any],
        index: int,
        content_cards: list[dict[str, Any]],
        card_index: dict[str, int],
    ) -> dict[str, Any]:
        """Build an H5P.AdvancedText content node for a content card."""
        card_title = str(card.get("cardTitle", ""))
        card_content = str(card.get("cardContent", ""))
        text = f"<h2>{card_title}</h2><p>{card_content}</p>" if card_title else f"<p>{card_content}</p>"

        # Determine nextContentId: sequential to next card, or -1 if last
        next_id = index + 1 if index < len(content_cards) - 1 else -1

        return {
            "type": {
                "library": "H5P.AdvancedText 1.1",
                "params": {"text": text},
                "subContentId": str(uuid.uuid4()),
                "metadata": {"contentType": "Text", "title": card_title or "Content"},
            },
            "showContentTitle": bool(card_title),
            "contentTitle": card_title,
            "nextContentId": next_id,
            "proceedButtonText": "Continue",
        }

    def _build_branching_question(
        self,
        card: dict[str, Any],
        card_index: dict[str, int],
    ) -> dict[str, Any]:
        """Build an H5P.BranchingQuestion content node for a branch card."""
        card_title = str(card.get("cardTitle", ""))
        card_content = str(card.get("cardContent", ""))
        question_text = f"<h2>{card_title}</h2><p>{card_content}</p>" if card_title else f"<p>{card_content}</p>"

        choices: list[dict[str, Any]] = card.get("choices", [])
        alternatives: list[dict[str, Any]] = []
        for choice in choices:
            target_card_id = str(choice.get("targetCardId", ""))
            next_content_id = card_index.get(target_card_id, -1)
            alternatives.append({
                "text": str(choice.get("text", "")),
                "nextContentId": next_content_id,
            })

        return {
            "type": {
                "library": "H5P.BranchingQuestion 1.0",
                "params": {
                    "branchingQuestion": {
                        "question": question_text,
                        "alternatives": alternatives,
                    },
                },
                "subContentId": str(uuid.uuid4()),
                "metadata": {"contentType": "Branching Question", "title": card_title or "Decision"},
            },
            "showContentTitle": bool(card_title),
            "contentTitle": card_title,
            "nextContentId": -1,
        }

    def _build_end_screens(
        self,
        ending_cards: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build endScreens from ending cards."""
        if not ending_cards:
            return [
                {
                    "endScreenTitle": "Scenario Complete",
                    "endScreenSubtitle": "",
                    "contentId": -1,
                    "endScreenScore": 0,
                },
            ]

        return [
            {
                "endScreenTitle": str(card.get("cardTitle", "End")),
                "endScreenSubtitle": str(card.get("endMessage", "")),
                "contentId": -1,
                "endScreenScore": int(card.get("endScore", 0)),
            }
            for card in ending_cards
        ]

    def _build_content_json(
        self,
        title: str,
        content: list[dict[str, Any]],
        end_screens: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build the content/content.json structure."""
        return {
            "branchingScenario": {
                "title": f"<p>{title}</p>",
                "startScreen": {
                    "startScreenTitle": title,
                    "startScreenSubtitle": "",
                },
                "content": content,
                "endScreens": end_screens,
                "scoringOptionGroup": {
                    "scoringOption": "static-end-score",
                },
                "l10n": {
                    "startScreenButtonText": "Start",
                    "endScreenButtonText": "Restart",
                    "proceedButtonText": "Continue",
                    "scoreText": "Your score:",
                },
            },
        }

    def _build_h5p_json(self, title: str) -> dict[str, Any]:
        """Build the h5p.json manifest."""
        return {
            "title": title,
            "mainLibrary": "H5P.BranchingScenario",
            "language": "en",
            "embedTypes": ["div", "iframe"],
            "preloadedDependencies": [
                _BRANCHING_SCENARIO_LIB,
                _ADVANCED_TEXT_LIB,
                _BRANCHING_QUESTION_LIB,
            ],
        }


# Module-level singleton
h5p_branching_builder = H5PBranchingScenarioBuilder()
