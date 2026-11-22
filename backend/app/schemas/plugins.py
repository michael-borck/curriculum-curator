"""
Pydantic schemas for plugin endpoints
"""

from typing import Any

from pydantic import Field

from app.schemas.base import CamelModel

MAX_PLUGIN_CONTENT_LENGTH = 200_000


class PluginValidateRequest(CamelModel):
    content: str = Field(..., max_length=MAX_PLUGIN_CONTENT_LENGTH)
    validators: list[str] | None = Field(default=None, max_length=50)


class PluginRemediateRequest(CamelModel):
    content: str = Field(..., max_length=MAX_PLUGIN_CONTENT_LENGTH)
    remediators: list[str] | None = Field(default=None, max_length=50)


class PluginConfigUpdate(CamelModel):
    enabled: bool | None = None
    priority: int | None = None
    config: dict[str, Any] | None = None


class PluginResultData(CamelModel):
    success: bool
    message: str
    data: dict[str, Any] | None = None
    suggestions: list[str] | None = None


class PluginInfo(CamelModel):
    name: str
    description: str
    plugin_type: str
    enabled: bool
    priority: int


class PluginListResponse(CamelModel):
    plugins: list[PluginInfo]


class PluginValidateResponse(CamelModel):
    results: dict[str, PluginResultData]
    overall_score: float


class PluginRemediateResponse(CamelModel):
    content: str
    results: dict[str, PluginResultData]
    changes_made: list[str]
