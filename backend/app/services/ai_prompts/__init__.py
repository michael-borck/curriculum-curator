"""
Generation prompts for the structured AI endpoints, as code.

Each endpoint's hardened system prompt + a ``render_*`` function lives here,
co-located with the response model it targets. Kept as code (not the Jinja2
library or DB templates) because these are injection-hardened machinery prompts
whose exact JSON shape is coupled to a Pydantic response model.
"""

from app.services.ai_prompts.scaffold import (
    SCAFFOLD_UNIT_SYSTEM,
    render_scaffold_unit_prompt,
)
from app.services.ai_prompts.schedule import (
    SCHEDULE_SYSTEM,
    render_schedule_prompt,
)
from app.services.ai_prompts.validate import (
    VALIDATE_SYSTEM,
    ValidationCheck,
    render_validation_prompt,
)
from app.services.ai_prompts.video import (
    SUGGEST_POINTS_SYSTEM,
    VIDEO_INTERACTION_SYSTEM,
    render_suggest_points_prompt,
    render_video_interaction_prompt,
)
from app.services.ai_prompts.visual import (
    VISUAL_PROMPT_SYSTEM,
    render_visual_prompt,
)

__all__ = [
    "SCAFFOLD_UNIT_SYSTEM",
    "SCHEDULE_SYSTEM",
    "SUGGEST_POINTS_SYSTEM",
    "VALIDATE_SYSTEM",
    "VIDEO_INTERACTION_SYSTEM",
    "VISUAL_PROMPT_SYSTEM",
    "ValidationCheck",
    "render_scaffold_unit_prompt",
    "render_schedule_prompt",
    "render_suggest_points_prompt",
    "render_validation_prompt",
    "render_video_interaction_prompt",
    "render_visual_prompt",
]
