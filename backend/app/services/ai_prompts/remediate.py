"""Prompts for /remediate — auto-remediate content (streaming text)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.llm import ContentRemediationRequest

REMEDIATE_SYSTEM = "You are an expert educational content editor."


def render_remediate_prompt(request: ContentRemediationRequest) -> str | None:
    """Render the remediation prompt for the request's type, or None if invalid."""
    if request.remediation_type == "readability":
        return f"""Improve the readability of the following content for university undergraduate students.
Use Australian/British spelling. Make sentences clearer and more accessible.
Preserve the educational intent and technical accuracy.

Original content:
{request.content}

Return ONLY the improved content, no explanations."""
    if request.remediation_type == "structure":
        return f"""Reorganize the following educational content to follow a standard structure:
1. Learning Objectives (2-3 clear objectives)
2. Introduction
3. Main Content with clear sections
4. Summary/Key Takeaways

Preserve the educational content and meaning.

Original content:
{request.content}

Return ONLY the restructured content, no explanations."""
    if request.custom_prompt:
        return f"""{request.custom_prompt}

Content to improve:
{request.content}

Return ONLY the improved content."""
    return None
