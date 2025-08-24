"""
API endpoints for analytics and reporting
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.analytics import (
    AlignmentReport,
    CompletionReport,
    ProgressReport,
    UnitOverview,
    WeeklyWorkload,
)
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get("/units/{unit_id}/overview", response_model=UnitOverview)
async def get_unit_overview(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get comprehensive overview of a unit"""
    return await analytics_service.get_unit_overview(
        db=db,
        unit_id=unit_id,
    )


@router.get("/units/{unit_id}/progress", response_model=ProgressReport)
async def get_unit_progress(
    unit_id: UUID,
    include_details: bool = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get progress report for a unit"""
    return await analytics_service.get_unit_progress(
        db=db,
        unit_id=unit_id,
        include_details=include_details,
    )


@router.get("/units/{unit_id}/completion", response_model=CompletionReport)
async def get_completion_report(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get completion status for all unit components"""
    return await analytics_service.get_completion_report(
        db=db,
        unit_id=unit_id,
    )


@router.get("/units/{unit_id}/alignment", response_model=AlignmentReport)
async def get_alignment_report(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get learning outcome alignment report"""
    return await analytics_service.get_alignment_report(
        db=db,
        unit_id=unit_id,
    )


@router.get("/units/{unit_id}/workload", response_model=list[WeeklyWorkload])
async def get_weekly_workload(
    unit_id: UUID,
    start_week: int = Query(1, ge=1, le=52),
    end_week: int = Query(52, ge=1, le=52),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get weekly workload analysis"""
    return await analytics_service.get_weekly_workload(
        db=db,
        unit_id=unit_id,
        start_week=start_week,
        end_week=end_week,
    )


@router.get("/units/{unit_id}/recommendations")
async def get_recommendations(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get AI-generated recommendations for unit improvement"""
    return await analytics_service.get_recommendations(
        db=db,
        unit_id=unit_id,
    )


@router.get("/units/{unit_id}/export")
async def export_unit_data(
    unit_id: UUID,
    export_format: str = Query("json", pattern="^(json|csv|pdf)$", alias="format"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Export unit data in various formats"""
    return await analytics_service.export_unit_data(
        db=db,
        unit_id=unit_id,
        export_format=export_format,
    )


@router.get("/units/{unit_id}/quality-score")
async def get_quality_score(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Calculate quality score for a unit"""
    return await analytics_service.calculate_quality_score(
        db=db,
        unit_id=unit_id,
    )


@router.get("/units/{unit_id}/validation")
async def validate_unit(
    unit_id: UUID,
    strict: bool = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Validate unit structure and content"""
    return await analytics_service.validate_unit(
        db=db,
        unit_id=unit_id,
        strict_mode=strict,
    )


@router.get("/units/{unit_id}/statistics")
async def get_unit_statistics(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get detailed statistics for a unit"""
    return await analytics_service.get_unit_statistics(
        db=db,
        unit_id=unit_id,
    )
