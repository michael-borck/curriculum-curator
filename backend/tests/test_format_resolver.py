"""Tests for the format resolver service — content detection + target resolution."""

from app.services.format_resolver import (
    AUTO_DEFAULTS,
    CONTENT_TYPE_BRANCHING,
    CONTENT_TYPE_QUIZ,
    CONTENT_TYPE_RICH_TEXT,
    CONTENT_TYPE_SLIDES,
    detect_content_types,
    resolve_targets_for_material,
)


# ─── Content detection ────────────────────────────────────────────────


class TestDetectContentTypes:
    def test_empty_content_json(self) -> None:
        assert detect_content_types(None) == [CONTENT_TYPE_RICH_TEXT]
        assert detect_content_types({}) == [CONTENT_TYPE_RICH_TEXT]

    def test_plain_text(self) -> None:
        doc = {"type": "doc", "content": [{"type": "paragraph"}]}
        assert detect_content_types(doc) == [CONTENT_TYPE_RICH_TEXT]

    def test_quiz_nodes(self) -> None:
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "quizQuestion",
                    "attrs": {
                        "questionText": "What?",
                        "questionType": "multiple_choice",
                        "options": [
                            {"text": "A", "correct": True},
                            {"text": "B", "correct": False},
                        ],
                    },
                }
            ],
        }
        assert CONTENT_TYPE_QUIZ in detect_content_types(doc)

    def test_slide_breaks(self) -> None:
        doc = {
            "type": "doc",
            "content": [
                {"type": "paragraph"},
                {"type": "slideBreak"},
                {"type": "paragraph"},
            ],
        }
        assert CONTENT_TYPE_SLIDES in detect_content_types(doc)

    def test_branching_cards(self) -> None:
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "branchingCard",
                    "attrs": {
                        "title": "Branch 1",
                        "scenario": "Scenario A",
                        "choices": [],
                    },
                }
            ],
        }
        assert CONTENT_TYPE_BRANCHING in detect_content_types(doc)

    def test_mixed_content(self) -> None:
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "quizQuestion",
                    "attrs": {
                        "questionText": "Q",
                        "questionType": "multiple_choice",
                        "options": [{"text": "A", "correct": True}],
                    },
                },
                {"type": "slideBreak"},
                {"type": "paragraph"},
            ],
        }
        types = detect_content_types(doc)
        assert CONTENT_TYPE_QUIZ in types
        assert CONTENT_TYPE_SLIDES in types


# ─── Target resolution ────────────────────────────────────────────────


class TestResolveTargets:
    def test_auto_defaults(self) -> None:
        result = resolve_targets_for_material([CONTENT_TYPE_QUIZ], [])
        assert result == {"quiz": ["qti"]}

    def test_auto_defaults_slides(self) -> None:
        result = resolve_targets_for_material([CONTENT_TYPE_SLIDES], [])
        assert result == {"slides": ["h5p_course_presentation"]}

    def test_auto_defaults_rich_text(self) -> None:
        result = resolve_targets_for_material([CONTENT_TYPE_RICH_TEXT], [])
        assert result == {"rich_text": ["html"]}

    def test_user_defaults_override(self) -> None:
        result = resolve_targets_for_material(
            [CONTENT_TYPE_QUIZ],
            [],
            user_defaults={"quiz": ["h5p_question_set"]},
        )
        assert result == {"quiz": ["h5p_question_set"]}

    def test_user_defaults_invalid_filtered(self) -> None:
        """Unknown targets in user defaults are filtered out."""
        result = resolve_targets_for_material(
            [CONTENT_TYPE_QUIZ],
            [],
            user_defaults={"quiz": ["unknown_target", "qti"]},
        )
        assert result == {"quiz": ["qti"]}

    def test_user_defaults_all_invalid_falls_back(self) -> None:
        """If all user defaults are invalid, auto defaults are kept."""
        result = resolve_targets_for_material(
            [CONTENT_TYPE_QUIZ],
            [],
            user_defaults={"quiz": ["unknown"]},
        )
        assert result == {"quiz": AUTO_DEFAULTS[CONTENT_TYPE_QUIZ]}

    def test_material_override(self) -> None:
        result = resolve_targets_for_material(
            [CONTENT_TYPE_QUIZ],
            ["h5p_question_set"],
            user_defaults={"quiz": ["qti"]},
        )
        assert result == {"quiz": ["h5p_question_set"]}

    def test_material_override_invalid_filtered(self) -> None:
        """Unknown targets in material overrides are filtered."""
        result = resolve_targets_for_material(
            [CONTENT_TYPE_QUIZ],
            ["bogus"],
        )
        # Falls back to auto defaults since material override was all invalid
        assert result == {"quiz": ["qti"]}

    def test_multiple_content_types(self) -> None:
        result = resolve_targets_for_material(
            [CONTENT_TYPE_QUIZ, CONTENT_TYPE_SLIDES],
            [],
        )
        assert result == {
            "quiz": ["qti"],
            "slides": ["h5p_course_presentation"],
        }

    def test_branching_defaults(self) -> None:
        result = resolve_targets_for_material([CONTENT_TYPE_BRANCHING], [])
        assert result == {"branching": ["h5p_branching"]}
