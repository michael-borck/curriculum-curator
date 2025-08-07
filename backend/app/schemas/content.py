"""
Pydantic schemas for content-related requests/responses
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional

class ContentGenerationRequest(BaseModel):
    content_type: str
    pedagogy_style: str
    context: Dict[str, Any]
    stream: bool = False

class ContentEnhanceRequest(BaseModel):
    content: str
    pedagogy_style: str
    suggestions: Optional[list] = None

class ContentValidationResponse(BaseModel):
    is_valid: bool
    issues: list
    suggestions: list
