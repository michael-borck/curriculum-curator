"""
Tests for H5P Interactive Video builder and related extractors.

Covers:
- extract_video_embed / extract_video_interactions from unit_export_data
- H5P Interactive Video builder (YouTube, Vimeo, Echo360 rejection)
- Interaction ordering by time
- Format resolver detection of interactive_video content type
"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from typing import Any

import pytest

from app.services.format_resolver import (
    CONTENT_TYPE_INTERACTIVE_VIDEO,
    TARGETS_FOR_CONTENT_TYPE,
    detect_content_types,
)
from app.services.h5p_interactive_video_service import (
    H5PInteractiveVideoBuilder,
    h5p_interactive_video_builder,
)
from app.services.unit_export_data import (
    extract_video_embed,
    extract_video_interactions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _video_embed(
    url: str = "https://youtube.com/watch?v=abc",
    platform: str = "youtube",
    title: str = "My Video",
) -> dict[str, Any]:
    return {
        "type": "interactiveVideoEmbed",
        "attrs": {"url": url, "platform": platform, "title": title},
    }


def _video_interaction(
    *,
    time: float = 10.0,
    question_text: str = "What is 2+2?",
    question_type: str = "multiple_choice",
    pause: bool = True,
    options: list[dict[str, Any]] | None = None,
    interaction_id: str = "q1",
) -> dict[str, Any]:
    if options is None:
        options = [
            {"text": "3", "correct": False},
            {"text": "4", "correct": True},
            {"text": "5", "correct": False},
        ]
    return {
        "type": "videoInteraction",
        "attrs": {
            "interactionId": interaction_id,
            "time": time,
            "pause": pause,
            "questionType": question_type,
            "questionText": question_text,
            "options": options,
            "feedback": "Good job!",
            "points": 1.0,
        },
    }


def _doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


def _unpack_h5p(buf: BytesIO) -> tuple[dict[str, Any], dict[str, Any]]:
    """Unpack h5p.json and content/content.json from a .h5p ZIP."""
    buf.seek(0)
    with zipfile.ZipFile(buf, "r") as zf:
        h5p_json = json.loads(zf.read("h5p.json"))
        content_json = json.loads(zf.read("content/content.json"))
    return h5p_json, content_json


class TestExtractVideoEmbed:
    def test_extract_video_embed(self) -> None:
        doc = _doc(
            _video_embed(
                url="https://youtube.com/watch?v=abc",
                platform="youtube",
                title="Lecture",
            )
        )
        result = extract_video_embed(doc)
        assert result is not None
        assert result["url"] == "https://youtube.com/watch?v=abc"
        assert result["platform"] == "youtube"
        assert result["title"] == "Lecture"

    def test_extract_video_embed_missing(self) -> None:
        doc = _doc(
            {"type": "paragraph", "content": [{"type": "text", "text": "hello"}]}
        )
        result = extract_video_embed(doc)
        assert result is None

    def test_extract_video_embed_empty_doc(self) -> None:
        result = extract_video_embed({"type": "doc"})
        assert result is None


class TestExtractVideoInteractions:
    def test_extract_video_interactions(self) -> None:
        doc = _doc(
            _video_embed(),
            _video_interaction(time=10.0, question_text="Q1"),
        )
        result = extract_video_interactions(doc)
        assert len(result) == 1
        assert result[0]["questionText"] == "Q1"
        assert result[0]["time"] == 10.0

    def test_extract_video_interactions_empty(self) -> None:
        doc = _doc(_video_embed())
        result = extract_video_interactions(doc)
        assert result == []

    def test_extract_video_interactions_sorted_by_time(self) -> None:
        doc = _doc(
            _video_embed(),
            _video_interaction(time=30.0, question_text="Q3", interaction_id="q3"),
            _video_interaction(time=10.0, question_text="Q1", interaction_id="q1"),
            _video_interaction(time=20.0, question_text="Q2", interaction_id="q2"),
        )
        result = extract_video_interactions(doc)
        assert len(result) == 3
        assert [r["questionText"] for r in result] == ["Q1", "Q2", "Q3"]


class TestBuildYouTube:
    def test_build_youtube(self) -> None:
        embed = {
            "url": "https://youtube.com/watch?v=abc",
            "platform": "youtube",
            "title": "Lecture",
        }
        interactions = [
            {
                "interactionId": "q1",
                "time": 10.0,
                "pause": True,
                "questionType": "multiple_choice",
                "questionText": "What is 2+2?",
                "options": [
                    {"text": "3", "correct": False},
                    {"text": "4", "correct": True},
                ],
                "feedback": "Good!",
                "points": 1.0,
            },
        ]

        buf = h5p_interactive_video_builder.build(embed, interactions, "Test Video")
        h5p_json, content_json = _unpack_h5p(buf)

        # h5p.json
        assert h5p_json["mainLibrary"] == "H5P.InteractiveVideo"
        assert h5p_json["title"] == "Test Video"

        # content.json structure
        iv = content_json["interactiveVideo"]
        assert iv["video"]["files"][0]["mime"] == "video/YouTube"
        assert iv["video"]["files"][0]["path"] == "https://youtube.com/watch?v=abc"

        # Interactions
        interactions_out = iv["assets"]["interactions"]
        assert len(interactions_out) == 1
        assert interactions_out[0]["duration"]["from"] == 10.0
        assert interactions_out[0]["pause"] is True

    def test_zip_contains_required_files(self) -> None:
        embed = {
            "url": "https://youtube.com/watch?v=abc",
            "platform": "youtube",
            "title": "Test",
        }
        interactions = [
            {
                "interactionId": "q1",
                "time": 5.0,
                "pause": True,
                "questionType": "multiple_choice",
                "questionText": "Q?",
                "options": [{"text": "A", "correct": True}],
                "points": 1.0,
            },
        ]
        buf = h5p_interactive_video_builder.build(embed, interactions, "Test")
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
        assert "h5p.json" in names
        assert "content/content.json" in names


class TestBuildVimeo:
    def test_build_vimeo(self) -> None:
        embed = {
            "url": "https://vimeo.com/123456",
            "platform": "vimeo",
            "title": "Vimeo Lecture",
        }
        interactions = [
            {
                "interactionId": "q1",
                "time": 5.0,
                "pause": False,
                "questionType": "true_false",
                "questionText": "Is this true?",
                "options": [
                    {"text": "True", "correct": True},
                    {"text": "False", "correct": False},
                ],
                "points": 1.0,
            },
        ]

        buf = h5p_interactive_video_builder.build(embed, interactions, "Vimeo Test")
        _, content_json = _unpack_h5p(buf)

        iv = content_json["interactiveVideo"]
        assert iv["video"]["files"][0]["mime"] == "video/Vimeo"
        assert iv["video"]["files"][0]["path"] == "https://vimeo.com/123456"


class TestBuildEcho360Fails:
    def test_build_echo360_raises(self) -> None:
        embed = {
            "url": "https://echo360.org/video/abc",
            "platform": "echo360",
            "title": "Echo Lecture",
        }
        interactions = [
            {
                "interactionId": "q1",
                "time": 5.0,
                "pause": True,
                "questionType": "multiple_choice",
                "questionText": "Q?",
                "options": [{"text": "A", "correct": True}],
                "points": 1.0,
            },
        ]

        with pytest.raises(ValueError, match="not supported"):
            h5p_interactive_video_builder.build(embed, interactions, "Echo Test")

    def test_build_unknown_platform_raises(self) -> None:
        embed = {
            "url": "https://example.com/video",
            "platform": "unknown",
            "title": "Test",
        }
        interactions = [
            {
                "interactionId": "q1",
                "time": 5.0,
                "pause": True,
                "questionType": "multiple_choice",
                "questionText": "Q?",
                "options": [{"text": "A", "correct": True}],
                "points": 1.0,
            },
        ]

        with pytest.raises(ValueError, match="not supported"):
            h5p_interactive_video_builder.build(embed, interactions, "Test")


class TestBuildMultipleInteractions:
    def test_multiple_interactions_ordered(self) -> None:
        embed = {
            "url": "https://youtube.com/watch?v=abc",
            "platform": "youtube",
            "title": "Test",
        }
        interactions = [
            {
                "interactionId": "q1",
                "time": 10.0,
                "pause": True,
                "questionType": "multiple_choice",
                "questionText": "First Q",
                "options": [{"text": "A", "correct": True}],
                "points": 1.0,
            },
            {
                "interactionId": "q2",
                "time": 30.0,
                "pause": False,
                "questionType": "multiple_choice",
                "questionText": "Second Q",
                "options": [{"text": "B", "correct": True}],
                "points": 2.0,
            },
            {
                "interactionId": "q3",
                "time": 60.0,
                "pause": True,
                "questionType": "true_false",
                "questionText": "Third Q",
                "options": [
                    {"text": "True", "correct": True},
                    {"text": "False", "correct": False},
                ],
                "points": 1.0,
            },
        ]

        buf = h5p_interactive_video_builder.build(embed, interactions, "Multi Test")
        _, content_json = _unpack_h5p(buf)

        h5p_interactions = content_json["interactiveVideo"]["assets"]["interactions"]
        assert len(h5p_interactions) == 3
        assert h5p_interactions[0]["duration"]["from"] == 10.0
        assert h5p_interactions[1]["duration"]["from"] == 30.0
        assert h5p_interactions[2]["duration"]["from"] == 60.0


class TestDetectContentTypesInteractiveVideo:
    def test_detect_interactive_video(self) -> None:
        doc = _doc(
            _video_embed(),
            _video_interaction(time=10.0),
        )
        types = detect_content_types(doc)
        assert CONTENT_TYPE_INTERACTIVE_VIDEO in types

    def test_no_interactive_video_without_interactions(self) -> None:
        doc = _doc(_video_embed())
        types = detect_content_types(doc)
        assert CONTENT_TYPE_INTERACTIVE_VIDEO not in types

    def test_no_interactive_video_without_embed(self) -> None:
        doc = _doc(_video_interaction(time=10.0))
        types = detect_content_types(doc)
        assert CONTENT_TYPE_INTERACTIVE_VIDEO not in types

    def test_interactive_video_targets_include_fallbacks(self) -> None:
        targets = TARGETS_FOR_CONTENT_TYPE[CONTENT_TYPE_INTERACTIVE_VIDEO]
        assert "h5p_interactive_video" in targets
        assert "h5p_question_set" in targets
        assert "qti" in targets


class TestSingleton:
    def test_singleton_is_instance(self) -> None:
        assert isinstance(h5p_interactive_video_builder, H5PInteractiveVideoBuilder)
