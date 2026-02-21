"""
Pydantic schemas for plugin endpoints
"""

from typing import Any

from app.schemas.base import CamelModel


class PluginValidateRequest(CamelModel):
    content: str
    validators: list[str] | None = None


class PluginRemediateRequest(CamelModel):
    content: str
    remediators: list[str] | None = None


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
