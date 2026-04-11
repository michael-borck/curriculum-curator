"""
API endpoint for standalone QTI 2.1 quiz export.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.models.quiz_question import (
    QuizQuestion,  # noqa: TC001  # runtime use in type annotation
)
from app.models.weekly_material import WeeklyMaterial
from app.schemas.unit import UnitResponse
from app.services.qti_service import qti_exporter
from app.services.unit_export_data import extract_quiz_nodes, slugify

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/units/{unit_id}/export/qti")
async def export_unit_qti(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Export all quiz questions in a unit as a QTI 2.1 package (.zip).

    Quizzes live inline as ``quizQuestion`` TipTap nodes inside
    ``WeeklyMaterial.content_json``. This used to also query legacy
    ``Content`` rows of type QUIZ, but Content was removed during the
    pre-MVP cleanup — modern quizzes are always inline.
    """
    all_questions: list[QuizQuestion] = []

    # Extract quiz nodes from editor content_json in weekly materials
    materials = (
        db.query(WeeklyMaterial)
        .filter(WeeklyMaterial.unit_id == unit.id)
        .all()
    )
    for mat in materials:
        if mat.content_json:
            all_questions.extend(extract_quiz_nodes(mat.content_json))

    title = f"{unit.code} - Quiz Export"
    buf = qti_exporter.export_qti21_zip(all_questions, title)

    title_slug = slugify(str(unit.title))
    filename = f"{unit.code}_{title_slug}_qti.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
