"""
API endpoints for H5P Question Set export.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.models.content import Content
from app.models.enums import ContentType
from app.models.quiz_question import QuizQuestion
from app.models.weekly_material import WeeklyMaterial
from app.schemas.unit import UnitResponse
from app.services.h5p_branching_service import h5p_branching_builder
from app.services.h5p_course_presentation import h5p_course_presentation_builder
from app.services.h5p_service import h5p_builder
from app.services.slide_splitter import has_slide_breaks
from app.services.unit_export_data import extract_branching_cards, extract_quiz_nodes, slugify

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/units/{unit_id}/export/h5p")
async def export_unit_h5p(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Export all quiz questions in a unit as H5P Question Set (.h5p)."""
    all_questions = _gather_all_questions(str(unit.id), db)

    if not all_questions:
        raise HTTPException(status_code=404, detail="No quiz questions found in this unit")

    title = f"{unit.code} - Interactive Quiz"
    buf = h5p_builder.build(all_questions, title)

    title_slug = slugify(str(unit.title))
    filename = f"{unit.code}_{title_slug}_quiz.h5p"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/materials/{material_id}/export/h5p")
async def export_material_h5p(
    material_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Export quiz questions from a single material as H5P Question Set."""
    material = db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    questions: list[QuizQuestion] = []
    if material.content_json:
        questions = extract_quiz_nodes(material.content_json)

    if not questions:
        raise HTTPException(status_code=404, detail="No quiz questions found in this material")

    title = f"{material.title} - Interactive Quiz"
    buf = h5p_builder.build(questions, title)

    title_slug = slugify(str(material.title))
    filename = f"{title_slug}_quiz.h5p"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/materials/{material_id}/export/h5p-slides")
async def export_material_h5p_slides(
    material_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Export a material as H5P Course Presentation (.h5p) using slide breaks."""
    material = db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if not material.content_json or not has_slide_breaks(material.content_json):
        raise HTTPException(status_code=404, detail="No slide breaks found in this material")

    title = f"{material.title} - Slides"
    buf = h5p_course_presentation_builder.build(material.content_json, title)

    title_slug = slugify(str(material.title))
    filename = f"{title_slug}_slides.h5p"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/materials/{material_id}/export/h5p-branching")
async def export_material_h5p_branching(
    material_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Export branching cards from a material as H5P Branching Scenario."""
    material = db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    cards: list[dict[str, Any]] = []
    if material.content_json:
        cards = extract_branching_cards(material.content_json)

    if not cards:
        raise HTTPException(status_code=404, detail="No branching cards found in this material")

    title = f"{material.title} - Branching Scenario"
    buf = h5p_branching_builder.build(cards, title)

    title_slug = slugify(str(material.title))
    filename = f"{title_slug}_branching.h5p"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def _gather_all_questions(unit_id: str, db: Session) -> list[QuizQuestion]:
    """Gather quiz questions from both DB Content rows and editor content_json."""
    all_questions: list[QuizQuestion] = []

    # DB-stored quiz questions
    quiz_contents = (
        db.query(Content)
        .filter(Content.unit_id == unit_id, Content.type == ContentType.QUIZ.value)
        .all()
    )
    for content in quiz_contents:
        questions = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.content_id == content.id)
            .order_by(QuizQuestion.order_index)
            .all()
        )
        all_questions.extend(questions)

    # Editor content_json quiz nodes
    materials = db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
    for mat in materials:
        if mat.content_json:
            all_questions.extend(extract_quiz_nodes(mat.content_json))

    return all_questions
