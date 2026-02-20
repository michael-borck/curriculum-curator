"""
IMSCC import/export schemas (Phase 2 import prep).
"""

from pydantic import Field

from app.schemas.base import CamelModel


class IMSCCResourcePreview(CamelModel):
    """Preview of a single resource within an IMSCC package."""

    identifier: str
    title: str
    resource_type: str  # "webcontent", "assessment", etc.
    file_path: str
    content_preview: str | None = None  # First ~200 chars of text content


class IMSCCWeekPreview(CamelModel):
    """Preview of a week's content from an IMSCC package."""

    week_number: int
    title: str
    materials: list[IMSCCResourcePreview] = Field(default_factory=list)


class IMSCCPreview(CamelModel):
    """Full preview of an IMSCC package before import."""

    title: str
    description: str | None = None
    has_curator_metadata: bool = False
    weeks: list[IMSCCWeekPreview] = Field(default_factory=list)
    assessments: list[IMSCCResourcePreview] = Field(default_factory=list)
    unmatched_resources: list[IMSCCResourcePreview] = Field(default_factory=list)
