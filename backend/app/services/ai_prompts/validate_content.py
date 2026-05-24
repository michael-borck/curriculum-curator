"""Prompt for /validate-content — AI quality validation (chat completion)."""

from __future__ import annotations

VALIDATE_CONTENT_SYSTEM = "You are an expert content validator."


def render_validate_content_prompt(content: str, validation_type: str) -> str:
    """Render the comprehensive content-validation prompt."""
    return f"""Validate the following content for {validation_type} quality:

{content}

Check for:
1. Factual accuracy
2. Internal consistency
3. Completeness of coverage
4. Logical flow
5. Appropriate difficulty level

Return findings as JSON with keys: issues, suggestions, score"""
