"""Prompt for /visual-prompt — generate an image-generation prompt."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.ai import VisualPromptRequest

VISUAL_PROMPT_SYSTEM = (
    "You are an expert visual prompt engineer for AI image generation tools. "
    "You create detailed, effective prompts that produce high-quality educational "
    "imagery. Always respond with valid JSON only."
)


def render_visual_prompt(request: VisualPromptRequest) -> str:
    """Render the visual-prompt generation prompt."""
    context_line = f"\nPurpose: {request.context}" if request.context else ""
    return f"""Generate a detailed image-generation prompt based on the following educational content.

Style: {request.style}
Aspect ratio: {request.aspect_ratio}{context_line}

Educational content:
{request.content}

Return a JSON object with exactly these keys:
{{
  "prompt": "A detailed, vivid image generation prompt (1-3 sentences). Be specific about composition, colours, mood, and subject matter. Make it tool-agnostic (works with Midjourney, DALL-E, Stable Diffusion, etc.).",
  "negative_prompt": "A comma-separated list of things to avoid (e.g. text, watermarks, blurry, low quality).",
  "style_notes": "1-2 sentences of practical tips for generating this style of image (e.g. recommended tools, settings, or modifiers)."
}}

Return ONLY valid JSON, no markdown fences or extra text."""
