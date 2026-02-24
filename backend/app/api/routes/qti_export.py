"""
API endpoint for standalone QTI 2.1 quiz export.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_unit
from app.models.content import Content
from app.models.enums import ContentType
from app.models.quiz_question import QuizQuestion
from app.schemas.unit import UnitResponse
from app.services.qti_service import qti_exporter
from app.services.unit_export_data import slugify

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/units/{unit_id}/export/qti")
async def export_unit_qti(
    unit: Annotated[UnitResponse, Depends(get_user_unit)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Export all quiz questions in a unit as a QTI 2.1 package (.zip)."""
    # Gather all quiz questions for this unit
    quiz_contents = (
        db.query(Content)
        .filter(Content.unit_id == unit.id, Content.type == ContentType.QUIZ.value)
        .all()
    )

    all_questions: list[QuizQuestion] = []
    for content in quiz_contents:
        questions = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.content_id == content.id)
            .order_by(QuizQuestion.order_index)
            .all()
        )
        all_questions.extend(questions)

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
