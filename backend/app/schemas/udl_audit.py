"""Pydantic schemas for UDL Audit responses and guidelines."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import CamelModel

UDLAuditResponseValue = Literal["doing_well", "needs_work", "not_applicable", "skipped"]


class UDLCheckpointEntry(CamelModel):
    """A single checkpoint result within an audit response list."""

    checkpoint_id: str
    response: UDLAuditResponseValue = "skipped"
    notes: str | None = None


class UDLAuditBatchUpsert(CamelModel):
    """Batch upsert request — replace all responses for a unit+profile+scope."""

    profile_id: str
    assessment_id: str = ""  # "" = unit-level
    responses: list[UDLCheckpointEntry] = Field(default_factory=list)


class UDLAuditResponseItem(CamelModel):
    """Single persisted audit response (API output)."""

    id: str
    unit_id: str
    profile_id: str
    checkpoint_id: str
    assessment_id: str
    response: UDLAuditResponseValue
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class UDLAuditSummary(CamelModel):
    """Coverage summary for a unit+profile+scope."""

    unit_id: str
    profile_id: str
    assessment_id: str
    total_checkpoints: int
    doing_well: int
    needs_work: int
    not_applicable: int
    skipped: int


class UDLAuditAISuggestion(CamelModel):
    """One AI-generated improvement suggestion for a needs_work checkpoint."""

    checkpoint_id: str
    checkpoint_name: str
    suggestion: str


class UDLAuditAISuggestionsResponse(CamelModel):
    """Response from the AI suggestions endpoint."""

    unit_id: str
    profile_id: str
    assessment_id: str
    suggestions: list[UDLAuditAISuggestion]
    generated_at: datetime
