"""
Schemas for admin configuration management
"""

from typing import Any

from pydantic import BaseModel, Field

from app.models import ConfigCategory


class ConfigBase(BaseModel):
    """Base configuration schema"""

    key: str = Field(..., description="Configuration key")
    value: str = Field(..., description="Configuration value")
    category: ConfigCategory = Field(..., description="Configuration category")
    value_type: str = Field("string", description="Value type")
    description: str | None = Field(None, description="Configuration description")
    is_sensitive: bool = Field(False, description="Whether value is sensitive")
    validation_regex: str | None = Field(None, description="Validation regex pattern")
    min_value: float | None = Field(None, description="Minimum value for numeric types")
    max_value: float | None = Field(None, description="Maximum value for numeric types")
    allowed_values: list[str] | None = Field(None, description="List of allowed values")
    requires_restart: bool = Field(False, description="Whether change requires restart")


class ConfigCreate(ConfigBase):
    """Schema for creating a configuration"""


class ConfigUpdate(BaseModel):
    """Schema for updating a configuration"""

    value: str | None = Field(None, description="New value")
    description: str | None = Field(None, description="New description")
    validation_regex: str | None = Field(None, description="New validation regex")
    min_value: float | None = Field(None, description="New minimum value")
    max_value: float | None = Field(None, description="New maximum value")
    allowed_values: list[str] | None = Field(None, description="New allowed values")


class ConfigBulkUpdate(BaseModel):
    """Schema for bulk updating configurations"""

    updates: dict[str, str] = Field(..., description="Map of key to new value")


class ConfigResponse(ConfigBase):
    """Response schema for a configuration"""

    id: str
    created_at: str
    updated_at: str
    warning: str | None = None


class ConfigListResponse(BaseModel):
    """Response schema for configuration list"""

    configs: list[ConfigResponse]
    total: int
    skip: int
    limit: int


class ConfigExport(BaseModel):
    """Schema for configuration export"""

    version: str
    exported_at: str
    exported_by: str
    configs: list[dict[str, Any]]
