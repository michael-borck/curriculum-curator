"""
Shared data-gathering module for unit export services (IMSCC, SCORM).

Provides:
- UnitExportData dataclass with all DB entities needed for export
- gather_unit_export_data() function to query DB
- Shared utilities: _slugify, _escape_html, HTML_TEMPLATE
"""

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.accreditation_mappings import (
    ULOGraduateCapabilityMapping,
    UnitAoLMapping,
    UnitSDGMapping,
)
from app.models.assessment import Assessment
from app.models.content import Content
from app.models.enums import ContentType
from app.models.learning_outcome import UnitLearningOutcome
from app.models.quiz_question import QuizQuestion
from app.models.unit import Unit
from app.models.unit_outline import UnitOutline
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic

MERMAID_CDN_SCRIPT = (
    '  <script type="module">'
    "import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';"
    "mermaid.initialize({startOnLoad:true});"
    "</script>"
)


def mermaid_head(content: str) -> str:
    """Return the Mermaid CDN script tag if content contains Mermaid blocks."""
    if '<pre class="mermaid">' in content:
        return MERMAID_CDN_SCRIPT
    return ""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
    h1, h2, h3 {{ color: #1a1a2e; }}
    code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
    pre {{ background: #f4f4f4; padding: 1rem; overflow-x: auto; border-radius: 6px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f0f0f0; }}
  </style>
{extra_head}
</head>
<body>
  <h1>{title}</h1>
  {content}
</body>
</html>"""


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug[:60]


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@dataclass
class UnitExportData:
    """All data needed to export a unit."""

    unit: Unit
    outline: UnitOutline | None
    weekly_topics: list[WeeklyTopic]
    weekly_materials: list[WeeklyMaterial]
    assessments: list[Assessment]
    learning_outcomes: list[UnitLearningOutcome]
    aol_mappings: list[UnitAoLMapping]
    sdg_mappings: list[UnitSDGMapping]
    gc_mappings: list[ULOGraduateCapabilityMapping]
    materials_by_week: dict[int, list[WeeklyMaterial]] = field(default_factory=dict)
    quiz_questions_by_content: dict[str, list[QuizQuestion]] = field(
        default_factory=dict
    )


def gather_unit_export_data(unit_id: str, db: Session) -> UnitExportData:
    """Query the DB for all data needed to export a unit.

    Raises ValueError if the unit is not found.
    """
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        msg = f"Unit {unit_id} not found"
        raise ValueError(msg)

    outline = db.query(UnitOutline).filter(UnitOutline.unit_id == unit_id).first()

    weekly_topics = (
        db.query(WeeklyTopic)
        .filter(WeeklyTopic.unit_id == unit_id)
        .order_by(WeeklyTopic.week_number)
        .all()
    )

    weekly_materials = (
        db.query(WeeklyMaterial)
        .filter(WeeklyMaterial.unit_id == unit_id)
        .order_by(WeeklyMaterial.week_number, WeeklyMaterial.order_index)
        .all()
    )

    assessments = (
        db.query(Assessment)
        .filter(Assessment.unit_id == unit_id)
        .order_by(Assessment.due_week)
        .all()
    )

    learning_outcomes = (
        db.query(UnitLearningOutcome)
        .filter(UnitLearningOutcome.unit_id == unit_id)
        .order_by(UnitLearningOutcome.sequence_order)
        .all()
    )

    aol_mappings = (
        db.query(UnitAoLMapping).filter(UnitAoLMapping.unit_id == unit_id).all()
    )

    sdg_mappings = (
        db.query(UnitSDGMapping).filter(UnitSDGMapping.unit_id == unit_id).all()
    )

    gc_mappings: list[ULOGraduateCapabilityMapping] = []
    for ulo in learning_outcomes:
        gc_maps = (
            db.query(ULOGraduateCapabilityMapping)
            .filter(ULOGraduateCapabilityMapping.ulo_id == ulo.id)
            .all()
        )
        gc_mappings.extend(gc_maps)

    # Group materials by week
    materials_by_week: dict[int, list[WeeklyMaterial]] = {}
    for mat in weekly_materials:
        week = int(mat.week_number)
        materials_by_week.setdefault(week, []).append(mat)

    # Quiz questions grouped by content ID
    quiz_contents = (
        db.query(Content)
        .filter(Content.unit_id == unit_id, Content.type == ContentType.QUIZ.value)
        .all()
    )
    quiz_questions_by_content: dict[str, list[QuizQuestion]] = {}
    for qc in quiz_contents:
        questions = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.content_id == qc.id)
            .order_by(QuizQuestion.order_index)
            .all()
        )
        if questions:
            quiz_questions_by_content[str(qc.id)] = questions

    return UnitExportData(
        unit=unit,
        outline=outline,
        weekly_topics=weekly_topics,
        weekly_materials=weekly_materials,
        assessments=assessments,
        learning_outcomes=learning_outcomes,
        aol_mappings=aol_mappings,
        sdg_mappings=sdg_mappings,
        gc_mappings=gc_mappings,
        materials_by_week=materials_by_week,
        quiz_questions_by_content=quiz_questions_by_content,
    )
