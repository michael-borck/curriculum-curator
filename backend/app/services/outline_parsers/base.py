"""
Abstract base class and data models for outline parsers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Extracted data models
# ---------------------------------------------------------------------------


class ExtractedULO(BaseModel):
    code: str = ""
    description: str
    bloom_level: str = "understand"


class ExtractedWeek(BaseModel):
    week_number: int
    topic: str
    activities: list[str] = Field(default_factory=list)
    readings: list[str] = Field(default_factory=list)


class ExtractedAssessment(BaseModel):
    title: str
    category: str = "assignment"
    weight: float = 0.0
    due_week: int | None = None
    description: str = ""


class ExtractedTextbook(BaseModel):
    title: str
    authors: str = ""
    isbn: str = ""
    required: bool = True


class ExtractedSnippet(BaseModel):
    heading: str
    content: str


class OutlineParseResult(BaseModel):
    """Complete extraction result from an outline parser."""

    # Unit metadata
    unit_code: str | None = None
    unit_title: str | None = None
    description: str | None = None
    credit_points: int | None = None
    duration_weeks: int | None = None
    year: int | None = None
    semester: str | None = None
    prerequisites: str | None = None
    delivery_mode: str | None = None
    teaching_pattern: str | None = None

    # Structured data
    learning_outcomes: list[ExtractedULO] = Field(default_factory=list)
    weekly_schedule: list[ExtractedWeek] = Field(default_factory=list)
    assessments: list[ExtractedAssessment] = Field(default_factory=list)
    textbooks: list[ExtractedTextbook] = Field(default_factory=list)

    # Unmapped content
    supplementary_info: list[ExtractedSnippet] = Field(default_factory=list)

    # Metadata
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    parser_used: str = "generic"
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Abstract parser
# ---------------------------------------------------------------------------


class OutlineParser(ABC):
    """Base class for all outline parsers."""

    name: ClassVar[str] = "base"
    display_name: ClassVar[str] = "Base Parser"
    description: ClassVar[str] = ""
    supported_formats: ClassVar[list[str]] = ["pdf", "docx", "txt"]

    @abstractmethod
    async def parse(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> OutlineParseResult:
        """Parse a document and return structured extraction."""
        ...
