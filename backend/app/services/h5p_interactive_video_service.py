"""
H5P Interactive Video package builder.

Generates .h5p (ZIP) archives containing an Interactive Video from
video embed data and quiz interactions extracted from TipTap content_json.

Supported platforms: YouTube, Vimeo.
Echo360 and other platforms raise ValueError (caller handles fallback).
"""

import json
import uuid
import zipfile
from io import BytesIO
from typing import Any

from app.services.h5p_service import (
    _MULTI_CHOICE_LIB,  # pyright: ignore[reportPrivateUsage]
    _TYPE_MAP,  # pyright: ignore[reportPrivateUsage]
    H5PQuestionSetBuilder,
)
from app.services.unit_export_data import InMemoryQuizQuestion

# H5P library version dicts
_INTERACTIVE_VIDEO_LIB: dict[str, Any] = {
    "machineName": "H5P.InteractiveVideo",
    "majorVersion": 1,
    "minorVersion": 27,
}

# Platform → H5P MIME type mapping
_PLATFORM_MIME: dict[str, str] = {
    "youtube": "video/YouTube",
    "vimeo": "video/Vimeo",
}

# Unsupported platforms
_UNSUPPORTED_PLATFORMS: set[str] = {"echo360"}

# Reuse question-building logic from H5PQuestionSetBuilder
_question_builder = H5PQuestionSetBuilder()


def _interaction_to_quiz_question(interaction: dict[str, Any]) -> InMemoryQuizQuestion:
    """Convert a videoInteraction attrs dict to a duck-typed QuizQuestion."""
    options_raw: list[dict[str, Any]] = interaction.get("options", [])

    options = [{"text": str(o.get("text", ""))} for o in options_raw]
    correct_answers = [
        str(o.get("text", "")) for o in options_raw if o.get("correct", False)
    ]

    return InMemoryQuizQuestion(
        question_id=str(interaction.get("interactionId", str(uuid.uuid4()))),
        question_text=str(interaction.get("questionText", "")),
        question_type=str(interaction.get("questionType", "multiple_choice")),
        options=options,
        correct_answers=correct_answers,
        answer_explanation=interaction.get("feedback") or None,
        points=float(interaction.get("points", 1.0)),
        order_index=0,
    )


class H5PInteractiveVideoBuilder:
    """Builds an H5P Interactive Video package (.h5p ZIP)."""

    def build(
        self,
        video_embed: dict[str, Any],
        interactions: list[dict[str, Any]],
        title: str,
    ) -> BytesIO:
        """Create .h5p ZIP with content.json + h5p.json.

        Args:
            video_embed: Video embed attrs (url, platform, title).
            interactions: List of videoInteraction attrs dicts, sorted by time.
            title: Title for the interactive video.

        Returns:
            BytesIO containing the .h5p ZIP archive.

        Raises:
            ValueError: If the video platform is not supported (e.g. Echo360).
        """
        platform = str(video_embed.get("platform", "")).lower()

        if platform in _UNSUPPORTED_PLATFORMS or platform not in _PLATFORM_MIME:
            msg = f"Platform '{platform}' is not supported for H5P Interactive Video. Only YouTube and Vimeo are supported."
            raise ValueError(msg)

        mime_type = _PLATFORM_MIME[platform]
        video_url = str(video_embed.get("url", ""))
        video_title = str(video_embed.get("title", "")) or title

        h5p_interactions = self._build_interactions(interactions)
        content_json = self._build_content_json(
            video_url, mime_type, video_title, h5p_interactions
        )
        h5p_json = self._build_h5p_json(title)

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("h5p.json", json.dumps(h5p_json, indent=2))
            zf.writestr("content/content.json", json.dumps(content_json, indent=2))
        buf.seek(0)
        return buf

    def _build_interactions(
        self, interactions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Convert video interactions to H5P interaction objects."""
        h5p_interactions: list[dict[str, Any]] = []

        for interaction in interactions:
            q = _interaction_to_quiz_question(interaction)
            q_type = str(q.question_type)
            lib = _TYPE_MAP.get(q_type, _MULTI_CHOICE_LIB)  # pyright: ignore[reportPrivateUsage]
            h5p_question = _question_builder._build_question(q, q_type, lib)  # pyright: ignore[reportPrivateUsage, reportArgumentType]

            time_val = float(interaction.get("time", 0))
            pause = bool(interaction.get("pause", True))

            h5p_interaction: dict[str, Any] = {
                "x": 50,
                "y": 50,
                "width": 10,
                "height": 10,
                "duration": {
                    "from": time_val,
                    "to": time_val,
                },
                "pause": pause,
                "action": h5p_question,
                "label": str(q.question_text)[:50],
            }
            h5p_interactions.append(h5p_interaction)

        return h5p_interactions

    def _build_content_json(
        self,
        video_url: str,
        mime_type: str,
        video_title: str,
        interactions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build the content/content.json structure."""
        return {
            "interactiveVideo": {
                "video": {
                    "startScreenOptions": {"title": video_title},
                    "textTracks": {"videoTrack": []},
                    "files": [{"path": video_url, "mime": mime_type}],
                },
                "assets": {
                    "interactions": interactions,
                },
            },
        }

    def _build_h5p_json(self, title: str) -> dict[str, Any]:
        """Build the h5p.json manifest."""
        return {
            "title": title,
            "mainLibrary": "H5P.InteractiveVideo",
            "language": "en",
            "embedTypes": ["div", "iframe"],
            "preloadedDependencies": [_INTERACTIVE_VIDEO_LIB],
        }


# Module-level singleton
h5p_interactive_video_builder = H5PInteractiveVideoBuilder()
