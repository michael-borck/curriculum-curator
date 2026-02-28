"""
Content-type detection and 4-level export-target resolution.

Resolution chain (each level overrides the previous):
1. Auto-infer — sane defaults from content type
2. User settings — per-content-type defaults from teaching_preferences
3. Per-material override — stored in weekly_material.export_targets
4. At export time — final override from the export dialog (applied client-side)
"""

from __future__ import annotations

from typing import Any

from app.services.slide_splitter import has_slide_breaks
from app.services.unit_export_data import (
    extract_branching_cards,
    extract_quiz_nodes,
    extract_video_embed,
    extract_video_interactions,
)

# ─── Content type detection ───────────────────────────────────────────

CONTENT_TYPE_QUIZ = "quiz"
CONTENT_TYPE_SLIDES = "slides"
CONTENT_TYPE_BRANCHING = "branching"
CONTENT_TYPE_INTERACTIVE_VIDEO = "interactive_video"
CONTENT_TYPE_RICH_TEXT = "rich_text"


def detect_content_types(content_json: dict[str, Any] | None) -> list[str]:
    """Walk content_json and return detected content type tags.

    Returns a list like ``["quiz", "slides"]``.  Falls back to
    ``["rich_text"]`` when no specialised content is found.
    """
    if not content_json:
        return [CONTENT_TYPE_RICH_TEXT]

    types: list[str] = []

    if extract_quiz_nodes(content_json):
        types.append(CONTENT_TYPE_QUIZ)

    if has_slide_breaks(content_json):
        types.append(CONTENT_TYPE_SLIDES)

    if extract_branching_cards(content_json):
        types.append(CONTENT_TYPE_BRANCHING)

    if extract_video_embed(content_json) and extract_video_interactions(content_json):
        types.append(CONTENT_TYPE_INTERACTIVE_VIDEO)

    return types or [CONTENT_TYPE_RICH_TEXT]


# ─── Target resolution ────────────────────────────────────────────────

# Level 1: auto-inferred defaults per content type
AUTO_DEFAULTS: dict[str, list[str]] = {
    CONTENT_TYPE_QUIZ: ["qti"],
    CONTENT_TYPE_SLIDES: ["h5p_course_presentation"],
    CONTENT_TYPE_BRANCHING: ["h5p_branching"],
    CONTENT_TYPE_INTERACTIVE_VIDEO: ["h5p_interactive_video"],
    CONTENT_TYPE_RICH_TEXT: ["html"],
}

# Valid targets per content type (used by the dialog for available options)
TARGETS_FOR_CONTENT_TYPE: dict[str, list[str]] = {
    CONTENT_TYPE_QUIZ: ["qti", "h5p_question_set"],
    CONTENT_TYPE_SLIDES: ["h5p_course_presentation", "html"],
    CONTENT_TYPE_BRANCHING: ["h5p_branching"],
    CONTENT_TYPE_INTERACTIVE_VIDEO: [
        "h5p_interactive_video",
        "h5p_question_set",
        "qti",
    ],
    CONTENT_TYPE_RICH_TEXT: ["html"],
}

# All known target strings (for validation)
ALL_KNOWN_TARGETS: set[str] = {
    t for targets in TARGETS_FOR_CONTENT_TYPE.values() for t in targets
}


def resolve_targets_for_material(
    content_types: list[str],
    material_targets: list[str],
    user_defaults: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Resolve export targets for a material, applying levels 1-3.

    Args:
        content_types: Detected content types (from ``detect_content_types``).
        material_targets: Per-material override targets (from ``WeeklyMaterial.export_targets_list``).
        user_defaults: User-level defaults from ``teaching_preferences.export_defaults``.

    Returns:
        Mapping of content_type → resolved targets.
        e.g. ``{"quiz": ["qti"], "slides": ["h5p_course_presentation"]}``
    """
    result: dict[str, list[str]] = {}

    for ct in content_types:
        valid = set(TARGETS_FOR_CONTENT_TYPE.get(ct, []))

        # Level 1: auto defaults
        targets = list(AUTO_DEFAULTS.get(ct, ["html"]))

        # Level 2: user defaults
        if user_defaults and ct in user_defaults:
            user_targets = [t for t in user_defaults[ct] if t in valid]
            if user_targets:
                targets = user_targets

        # Level 3: per-material override
        if material_targets:
            mat_targets = [t for t in material_targets if t in valid]
            if mat_targets:
                targets = mat_targets

        result[ct] = targets

    return result
