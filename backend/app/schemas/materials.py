"""
Pydantic schemas for weekly materials
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.learning_outcomes import LLOResponse, ULOResponse


class MaterialBase(BaseModel):
    """Base schema for Weekly Materials"""

    week_number: int = Field(..., ge=1, le=52, description="Week number")
    title: str = Field(..., min_length=1, max_length=500, description="Material title")
    type: str = Field(..., description="Material type (lecture, handout, quiz, etc.)")
    description: str | None = Field(None, description="Material description")
    duration_minutes: int | None = Field(None, ge=0, description="Estimated duration in minutes")
    order_index: int = Field(default=0, ge=0, description="Display order within week")
    status: str = Field(default="draft", description="Material status")


class MaterialCreate(MaterialBase):
    """Schema for creating a Weekly Material"""

    file_path: str | None = Field(None, max_length=500, description="Path to content file")
    material_metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class MaterialUpdate(BaseModel):
    """Schema for updating a Weekly Material"""

    week_number: int | None = Field(None, ge=1, le=52)
    title: str | None = Field(None, min_length=1, max_length=500)
    type: str | None = None
    description: str | None = None
    duration_minutes: int | None = Field(None, ge=0)
    file_path: str | None = Field(None, max_length=500)
    material_metadata: dict[str, Any] | None = None
    order_index: int | None = Field(None, ge=0)
    status: str | None = None


class MaterialResponse(MaterialBase):
    """Schema for Weekly Material response"""

    id: str
    unit_id: str
    file_path: str | None
    material_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaterialWithOutcomes(MaterialResponse):
    """Schema for Material with its learning outcomes"""

    local_outcomes: list[LLOResponse] = []
    mapped_ulos: list[ULOResponse] = []


class MaterialDuplicate(BaseModel):
    """Schema for duplicating a material"""

    target_week: int = Field(..., ge=1, le=52, description="Target week number")
    new_title: str | None = Field(None, min_length=1, max_length=500, description="Optional new title")


class MaterialReorder(BaseModel):
    """Schema for reordering materials within a week"""

    material_ids: list[str] = Field(..., min_length=1, description="Ordered list of material IDs")


class MaterialMapping(BaseModel):
    """Schema for mapping materials to ULOs"""

    ulo_ids: list[str] = Field(..., description="List of ULO IDs to map")


class MaterialBulkCreate(BaseModel):
    """Schema for creating multiple materials at once"""

    week_number: int = Field(..., ge=1, le=52)
    materials: list[MaterialCreate] = Field(..., min_length=1, max_length=20)


class WeekMaterials(BaseModel):
    """Schema for all materials in a week"""

    week_number: int
    total_duration_minutes: int
    material_count: int
    materials: list[MaterialResponse]


class MaterialFilter(BaseModel):
    """Schema for filtering materials"""

    week_number: int | None = Field(None, ge=1, le=52)
    type: str | None = None
    status: str | None = None
    search: str | None = Field(None, description="Search in title and description")
