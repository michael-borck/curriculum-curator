"""Prompt for /fill-gap — generate content for a unit-structure gap (text)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.ai import FillGapRequest

FILL_GAP_SYSTEM = (
    "You are an expert university curriculum designer helping fill gaps in a "
    "unit structure."
)

_GAP_PROMPTS = {
    "ulo": "Generate a well-written Unit Learning Outcome (ULO) description. Use Bloom's taxonomy verbs. Be specific and measurable.",
    "material": "Generate a brief content outline for a teaching material. Include key topics, activities, and learning objectives.",
    "assessment": "Suggest an assessment item including: title, description, type (quiz/assignment/project/exam), and recommended weight.",
}


def render_fill_gap_prompt(request: FillGapRequest, design_block: str) -> str:
    """Render the fill-gap prompt. ``design_block`` is the (optional) formatted
    Learning Design spec to append."""
    base_prompt = _GAP_PROMPTS.get(request.gap_type, _GAP_PROMPTS["material"])
    extra_context = (
        f"\n\nAdditional context: {request.context}" if request.context else ""
    )
    return f"{base_prompt}{extra_context}{design_block}"
