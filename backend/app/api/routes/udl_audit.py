"""API routes for UDL Audit — checkpoint self-assessment."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.udl_audit import (
    UDLAuditAISuggestionsResponse,
    UDLAuditBatchUpsert,
    UDLAuditResponseItem,
    UDLAuditSummary,
)
from app.services.udl_audit_service import udl_audit_service

router = APIRouter()


@router.get("/profiles")
async def list_profiles() -> Any:
    """Return all available audit profiles."""
    return udl_audit_service.list_profiles()


@router.get("/guidelines")
async def list_guidelines() -> Any:
    """Return full CAST UDL 3.0 guidelines structure."""
    return udl_audit_service.list_guidelines()


@router.get(
    "/units/{unit_id}/responses",
    response_model=list[UDLAuditResponseItem],
)
async def get_unit_responses(
    unit_id: UUID,
    profile_id: str = Query(...),
    assessment_id: str = Query(default=""),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all saved audit responses for a unit+profile+scope."""
    return udl_audit_service.get_responses(db, unit_id, profile_id, assessment_id)


@router.get(
    "/units/{unit_id}/summary",
    response_model=UDLAuditSummary,
)
async def get_unit_summary(
    unit_id: UUID,
    profile_id: str = Query(...),
    assessment_id: str = Query(default=""),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get coverage summary for a unit+profile+scope."""
    return udl_audit_service.get_summary(db, unit_id, profile_id, assessment_id)


@router.put(
    "/units/{unit_id}/responses",
    response_model=list[UDLAuditResponseItem],
)
async def upsert_unit_responses(
    unit_id: UUID,
    data: UDLAuditBatchUpsert,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Upsert audit responses for a unit+profile+scope."""
    return udl_audit_service.upsert_responses(db, unit_id, data)


@router.post(
    "/units/{unit_id}/ai-suggestions",
    response_model=UDLAuditAISuggestionsResponse,
)
async def get_ai_suggestions(
    unit_id: UUID,
    profile_id: str = Query(...),
    assessment_id: str = Query(default=""),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Generate AI improvement suggestions for needs_work checkpoints."""
    return await udl_audit_service.get_ai_suggestions(
        db=db,
        unit_id=unit_id,
        profile_id=profile_id,
        assessment_id=assessment_id,
        user=current_user,
        db_for_llm=db,
    )
