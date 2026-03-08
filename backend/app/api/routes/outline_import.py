"""
API routes for unit outline import (ADR-063).

Endpoints:
    GET  /parsers  — list available parsers
    POST /parse    — upload + parse a document
    POST /apply    — create a unit from reviewed extraction
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api import deps
from app.models.assessment import Assessment
from app.models.learning_outcome import UnitLearningOutcome
from app.models.unit import Unit
from app.models.unit_outline import UnitOutline
from app.models.user import User
from app.models.weekly_topic import WeeklyTopic
from app.schemas.outline_import import (
    OutlineApplyRequest,
    OutlineAssessment,
    OutlineParseResponse,
    OutlineSnippet,
    OutlineTextbook,
    OutlineULO,
    OutlineWeek,
    ParserInfo,
)
from app.services.outline_parsers import get_parser, list_parsers

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


# ---------------------------------------------------------------------------
# GET /parsers
# ---------------------------------------------------------------------------


@router.get("/parsers", response_model=list[ParserInfo])
async def get_available_parsers(
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> list[dict[str, object]]:
    """Return metadata for all registered outline parsers."""
    return list_parsers()


# ---------------------------------------------------------------------------
# POST /parse
# ---------------------------------------------------------------------------


@router.post("/parse", response_model=OutlineParseResponse)
async def parse_outline(
    file: UploadFile = File(...),
    parser_id: str = Form("generic"),
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> OutlineParseResponse:
    """Upload and parse a unit outline document."""

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(content) // 1024 // 1024}MB). Maximum is {_MAX_FILE_SIZE // 1024 // 1024}MB.",
        )

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Get parser
    try:
        parser = get_parser(parser_id)
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown parser: {parser_id}. Use GET /parsers to list available parsers.",
        )

    # Look up user for LLM key resolution
    user_obj = db.query(User).filter(User.id == str(current_user.id)).first()
    user_context = {"user": user_obj, "db": db}

    result = await parser.parse(
        file_content=content,
        filename=file.filename,
        file_type=ext,
        user_context=user_context,
    )

    return OutlineParseResponse(
        unit_code=result.unit_code,
        unit_title=result.unit_title,
        description=result.description,
        credit_points=result.credit_points,
        duration_weeks=result.duration_weeks,
        year=result.year,
        semester=result.semester,
        prerequisites=result.prerequisites,
        delivery_mode=result.delivery_mode,
        teaching_pattern=result.teaching_pattern,
        learning_outcomes=[
            OutlineULO(code=u.code, description=u.description, bloom_level=u.bloom_level)
            for u in result.learning_outcomes
        ],
        weekly_schedule=[
            OutlineWeek(
                week_number=w.week_number,
                topic=w.topic,
                activities=w.activities,
                readings=w.readings,
            )
            for w in result.weekly_schedule
        ],
        assessments=[
            OutlineAssessment(
                title=a.title,
                category=a.category,
                weight=a.weight,
                due_week=a.due_week,
                description=a.description,
            )
            for a in result.assessments
        ],
        textbooks=[
            OutlineTextbook(
                title=t.title, authors=t.authors, isbn=t.isbn, required=t.required
            )
            for t in result.textbooks
        ],
        supplementary_info=[
            OutlineSnippet(heading=s.heading, content=s.content)
            for s in result.supplementary_info
        ],
        confidence=result.confidence,
        parser_used=result.parser_used,
        warnings=result.warnings,
    )


# ---------------------------------------------------------------------------
# POST /apply
# ---------------------------------------------------------------------------


@router.post("/apply")
async def apply_outline(
    request: OutlineApplyRequest,
    current_user: UserResponse = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> dict[str, object]:
    """Create a unit from user-reviewed outline extraction."""

    now = datetime.now(UTC)

    # Check for duplicate code+semester+year
    query = db.query(Unit).filter(
        Unit.code == request.unit_code,
        Unit.owner_id == str(current_user.id),
    )
    if request.year:
        query = query.filter(Unit.year == request.year)
    if request.semester:
        query = query.filter(Unit.semester == request.semester)
    existing = query.first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A unit with code {request.unit_code} already exists for this period.",
        )

    # --- Create Unit ---
    unit_metadata: dict[str, object] = {}
    if request.textbooks:
        unit_metadata["textbooks"] = [
            {"title": t.title, "authors": t.authors, "isbn": t.isbn, "required": t.required}
            for t in request.textbooks
        ]
    kept_supplementary = [s for s in request.supplementary_info if s.keep]
    if kept_supplementary:
        unit_metadata["supplementary_info"] = [
            {"heading": s.heading, "content": s.content} for s in kept_supplementary
        ]
    unit_metadata["outline_import"] = {
        "parser_used": request.parser_used,
        "imported_at": now.isoformat(),
    }

    unit = Unit(
        id=str(uuid.uuid4()),
        title=request.unit_title,
        code=request.unit_code,
        description=request.description,
        year=request.year or now.year,
        semester=request.semester or "semester_1",
        pedagogy_type=request.pedagogy_type,
        difficulty_level="intermediate",
        duration_weeks=request.duration_weeks,
        credit_points=request.credit_points,
        prerequisites=request.prerequisites or None,
        owner_id=str(current_user.id),
        created_by_id=str(current_user.id),
        unit_metadata=unit_metadata if unit_metadata else None,
    )
    db.add(unit)
    db.flush()

    # --- Create UnitOutline ---
    outline = UnitOutline(
        id=str(uuid.uuid4()),
        unit_id=str(unit.id),
        title=request.unit_title,
        description=request.description or "",
        duration_weeks=request.duration_weeks,
        credit_points=request.credit_points,
        delivery_mode=request.delivery_mode or None,
        teaching_pattern=request.teaching_pattern or None,
        prerequisites=request.prerequisites or None,
        status="planning",
        created_by_id=str(current_user.id),
    )
    db.add(outline)
    db.flush()

    # --- Create ULOs (commit each individually — GUID sentinel constraint) ---
    for i, ulo in enumerate(request.learning_outcomes, 1):
        db.add(
            UnitLearningOutcome(
                id=str(uuid.uuid4()),
                unit_id=str(unit.id),
                outcome_type="ulo",
                outcome_code=ulo.code or f"ULO{i}",
                outcome_text=ulo.description,
                bloom_level=ulo.bloom_level.upper(),
                sequence_order=i,
                created_by_id=str(current_user.id),
            )
        )
        db.commit()

    # --- Create WeeklyTopics ---
    for week in request.weekly_schedule:
        db.add(
            WeeklyTopic(
                id=str(uuid.uuid4()),
                unit_outline_id=str(outline.id),
                unit_id=str(unit.id),
                week_number=week.week_number,
                topic_title=week.topic,
                learning_objectives=", ".join(week.activities) if week.activities else None,
                created_by_id=str(current_user.id),
            )
        )
        db.commit()

    # --- Create Assessments ---
    for assessment in request.assessments:
        db.add(
            Assessment(
                id=str(uuid.uuid4()),
                unit_id=str(unit.id),
                title=assessment.title,
                type="formative" if assessment.weight < 30 else "summative",
                category=assessment.category,
                weight=assessment.weight,
                due_week=assessment.due_week,
                description=assessment.description or None,
                status="draft",
            )
        )
        db.commit()

    return {
        "unit_id": str(unit.id),
        "title": unit.title,
        "code": unit.code,
        "ulos_created": len(request.learning_outcomes),
        "weeks_created": len(request.weekly_schedule),
        "assessments_created": len(request.assessments),
    }
