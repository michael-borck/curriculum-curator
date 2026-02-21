"""
Learning Design API schemas
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import CamelModel


class DesignCreate(CamelModel):
    """Request schema for creating a learning design"""

    unit_id: str
    content: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"


class DesignUpdate(CamelModel):
    """Request schema for updating a learning design"""

    content: dict[str, Any] | None = None
    version: str | None = None


class DesignResponse(CamelModel):
    """Full learning design response schema"""

    id: str
    unit_id: str
    version: str
    status: str
    content: dict[str, Any]
    approval_history: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class DesignListItem(CamelModel):
    """Summary learning design response (without full content)"""

    id: str
    unit_id: str
    version: str
    status: str
    created_at: datetime
    updated_at: datetime
