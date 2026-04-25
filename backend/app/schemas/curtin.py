"""Pydantic schemas for Curtin integration endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from app.schemas.base import CamelModel


class CurtinSettings(CamelModel):
    curtin_username: str = ""
    curtin_password: str = ""
    litec_url: str = "https://litec.curtin.edu.au/outline.cfm"
    blackboard_url: str = "https://lms.curtin.edu.au/"
    campus: str = "Bentley Perth Campus"


class CurtinOutlineRequest(CamelModel):
    unit_code: str


class CurtinCourseBuildRequest(CamelModel):
    course_name: str


class CurtinJobResponse(CamelModel):
    id: str
    course_name: str
    status: str
    triggered_at: datetime
    error_message: str | None = None

    model_config: ClassVar = {"from_attributes": True}
