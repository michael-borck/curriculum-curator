"""
Pydantic schemas for content-related requests/responses
"""

from typing import Any

from pydantic import BaseModel


class ContentGenerationRequest(BaseModel):
    content_type: str
    pedagogy_style: str
    context: dict[str, Any]
    stream: bool = False


class ContentEnhanceRequest(BaseModel):
    content: str
    pedagogy_style: str
    suggestions: list | None = None


class ContentValidationResponse(BaseModel):
    is_valid: bool
    issues: list
    suggestions: list
