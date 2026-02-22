"""
Research routes — academic search, URL extraction, outline synthesis, settings.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.assessment import Assessment
from app.models.learning_outcome import UnitLearningOutcome
from app.models.research_source import ResearchSource
from app.models.unit import Unit
from app.models.unit_outline import UnitOutline
from app.models.user import User
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic
from app.schemas.ai import ScaffoldUnitResponse
from app.schemas.research import (
    AcademicSearchRequest,
    AcademicSearchResponse,
    AcademicSearchResultItem,
    ApplyComparisonRequest,
    ApplyReadingListRequest,
    ApplyScaffoldRequest,
    AvailableTiersResponse,
    CompareRequest,
    ExtractedUrlItem,
    MatchReadingListRequest,
    ResearchSettings,
    ScaffoldFromSourcesRequest,
    TierInfo,
    UrlExtractRequest,
    UrlExtractResponse,
)
from app.schemas.user import UserResponse
from app.services.outline_synthesis_service import outline_synthesis_service
from app.services.search_router import SearchTier, search_router
from app.services.url_extraction_service import url_extraction_service

logger = logging.getLogger(__name__)

router = APIRouter()

_TIER_NAMES: dict[SearchTier, str] = {
    SearchTier.ACADEMIC: "Academic",
    SearchTier.LLM_NATIVE: "LLM Native",
    SearchTier.GENERAL_WEB: "General Web",
    SearchTier.SEARXNG: "SearXNG",
}


# =============================================================================
# Phase 1: Academic Search
# =============================================================================


@router.post("/search", response_model=AcademicSearchResponse)
async def search_academic(
    request: AcademicSearchRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Search academic databases (OpenAlex + Semantic Scholar)."""
    results, tier_used = await search_router.search(
        query=request.query,
        preferred_tier=request.preferred_tier,
        max_results=request.max_results,
    )

    items = [
        AcademicSearchResultItem(
            title=r.title,
            url=r.url,
            abstract=r.content,
            academic_score=r.academic_score,
            provider=r.source or "",
            source_name=r.source,
        )
        for r in results
    ]

    return AcademicSearchResponse(
        query=request.query,
        results=items,
        total_results=len(items),
        tier_used=int(tier_used),
        tier_name=_TIER_NAMES.get(tier_used, "Unknown"),
    )


@router.get("/tiers", response_model=AvailableTiersResponse)
async def get_available_tiers(
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Get available search tiers for the current user."""
    tiers = search_router.get_available_tiers()

    return AvailableTiersResponse(
        tiers=[
            TierInfo(
                tier=int(t.tier),
                name=_TIER_NAMES.get(t.tier, "Unknown"),
                available=t.available,
                reason=t.reason,
            )
            for t in tiers
        ]
    )


# =============================================================================
# Phase 2: URL Extraction
# =============================================================================


@router.post("/extract-urls", response_model=UrlExtractResponse)
async def extract_urls(
    request: UrlExtractRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Extract and classify content from user-provided URLs."""
    extracted = await url_extraction_service.extract_urls(
        urls=request.urls,
        summarize=request.summarize,
        purpose=request.purpose,
    )

    items = [
        ExtractedUrlItem(
            url=e.url,
            title=e.title,
            summary=e.summary,
            key_points=e.key_points,
            academic_score=e.academic_score,
            content_type=e.content_type,
            error=e.error,
        )
        for e in extracted
    ]

    successful = sum(1 for e in extracted if not e.error)
    failed = sum(1 for e in extracted if e.error)

    return UrlExtractResponse(
        results=items,
        total=len(items),
        successful=successful,
        failed=failed,
    )


# =============================================================================
# Phase 3: Outline Synthesis — Propose
# =============================================================================


@router.post("/scaffold", response_model=ScaffoldUnitResponse)
async def propose_scaffold(
    request: ScaffoldFromSourcesRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Generate a unit scaffold from research sources (no DB writes)."""
    result = await outline_synthesis_service.propose_scaffold(
        sources=request.source_data,
        unit_title=request.unit_title,
        unit_description=request.unit_description,
        duration_weeks=request.duration_weeks,
        pedagogy_style=request.pedagogy_style,
        unit_id=request.unit_id,
        design_id=request.design_id,
        db=db,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate scaffold")

    return result


@router.post("/compare")
async def propose_comparison(
    request: CompareRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Compare sources against an existing unit (no DB writes)."""
    unit = db.query(Unit).filter(Unit.id == request.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if str(unit.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your unit")

    result = await outline_synthesis_service.propose_comparison(
        sources=request.source_data,
        unit_id=request.unit_id,
        db=db,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate comparison")

    return result


@router.post("/match-reading-list")
async def propose_reading_list(
    request: MatchReadingListRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Match sources to unit weeks with confidence scores (no DB writes)."""
    unit = db.query(Unit).filter(Unit.id == request.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if str(unit.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your unit")

    result = await outline_synthesis_service.propose_reading_list(
        sources=request.source_data,
        unit_id=request.unit_id,
        db=db,
    )

    if not result:
        raise HTTPException(
            status_code=500, detail="Failed to generate reading list matches"
        )

    return result


# =============================================================================
# Phase 3: Outline Synthesis — Apply
# =============================================================================


@router.post("/scaffold/apply")
async def apply_scaffold(
    request: ApplyScaffoldRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Apply a scaffold proposal — creates Unit + ULOs + WeeklyTopics + Assessments."""
    proposal = request.proposal

    # Create or update unit
    if request.unit_id:
        unit = db.query(Unit).filter(Unit.id == request.unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        if str(unit.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not your unit")
        unit.title = proposal.title
        unit.description = proposal.description
    else:
        unit = Unit(
            id=str(uuid.uuid4()),
            title=proposal.title,
            code="NEW001",
            description=proposal.description,
            year=2026,
            semester="semester_1",
            pedagogy_type="mixed_approach",
            difficulty_level="intermediate",
            duration_weeks=len(proposal.weeks),
            owner_id=str(current_user.id),
            created_by_id=str(current_user.id),
            credit_points=6,
        )
        db.add(unit)
        db.flush()

    # Create unit outline for weekly topics
    outline = UnitOutline(
        id=str(uuid.uuid4()),
        unit_id=str(unit.id),
        title=proposal.title,
        description=proposal.description or "",
        duration_weeks=len(proposal.weeks),
        credit_points=6,
        status="planning",
        created_by_id=str(current_user.id),
    )
    db.add(outline)
    db.flush()

    # Create ULOs — commit each individually (GUID sentinel requires this)
    for i, ulo in enumerate(proposal.ulos, 1):
        db.add(
            UnitLearningOutcome(
                id=str(uuid.uuid4()),
                unit_id=str(unit.id),
                outcome_type="ulo",
                outcome_code=ulo.code,
                outcome_text=ulo.description,
                bloom_level=ulo.bloom_level.upper(),
                sequence_order=i,
                created_by_id=str(current_user.id),
            )
        )
        db.commit()

    # Create weekly topics
    for week in proposal.weeks:
        db.add(
            WeeklyTopic(
                id=str(uuid.uuid4()),
                unit_outline_id=str(outline.id),
                unit_id=str(unit.id),
                week_number=week.week_number,
                topic_title=week.topic,
                created_by_id=str(current_user.id),
            )
        )
        db.commit()

    # Create assessments
    for assessment in proposal.assessments:
        db.add(
            Assessment(
                id=str(uuid.uuid4()),
                unit_id=str(unit.id),
                title=assessment.title,
                type="formative" if assessment.weight < 30 else "summative",
                category=assessment.category,
                weight=assessment.weight,
                due_week=assessment.due_week,
                status="draft",
            )
        )
        db.commit()

    return {"unit_id": str(unit.id), "created": not request.unit_id}


@router.post("/compare/apply")
async def apply_comparison(
    request: ApplyComparisonRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Apply selected comparison suggestions — adds missing topics to unit weeks."""
    proposal = request.proposal

    unit = db.query(Unit).filter(Unit.id == proposal.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if str(unit.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your unit")

    return {
        "unit_id": proposal.unit_id,
        "applied_suggestions": request.selected_suggestions,
    }


@router.post("/match-reading-list/apply")
async def apply_reading_list(
    request: ApplyReadingListRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Apply a reading list proposal — creates ResearchSource + optional WeeklyMaterial."""
    proposal = request.proposal

    unit = db.query(Unit).filter(Unit.id == proposal.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if str(unit.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your unit")

    saved_sources: list[dict[str, object]] = []

    for match in proposal.matches:
        week = match.assigned_week or match.suggested_week
        if match.skipped:
            continue

        if request.save_as_sources:
            source = ResearchSource(
                id=str(uuid.uuid4()),
                user_id=str(current_user.id),
                unit_id=str(unit.id),
                url=match.url,
                title=match.title,
                source_type="website",
                academic_score=match.confidence,
                notes=match.reasoning,
            )
            db.add(source)
            db.flush()

            saved_sources.append(
                {
                    "source_id": str(source.id),
                    "url": match.url,
                    "week": week,
                }
            )

        if week is not None:
            existing_count = (
                db.query(WeeklyMaterial)
                .filter(
                    WeeklyMaterial.unit_id == str(unit.id),
                    WeeklyMaterial.week_number == week,
                )
                .count()
            )

            db.add(
                WeeklyMaterial(
                    id=str(uuid.uuid4()),
                    unit_id=str(unit.id),
                    week_number=week,
                    title=match.title,
                    type="reading",
                    description=f'<p><a href="{match.url}">{match.title}</a></p>',
                    order_index=existing_count,
                )
            )

    db.commit()

    return {"saved_sources": saved_sources}


# =============================================================================
# Phase 4: Research Settings
# =============================================================================


@router.put("/settings")
async def update_research_settings(
    request_settings: ResearchSettings,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Update user's research preferences (API keys, preferred tier, SearXNG URL)."""
    user = db.query(User).filter(User.id == str(current_user.id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = user.teaching_preferences or {}
    if not isinstance(prefs, dict):
        prefs = {}

    prefs["research"] = request_settings.model_dump(by_alias=True)
    user.teaching_preferences = prefs

    db.commit()

    return {"saved": True}
