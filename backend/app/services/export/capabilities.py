"""Export capability matrix and warnings (story 9.21).

Detects content features in a material's ``content_json`` and reports what
a given export target will silently drop or convert, so the export UI can
warn the user and suggest a better-fitting format before they export.

Grounded in the actual adapter behaviour:
- ``h5p_service._TYPE_MAP`` falls back to MultiChoice for question types it
  doesn't model (matching, long_answer, case_study, scenario) — a silent
  *conversion*.
- ``qti_service`` logs a warning and omits question types it can't render —
  a silent *drop*. QTI covers every type the editor can currently author.
- Exporting interactive-video content to a quiz target (qti, h5p_question
  _set) keeps the questions but *drops* the video itself.

The matrix is the single source of truth; a drift-guard test exercises each
declared-supported question type through the real adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.format_resolver import (
    CONTENT_TYPE_INTERACTIVE_VIDEO,
    CONTENT_TYPE_QUIZ,
)

# Human-readable question-type labels for warning messages.
QUESTION_TYPE_LABELS: dict[str, str] = {
    "multiple_choice": "Multiple choice",
    "multi_select": "Multiple select",
    "true_false": "True/False",
    "short_answer": "Short answer",
    "fill_in_blank": "Fill in the blank",
    "long_answer": "Long answer",
    "matching": "Matching",
    "case_study": "Case study",
    "scenario": "Scenario",
    "drag_drop": "Drag and drop",
}


@dataclass
class ContentFeatures:
    """Features detected in a material's content_json relevant to export."""

    question_types: set[str] = field(default_factory=set)
    has_video: bool = False
    has_tables: bool = False
    has_images: bool = False
    has_mermaid: bool = False


@dataclass(frozen=True)
class FormatCapabilities:
    """What a single export target can represent.

    ``question_types`` lists the types the target renders faithfully.
    ``converts_unlisted_questions`` is True when unlisted types are silently
    coerced (h5p_question_set → MultiChoice) rather than dropped (qti).
    ``carries_video`` is True when the target preserves an embedded video.
    """

    question_types: frozenset[str] = frozenset()
    converts_unlisted_questions: bool = False
    carries_video: bool = False


# Question types QTI renders (every type the editor/import can produce except
# drag_drop, which has no QTI primitive). Unlisted types are dropped.
_QTI_QUESTION_TYPES = frozenset(
    {
        "multiple_choice",
        "multi_select",
        "true_false",
        "short_answer",
        "fill_in_blank",
        "long_answer",
        "matching",
        "case_study",
        "scenario",
    }
)

# Question types H5P Question Set models with a dedicated library. Unlisted
# types fall back to MultiChoice (a silent conversion).
_H5P_QS_QUESTION_TYPES = frozenset(
    {
        "multiple_choice",
        "multi_select",
        "true_false",
        "short_answer",
        "fill_in_blank",
    }
)

FORMAT_CAPABILITIES: dict[str, FormatCapabilities] = {
    "qti": FormatCapabilities(question_types=_QTI_QUESTION_TYPES),
    "h5p_question_set": FormatCapabilities(
        question_types=_H5P_QS_QUESTION_TYPES,
        converts_unlisted_questions=True,
    ),
    "h5p_interactive_video": FormatCapabilities(carries_video=True),
    "h5p_course_presentation": FormatCapabilities(),
    "h5p_branching": FormatCapabilities(),
    "html": FormatCapabilities(),
}


@dataclass(frozen=True)
class ExportWarning:
    """A single capability mismatch for a (content_type, target) pair."""

    severity: str  # "converted" | "dropped"
    message: str
    suggested_target: str | None = None


def _walk_types(content_json: dict[str, Any] | None) -> set[str]:
    """Collect the set of node ``type`` strings present anywhere in the doc."""
    seen: set[str] = set()
    if not content_json:
        return seen

    def _walk(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            node_type = node.get("type")
            if isinstance(node_type, str):
                seen.add(node_type)
            children = node.get("content")
            if isinstance(children, list):
                _walk(children)

    top = content_json.get("content")
    if isinstance(top, list):
        _walk(top)
    return seen


def detect_content_features(
    content_json: dict[str, Any] | None,
) -> ContentFeatures:
    """Detect export-relevant features from a material's content_json."""
    # Local import avoids a module-load cycle with unit_export_data.
    from app.services.unit_export_data import (  # noqa: PLC0415
        extract_quiz_nodes,
        extract_video_embed,
    )

    features = ContentFeatures()
    if not content_json:
        return features

    features.question_types = {
        str(q.question_type) for q in extract_quiz_nodes(content_json)
    }
    features.has_video = extract_video_embed(content_json) is not None

    node_types = _walk_types(content_json)
    features.has_tables = "table" in node_types
    features.has_images = "image" in node_types
    features.has_mermaid = "mermaid" in node_types
    return features


def _suggest_for_question_type(qtype: str) -> str | None:
    """Pick a target that renders ``qtype`` faithfully, preferring QTI."""
    for target in ("qti", "h5p_question_set"):
        if qtype in FORMAT_CAPABILITIES[target].question_types:
            return target
    return None


def warnings_for(
    content_type: str,
    target: str,
    features: ContentFeatures,
) -> list[ExportWarning]:
    """Return warnings for exporting ``content_type`` content to ``target``."""
    caps = FORMAT_CAPABILITIES.get(target)
    if caps is None:
        return []

    warnings: list[ExportWarning] = []

    # Quiz question-type mismatches
    if content_type == CONTENT_TYPE_QUIZ and features.question_types:
        for qtype in sorted(features.question_types):
            if qtype in caps.question_types:
                continue
            label = QUESTION_TYPE_LABELS.get(qtype, qtype.replace("_", " "))
            suggestion = _suggest_for_question_type(qtype)
            if caps.converts_unlisted_questions:
                warnings.append(
                    ExportWarning(
                        severity="converted",
                        message=(
                            f"{label} questions become multiple choice in this format."
                        ),
                        suggested_target=suggestion,
                    )
                )
            else:
                warnings.append(
                    ExportWarning(
                        severity="dropped",
                        message=(
                            f"{label} questions can't be represented in this "
                            f"format and will be omitted."
                        ),
                        suggested_target=suggestion,
                    )
                )

    # Interactive video exported to a target that can't carry the video
    if (
        content_type == CONTENT_TYPE_INTERACTIVE_VIDEO
        and features.has_video
        and not caps.carries_video
    ):
        warnings.append(
            ExportWarning(
                severity="dropped",
                message=(
                    "The video itself isn't included — only the questions are exported."
                ),
                suggested_target="h5p_interactive_video",
            )
        )

    return warnings
