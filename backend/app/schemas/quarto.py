"""
Quarto-related schemas for API requests and responses
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.base import CamelModel


class QuartoSimpleSettings(CamelModel):
    """Simple mode settings for Quarto"""
    
    formats: List[str] = Field(default=["html"], description="Output formats")
    theme: str = Field(default="default", description="Theme for HTML/RevealJS")
    toc: bool = Field(default=True, description="Include table of contents")
    author: Optional[str] = Field(None, description="Document author")
    title: Optional[str] = Field(None, description="Document title")
    subtitle: Optional[str] = Field(None, description="Document subtitle")


class QuartoExportRequest(CamelModel):
    """Request for exporting content"""
    
    mode: str = Field(..., description="'simple' or 'advanced'")
    settings: Dict[str, Any] = Field(..., description="Settings based on mode")


class QuartoExportResponse(CamelModel):
    """Response from content export"""
    
    success: bool
    render_id: str = Field(alias="renderId")
    outputs: List[Dict[str, Any]]
    yaml_used: str = Field(alias="yamlUsed")


class QuartoPreviewRequest(CamelModel):
    """Request for content preview"""
    
    content: Optional[str] = Field(None, description="Content to preview (uses saved if not provided)")
    settings: Optional[Dict[str, Any]] = Field(None, description="Preview settings")


class QuartoSettingsUpdate(CamelModel):
    """Update Quarto settings for content"""
    
    simple_settings: Optional[Dict[str, Any]] = Field(None, alias="simpleSettings")
    advanced_yaml: Optional[str] = Field(None, alias="advancedYaml")
    active_mode: Optional[str] = Field(None, alias="activeMode")
    active_preset: Optional[str] = Field(None, alias="activePreset")


class QuartoPresetCreate(CamelModel):
    """Create a new Quarto preset"""
    
    name: str = Field(..., min_length=1, max_length=255)
    yaml_content: str = Field(..., alias="yamlContent")
    is_default: bool = Field(default=False, alias="isDefault")


class QuartoPresetResponse(CamelModel):
    """Response for Quarto preset"""
    
    id: str
    name: str
    yaml_content: str = Field(alias="yamlContent")
    is_default: bool = Field(alias="isDefault")
    created_at: str = Field(alias="createdAt")


class QuartoThemesResponse(CamelModel):
    """Available themes for different formats"""
    
    html: List[str]
    revealjs: List[str]