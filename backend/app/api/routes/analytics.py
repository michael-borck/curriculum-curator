"""
API endpoints for analytics and reporting
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.analytics import (
    AlignmentReport,
    BatchDashboardMetricsResponse,
    BatchQualityResponse,
    CompletionReport,
    ProgressReport,
    QualityScore,
    SnapshotComparison,
    SnapshotCreate,
    SnapshotListItem,
    SnapshotResponse,
    UnitOverview,
    WeeklyWorkload,
    WeekQualityScore,
)
from app.schemas.udl import UDLSuggestionsResponse, UDLUnitScore, UDLWeekScore
from app.services.analytics_service import analytics_service
from app.services.snapshot_service import snapshot_service
from app.services.udl_service import udl_service

logger = logging.getLogger(__name__)

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
    source: str = Query("rules", pattern="^(rules|llm)$"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get recommendations for unit improvement"""
    return await analytics_service.get_recommendations(
        db=db,
        unit_id=unit_id,
        source=source,
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


@router.get("/units/{unit_id}/quality-score", response_model=QualityScore)
async def get_quality_score(
    unit_id: UUID,
    total_weeks: int = Query(12, ge=1, le=52),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Calculate quality score for a unit with 6 dimensions"""
    # Auto-snapshot side-effect (best-effort, don't break the response)
    try:
        await snapshot_service.maybe_auto_snapshot(
            db=db, unit_id=unit_id, user_id=str(current_user.id)
        )
    except Exception:
        logger.debug("Auto-snapshot failed for unit %s", unit_id, exc_info=True)

    prefs = (
        (current_user.teaching_preferences or {})
        if current_user.teaching_preferences
        else {}
    )
    quality_config = prefs.get("qualityRating", {})
    rating_method = quality_config.get("method", "weighted_average")
    return await analytics_service.calculate_quality_score(
        db=db,
        unit_id=unit_id,
        rating_method=rating_method,
        rating_config=quality_config,
        total_weeks=total_weeks,
    )


@router.get(
    "/units/{unit_id}/weekly-quality",
    response_model=list[WeekQualityScore],
)
async def get_weekly_quality(
    unit_id: UUID,
    total_weeks: int = Query(12, ge=1, le=52),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get per-week quality scores"""
    return await analytics_service.calculate_weekly_quality(
        db=db,
        unit_id=unit_id,
        total_weeks=total_weeks,
    )


@router.post("/units/batch-quality-scores", response_model=BatchQualityResponse)
async def get_batch_quality_scores(
    unit_ids: list[str] = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get star ratings for multiple units"""
    uuids = [UUID(uid) for uid in unit_ids]
    scores = await analytics_service.calculate_batch_quality_scores(
        db=db,
        unit_ids=uuids,
    )
    return {"scores": scores}


@router.post(
    "/units/batch-dashboard-metrics",
    response_model=BatchDashboardMetricsResponse,
)
async def get_batch_dashboard_metrics(
    unit_ids: list[str] = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get quality stars, UDL stars, and weeks with content for multiple units"""
    uuids = [UUID(uid) for uid in unit_ids]
    metrics = await analytics_service.calculate_batch_dashboard_metrics(
        db=db,
        unit_ids=uuids,
    )
    return {"metrics": metrics}


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


@router.get("/units/{unit_id}/udl-score", response_model=UDLUnitScore)
async def get_udl_score(
    unit_id: UUID,
    total_weeks: int = Query(12, ge=1, le=52),
    target_level: str = Query("university"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Calculate UDL inclusivity score for a unit"""
    # Auto-snapshot side-effect (best-effort)
    try:
        await snapshot_service.maybe_auto_snapshot(
            db=db, unit_id=unit_id, user_id=str(current_user.id)
        )
    except Exception:
        logger.debug("Auto-snapshot failed for unit %s", unit_id, exc_info=True)

    return await udl_service.calculate_unit_udl(
        db=db,
        unit_id=unit_id,
        total_weeks=total_weeks,
        target_level=target_level,
    )


@router.get(
    "/units/{unit_id}/udl-weekly",
    response_model=list[UDLWeekScore],
)
async def get_udl_weekly(
    unit_id: UUID,
    total_weeks: int = Query(12, ge=1, le=52),
    target_level: str = Query("university"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get per-week UDL breakdown"""
    return await udl_service.calculate_weekly_udl(
        db=db,
        unit_id=unit_id,
        total_weeks=total_weeks,
        target_level=target_level,
    )


@router.get(
    "/units/{unit_id}/udl-suggestions",
    response_model=UDLSuggestionsResponse,
)
async def get_udl_suggestions(
    unit_id: UUID,
    total_weeks: int = Query(12, ge=1, le=52),
    target_level: str = Query("university"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get UDL improvement suggestions"""
    return await udl_service.get_udl_suggestions(
        db=db,
        unit_id=unit_id,
        total_weeks=total_weeks,
        target_level=target_level,
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


# ============= Snapshot Endpoints =============


@router.get(
    "/units/{unit_id}/snapshots",
    response_model=list[SnapshotListItem],
)
async def list_snapshots(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """List all snapshots for a unit (newest first)"""
    return snapshot_service.list_snapshots(db=db, unit_id=unit_id)


@router.post(
    "/units/{unit_id}/snapshots",
    response_model=SnapshotResponse,
)
async def create_snapshot(
    unit_id: UUID,
    body: SnapshotCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a manual snapshot with optional label"""
    return await snapshot_service.create_snapshot(
        db=db,
        unit_id=unit_id,
        user_id=str(current_user.id),
        label=body.label,
        is_auto=False,
    )


@router.get(
    "/units/{unit_id}/snapshots/compare",
    response_model=SnapshotComparison,
)
async def compare_snapshots(
    unit_id: UUID,
    a: str = Query(..., description="Snapshot A ID"),
    b: str = Query(..., description='Snapshot B ID or "current"'),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Compare two snapshots. Pass b=current for live calculation."""
    try:
        return await snapshot_service.compare_snapshots(
            db=db,
            unit_id=unit_id,
            snapshot_a_id=a,
            snapshot_b_id=b,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/units/{unit_id}/snapshots/{snapshot_id}",
    response_model=SnapshotResponse,
)
async def get_snapshot(
    unit_id: UUID,
    snapshot_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a single snapshot"""
    result = snapshot_service.get_snapshot(db=db, snapshot_id=snapshot_id)
    if not result:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return result


@router.delete("/units/{unit_id}/snapshots/{snapshot_id}")
async def delete_snapshot(
    unit_id: UUID,
    snapshot_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete a snapshot"""
    deleted = snapshot_service.delete_snapshot(db=db, snapshot_id=snapshot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"detail": "Snapshot deleted"}
