"""Prompt for /generate-schedule — generate a weekly course schedule."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.llm import ScheduleGenerationRequest

SCHEDULE_SYSTEM = (
    "You are an expert curriculum designer. Always respond with valid JSON only, "
    "no additional text."
)


def render_schedule_prompt(
    request: ScheduleGenerationRequest,
    style_instruction: str,
    design_block: str,
) -> str:
    """Render the schedule prompt. Asks for a JSON object ``{"weeks": [...]}`` so
    it validates directly against GeneratedSchedule (summary is set server-side)."""
    outcomes_text = (
        "; ".join(request.learning_outcomes) if request.learning_outcomes else ""
    )
    return f"""Create a {request.duration_weeks}-week university course schedule for:

Title: {request.unit_title}
Description: {request.unit_description}
Learning Outcomes: {outcomes_text}
{style_instruction}{design_block}

For each week, provide:
1. A clear, descriptive title/theme
2. 2-4 key topics to be covered
3. Specific learning objectives for that week

Ensure logical progression from foundational to advanced concepts.
Use Australian/British English conventions.

Return the schedule as a JSON object with this exact structure:
{{
  "weeks": [
    {{
      "week_number": 1,
      "title": "Week title",
      "topics": ["topic1", "topic2"],
      "learning_objectives": ["objective1", "objective2"]
    }}
  ]
}}"""
