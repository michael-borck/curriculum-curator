"""Prompts for /validate — per-type content validation checks."""

from __future__ import annotations

from pydantic import BaseModel

VALIDATE_SYSTEM = (
    "You are an expert educational content reviewer. "
    "Always respond with valid JSON only."
)


class ValidationCheck(BaseModel):
    """The LLM output shape for a single validation check.

    Intermediate model: the route maps this into a ValidationResult, adding the
    server-set validator_name and remediation_prompt.
    """

    passed: bool = True
    score: float | None = None
    message: str = "Validation complete"
    suggestions: list[str] | None = None


def render_validation_prompt(validation_type: str, content: str) -> str | None:
    """Render the prompt for a validation type, or None if unsupported."""
    if validation_type == "readability":
        return f"""Analyze the readability of the following educational content for university undergraduate students.

Content:
{content}

Evaluate:
1. Is the language clear and accessible?
2. Are sentences well-structured and not overly complex?
3. Is technical terminology appropriately introduced and explained?
4. Does it use Australian/British English conventions?

Return JSON with:
{{
  "passed": true/false,
  "score": 0-100,
  "message": "brief assessment",
  "suggestions": ["suggestion1", "suggestion2"]
}}"""
    if validation_type == "structure":
        return f"""Analyze the structure of the following educational content.

Content:
{content}

Evaluate:
1. Does it have a logical flow and organization?
2. Are there clear sections (intro, body, conclusion)?
3. Are learning objectives or key points clearly stated?
4. Does it include appropriate examples or explanations?

Return JSON with:
{{
  "passed": true/false,
  "score": 0-100,
  "message": "brief assessment",
  "suggestions": ["suggestion1", "suggestion2"]
}}"""
    return None
