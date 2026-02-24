"""
Pydantic schemas for Custom Alignment Frameworks, items, and ULO→item mappings
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import CamelModel

# ============= Framework Item Schemas =============


class FrameworkItemCreate(CamelModel):
    """Schema for creating a framework item"""

    code: str = Field(..., max_length=20, description="Item code (e.g. 'PLO1', 'G')")
    description: str = Field(..., description="Full description of the item")
    is_ai_suggested: bool = Field(default=False)
    notes: str | None = Field(None)
    order_index: int = Field(default=0)


class FrameworkItemUpdate(CamelModel):
    """Schema for updating a framework item"""

    code: str | None = None
    description: str | None = None
    notes: str | None = None
    order_index: int | None = None


class FrameworkItemResponse(CamelModel):
    """Schema for framework item response"""

    id: str
    framework_id: str
    code: str
    description: str
    is_ai_suggested: bool
    notes: str | None
    order_index: int
    created_at: datetime
    updated_at: datetime


# ============= Framework Schemas =============


class FrameworkCreate(CamelModel):
    """Schema for creating a custom alignment framework"""

    name: str = Field(..., max_length=100, description="Framework name")
    description: str | None = Field(None, description="Optional description")
    preset_type: str | None = Field(
        None,
        max_length=30,
        description="Preset type (plo, grit, ethics, indigenous, vision)",
    )
    icon_hint: str | None = Field(None, max_length=10, description="Emoji icon hint")
    color_hint: str | None = Field(
        None, max_length=30, description="Tailwind color hint"
    )
    order_index: int = Field(default=0)
    items: list[FrameworkItemCreate] = Field(
        default_factory=list,
        description="Optional initial items to create with the framework",
    )


class FrameworkUpdate(CamelModel):
    """Schema for updating a framework"""

    name: str | None = None
    description: str | None = None
    icon_hint: str | None = None
    color_hint: str | None = None
    order_index: int | None = None


class FrameworkResponse(CamelModel):
    """Schema for framework response with nested items"""

    id: str
    unit_id: str
    name: str
    description: str | None
    preset_type: str | None
    icon_hint: str | None
    color_hint: str | None
    order_index: int
    items: list[FrameworkItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class FrameworkSummary(CamelModel):
    """Summary of all frameworks for a unit"""

    unit_id: str
    framework_count: int
    frameworks: list[FrameworkResponse] = Field(default_factory=list)


# ============= ULO→Item Mapping Schemas =============


class ULOItemMappingCreate(CamelModel):
    """Schema for creating a ULO→framework item mapping"""

    item_id: str = Field(..., description="Framework item ID")
    is_ai_suggested: bool = Field(default=False)
    notes: str | None = Field(None)


class ULOItemMappingResponse(CamelModel):
    """Schema for ULO→item mapping response"""

    id: str
    ulo_id: str
    item_id: str
    is_ai_suggested: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class BulkULOItemMappingCreate(BaseModel):
    """Schema for bulk-replacing all framework item mappings for a ULO"""

    mappings: list[ULOItemMappingCreate] = Field(
        default_factory=list,
        description="List of ULO→item mappings",
    )
