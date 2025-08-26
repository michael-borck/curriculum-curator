"""
Pydantic schemas for learning outcomes
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import CamelModel


# Unit Learning Outcome schemas
class ULOBase(CamelModel):
    """Base schema for Unit Learning Outcomes"""

    code: str = Field(
        ..., min_length=1, max_length=20, description="Outcome code (e.g., ULO1)"
    )
    description: str = Field(..., min_length=1, description="Outcome description")
    bloom_level: str = Field(..., description="Bloom's taxonomy level")
    order_index: int = Field(default=0, ge=0, description="Display order")


class ULOCreate(ULOBase):
    """Schema for creating a Unit Learning Outcome"""


class ULOUpdate(CamelModel):
    """Schema for updating a Unit Learning Outcome"""

    code: str | None = Field(None, min_length=1, max_length=20)
    description: str | None = Field(None, min_length=1)
    bloom_level: str | None = None
    order_index: int | None = Field(None, ge=0)


class ULOResponse(ULOBase):
    """Schema for Unit Learning Outcome response"""

    id: str
    unit_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ULOWithMappings(ULOResponse):
    """Schema for ULO with material and assessment mappings"""

    material_count: int = 0
    assessment_count: int = 0


# Weekly Learning Outcome schemas
class WLOBase(BaseModel):
    """Base schema for Weekly Learning Outcomes"""

    week_number: int = Field(..., ge=1, le=52, description="Week number")
    description: str = Field(..., min_length=1, description="Outcome description")
    order_index: int = Field(default=0, ge=0, description="Display order")


class WLOCreate(WLOBase):
    """Schema for creating a Weekly Learning Outcome"""


class WLOUpdate(BaseModel):
    """Schema for updating a Weekly Learning Outcome"""

    week_number: int | None = Field(None, ge=1, le=52)
    description: str | None = Field(None, min_length=1)
    order_index: int | None = Field(None, ge=0)


class WLOResponse(WLOBase):
    """Schema for Weekly Learning Outcome response"""

    id: str
    unit_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Local Learning Outcome schemas
class LLOBase(BaseModel):
    """Base schema for Local Learning Outcomes (material-specific)"""

    description: str = Field(..., min_length=1, description="Outcome description")
    order_index: int = Field(default=0, ge=0, description="Display order")


class LLOCreate(LLOBase):
    """Schema for creating a Local Learning Outcome"""


class LLOUpdate(BaseModel):
    """Schema for updating a Local Learning Outcome"""

    description: str | None = Field(None, min_length=1)
    order_index: int | None = Field(None, ge=0)


class LLOResponse(LLOBase):
    """Schema for Local Learning Outcome response"""

    id: str
    material_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Assessment Learning Outcome schemas
class ALOBase(BaseModel):
    """Base schema for Assessment Learning Outcomes"""

    description: str = Field(..., min_length=1, description="Outcome description")
    order_index: int = Field(default=0, ge=0, description="Display order")


class ALOCreate(ALOBase):
    """Schema for creating an Assessment Learning Outcome"""


class ALOUpdate(BaseModel):
    """Schema for updating an Assessment Learning Outcome"""

    description: str | None = Field(None, min_length=1)
    order_index: int | None = Field(None, ge=0)


class ALOResponse(ALOBase):
    """Schema for Assessment Learning Outcome response"""

    id: str
    assessment_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Reordering schemas
class OutcomeReorder(BaseModel):
    """Schema for reordering outcomes"""

    outcome_ids: list[str] = Field(
        ..., min_length=1, description="Ordered list of outcome IDs"
    )


# Bulk operations
class BulkULOCreate(BaseModel):
    """Schema for creating multiple ULOs at once"""

    outcomes: list[ULOCreate] = Field(..., min_length=1, max_length=50)


class BulkWLOCreate(BaseModel):
    """Schema for creating multiple WLOs at once"""

    week_number: int = Field(..., ge=1, le=52)
    outcomes: list[str] = Field(
        ..., min_length=1, max_length=20, description="List of outcome descriptions"
    )
