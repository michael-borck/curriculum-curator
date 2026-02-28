"""
Shared data-gathering module for unit export services (IMSCC, SCORM).

Provides:
- UnitExportData dataclass with all DB entities needed for export
- gather_unit_export_data() function to query DB
- Shared utilities: _slugify, _escape_html, HTML_TEMPLATE
"""

import re
from dataclasses import dataclass, field
from typing import Any

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
from app.services.content_json_renderer import render_content_json

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


def render_material_html(mat: "WeeklyMaterial") -> str:
    """Render material content to HTML, preferring content_json over description.

    If the material has structured content_json (from the TipTap editor),
    render it to HTML. Otherwise fall back to the legacy description field.
    """
    if mat.content_json:
        return render_content_json(mat.content_json)
    return str(mat.description or "")


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
    quiz_questions_by_material: dict[str, list[QuizQuestion]] = field(
        default_factory=dict
    )


class InMemoryQuizQuestion:
    """Lightweight stand-in for QuizQuestion without SQLAlchemy instrumentation.

    The QTI exporter only reads attribute values (question_text, question_type,
    options, correct_answers, answer_explanation, points, id). This class
    provides those attributes without triggering SQLAlchemy's descriptor
    machinery, so we can build instances outside a Session.
    """

    def __init__(
        self,
        *,
        question_id: str,
        question_text: str,
        question_type: str,
        options: list[dict[str, str]],
        correct_answers: list[str],
        answer_explanation: str | None,
        points: float,
        order_index: int,
    ) -> None:
        self.id = question_id
        self.content_id = ""
        self.question_text = question_text
        self.question_type = question_type
        self.order_index = order_index
        self.options = options
        self.correct_answers = correct_answers
        self.answer_explanation = answer_explanation
        self.points = points
        self.feedback: dict[str, Any] | None = None
        self.partial_credit: dict[str, Any] | None = None
        self.difficulty_level: str | None = None
        self.bloom_level: str | None = None
        self.learning_objective: str | None = None
        self.question_metadata: dict[str, Any] | None = None


def extract_quiz_nodes(content_json: dict[str, Any]) -> list[QuizQuestion]:
    """Extract quizQuestion nodes from TipTap content_json into in-memory QuizQuestion-compatible instances.

    Recursively walks the ProseMirror/TipTap document tree looking for
    nodes with type == "quizQuestion" and converts their attrs into
    lightweight objects that duck-type as QuizQuestion (no DB session needed).
    """
    questions: list[QuizQuestion] = []

    def _walk(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            if node.get("type") == "quizQuestion":
                attrs = node.get("attrs", {})
                options_raw: list[dict[str, Any]] = attrs.get("options", [])

                options = [{"text": str(o.get("text", ""))} for o in options_raw]
                correct_answers = [
                    str(o.get("text", ""))
                    for o in options_raw
                    if o.get("correct", False)
                ]

                q = InMemoryQuizQuestion(
                    question_id=str(attrs.get("questionId", "")),
                    question_text=str(attrs.get("questionText", "")),
                    question_type=str(attrs.get("questionType", "multiple_choice")),
                    options=options,
                    correct_answers=correct_answers,
                    answer_explanation=attrs.get("feedback") or None,
                    points=float(attrs.get("points", 1.0)),
                    order_index=len(questions),
                )
                questions.append(q)  # type: ignore[arg-type]

            # Recurse into child nodes
            if "content" in node:
                _walk(node["content"])

    top_content = content_json.get("content")
    if isinstance(top_content, list):
        _walk(top_content)

    return questions


def extract_branching_cards(content_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract branchingCard nodes from TipTap content_json.

    Recursively walks the ProseMirror/TipTap document tree looking for
    nodes with type == "branchingCard" and returns their attrs dicts.
    """
    cards: list[dict[str, Any]] = []

    def _walk(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            if node.get("type") == "branchingCard":
                attrs = node.get("attrs", {})
                cards.append(
                    {
                        "cardId": str(attrs.get("cardId", "")),
                        "cardType": str(attrs.get("cardType", "content")),
                        "cardTitle": str(attrs.get("cardTitle", "")),
                        "cardContent": str(attrs.get("cardContent", "")),
                        "choices": attrs.get("choices", []),
                        "endScore": int(attrs.get("endScore", 0)),
                        "endMessage": str(attrs.get("endMessage", "")),
                    }
                )

            if "content" in node:
                _walk(node["content"])

    top_content = content_json.get("content")
    if isinstance(top_content, list):
        _walk(top_content)

    return cards


def extract_video_embed(content_json: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the interactiveVideoEmbed node from TipTap content_json.

    Returns the node's attrs (url, platform, title) or None if not found.
    """
    result: dict[str, Any] | None = None

    def _walk(nodes: list[dict[str, Any]]) -> None:
        nonlocal result
        for node in nodes:
            if node.get("type") == "interactiveVideoEmbed":
                attrs = node.get("attrs", {})
                result = {
                    "url": str(attrs.get("url", "")),
                    "platform": str(attrs.get("platform", "")),
                    "title": str(attrs.get("title", "")),
                }
                return

            if "content" in node:
                _walk(node["content"])
                if result is not None:
                    return

    top_content = content_json.get("content")
    if isinstance(top_content, list):
        _walk(top_content)

    return result


def extract_video_interactions(content_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract videoInteraction nodes from TipTap content_json, sorted by time.

    Returns a list of interaction attrs dicts.
    """
    interactions: list[dict[str, Any]] = []

    def _walk(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            if node.get("type") == "videoInteraction":
                attrs = node.get("attrs", {})
                interactions.append(
                    {
                        "interactionId": str(attrs.get("interactionId", "")),
                        "time": float(attrs.get("time", 0)),
                        "pause": bool(attrs.get("pause", True)),
                        "questionType": str(
                            attrs.get("questionType", "multiple_choice")
                        ),
                        "questionText": str(attrs.get("questionText", "")),
                        "options": attrs.get("options", []),
                        "feedback": attrs.get("feedback") or None,
                        "points": float(attrs.get("points", 1.0)),
                    }
                )

            if "content" in node:
                _walk(node["content"])

    top_content = content_json.get("content")
    if isinstance(top_content, list):
        _walk(top_content)

    interactions.sort(key=lambda x: x["time"])
    return interactions


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

    # Quiz questions from editor content_json (quizQuestion TipTap nodes)
    quiz_questions_by_material: dict[str, list[QuizQuestion]] = {}
    for mat in weekly_materials:
        if mat.content_json:
            extracted = extract_quiz_nodes(mat.content_json)
            if extracted:
                quiz_questions_by_material[str(mat.id)] = extracted

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
        quiz_questions_by_material=quiz_questions_by_material,
    )
