"""
Course (Unit) schemas for API requests and responses
"""

from pydantic import Field

from app.schemas.base import CamelModel


class CourseBase(CamelModel):
    """Base course schema with common fields"""

    title: str = Field(..., min_length=1, max_length=500)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    year: int = Field(..., ge=2020, le=2100)
    semester: str = Field(...)
    pedagogy_type: str = Field(default="inquiry-based")
    difficulty_level: str = Field(default="intermediate")
    duration_weeks: int = Field(default=12, ge=1, le=52)
    credit_points: int = Field(default=6, ge=0, le=12)


class CourseCreate(CourseBase):
    """Schema for creating a new course"""

    status: str | None = Field(default="draft")


class CourseUpdate(CamelModel):
    """Schema for updating a course - all fields optional"""

    title: str | None = Field(None, min_length=1, max_length=500)
    code: str | None = Field(None, min_length=1, max_length=20)
    description: str | None = None
    year: int | None = Field(None, ge=2020, le=2100)
    semester: str | None = None
    status: str | None = None
    pedagogy_type: str | None = None
    difficulty_level: str | None = None
    duration_weeks: int | None = Field(None, ge=1, le=52)
    credit_points: int | None = Field(None, ge=0, le=12)


class CourseResponse(CourseBase):
    """Schema for course responses"""

    id: str
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CourseListResponse(CamelModel):
    """Schema for paginated course list responses"""

    courses: list[CourseResponse]
    total: int
    skip: int
    limit: int
