"""
LRD (Learning Requirements Document) API schemas
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import CamelModel


class LRDCreate(CamelModel):
    """Request schema for creating an LRD"""

    unit_id: str
    content: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"


class LRDUpdate(CamelModel):
    """Request schema for updating an LRD"""

    content: dict[str, Any] | None = None
    version: str | None = None


class LRDResponse(CamelModel):
    """Full LRD response schema"""

    id: str
    unit_id: str
    version: str
    status: str
    content: dict[str, Any]
    approval_history: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class LRDListItem(CamelModel):
    """Summary LRD response (without full content)"""

    id: str
    unit_id: str
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
