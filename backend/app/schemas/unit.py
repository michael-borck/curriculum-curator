"""
Pydantic schemas for Unit (Australian university subject)
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.base import CamelModel
from app.schemas.content import ContentType


# Define enums here instead of importing from models
class UnitStatus(str, Enum):
    """Unit status"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Semester(str, Enum):
    """Australian semester"""

    SEMESTER_1 = "semester_1"
    SEMESTER_2 = "semester_2"
    SUMMER = "summer"
    WINTER = "winter"


class PedagogyType(str, Enum):
    """Teaching pedagogy types"""

    INQUIRY_BASED = "inquiry-based"
    PROJECT_BASED = "project-based"
    TRADITIONAL = "traditional"
    COLLABORATIVE = "collaborative"
    PROBLEM_BASED = "problem-based"
    EXPERIENTIAL = "experiential"
    COMPETENCY_BASED = "competency-based"


class DifficultyLevel(str, Enum):
    """Unit difficulty levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class UnitCreate(CamelModel):
    """Schema for creating a new unit"""

    title: str = Field(..., min_length=1, max_length=500)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    year: int | None = Field(None, ge=2020, le=2100)
    semester: Semester | None = None
    pedagogy_type: PedagogyType = PedagogyType.INQUIRY_BASED
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    duration_weeks: int = Field(12, ge=1, le=52)


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


class UnitResponse(CamelModel):
    """Schema for unit responses"""

    id: str
    title: str
    code: str
    description: str | None = None
    owner_id: str
    status: str
    pedagogy_type: str
    difficulty_level: str
    year: int | None = None
    semester: str | None = None
    duration_weeks: int
    unit_metadata: dict[str, Any] | None = None
    created_at: datetime | str
    updated_at: datetime | str | None = None


class QuickCreateRequest(CamelModel):
    """Schema for quick-creating content with an auto-generated unit"""

    content_type: ContentType
    title: str | None = Field(None, max_length=500)


class QuickCreateResponse(CamelModel):
    """Response from quick-create"""

    unit_id: str
    content_id: str
    unit_title: str
    content_title: str
    content_type: str


class UnitList(CamelModel):
    """Schema for paginated unit list"""

    units: list[UnitResponse]
    total: int
