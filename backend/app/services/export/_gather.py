"""Shared data-gathering helpers for export adapters.

These pull content out of WeeklyMaterial rows so individual adapters don't each
re-implement the query + extraction loop (the leak that used to live in routes).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.weekly_material import WeeklyMaterial
from app.services.export.base import ExportContentError
from app.services.unit_export_data import extract_quiz_nodes

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.quiz_question import QuizQuestion


def gather_unit_quiz_questions(unit_id: str, db: Session) -> list[QuizQuestion]:
    """Collect quiz questions from every WeeklyMaterial's content_json in a unit."""
    questions: list[QuizQuestion] = []
    materials = db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
    for mat in materials:
        if mat.content_json:
            questions.extend(extract_quiz_nodes(mat.content_json))
    return questions


def load_material(material_id: str, db: Session) -> WeeklyMaterial:
    """Load a WeeklyMaterial by id or raise ExportContentError (→ 404)."""
    material = db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id).first()
    if material is None:
        raise ExportContentError("Material not found")
    return material
