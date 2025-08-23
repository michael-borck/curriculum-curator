"""
Pydantic schemas for Unit models
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.unit import DifficultyLevel, PedagogyType, Semester, UnitStatus
from app.schemas.base import CamelModel


class UnitBase(CamelModel):
    """Base unit schema with common fields"""

    title: str = Field(..., min_length=1, max_length=500)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    year: int = Field(..., ge=2020, le=2100)
    semester: Semester = Semester.SEMESTER_1
    pedagogy_type: PedagogyType = PedagogyType.INQUIRY_BASED
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    duration_weeks: int = Field(12, ge=1, le=52)
    credit_points: int = Field(25, ge=1, le=100)
    prerequisites: str | None = None
    learning_hours: int | None = Field(None, ge=0, le=1000)
    unit_metadata: dict[str, Any] | None = None
    generation_context: str | None = None


class UnitCreate(UnitBase):
    """Schema for creating a new unit"""

    status: UnitStatus = UnitStatus.DRAFT


class UnitUpdate(CamelModel):
    """Schema for updating an existing unit"""

    title: str | None = Field(None, min_length=1, max_length=500)
    code: str | None = Field(None, min_length=1, max_length=20)
    description: str | None = None
    year: int | None = Field(None, ge=2020, le=2100)
    semester: Semester | None = None
    status: UnitStatus | None = None
    pedagogy_type: PedagogyType | None = None
    difficulty_level: DifficultyLevel | None = None
    duration_weeks: int | None = Field(None, ge=1, le=52)
    credit_points: int | None = Field(None, ge=1, le=12)
    prerequisites: str | None = None
    learning_hours: int | None = Field(None, ge=0, le=1000)
    unit_metadata: dict[str, Any] | None = None
    generation_context: str | None = None


class UnitResponse(CamelModel):
    """Schema for unit responses"""

    id: str
    title: str
    code: str
    description: str | None
    year: int
    semester: str
    status: str
    pedagogy_type: str
    difficulty_level: str
    duration_weeks: int
    credit_points: int
    prerequisites: str | None
    learning_hours: int | None
    unit_metadata: dict[str, Any] | None
    generation_context: str | None
    owner_id: str
    created_by_id: str
    updated_by_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnitList(CamelModel):
    """Schema for paginated unit list"""

    units: list[UnitResponse]
    total: int
    skip: int
    limit: int
