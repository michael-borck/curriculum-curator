"""
Tests for QTI export from editor content_json (quizQuestion TipTap nodes).

Covers:
- extract_quiz_nodes() with each of the 5 editor question types
- extract_quiz_nodes() with mixed content (paragraphs + quiz nodes)
- extract_quiz_nodes() with empty/null content_json
- multi_select QTI 1.2 output has rcardinality="Multiple"
- multi_select QTI 2.1 output has maxChoices="0" and cardinality="multiple"
- gather_unit_export_data() populates quiz_questions_by_material
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any

import pytest

from app.models.quiz_question import QuestionType, QuizQuestion
from app.services.qti_service import qti_exporter
from app.services.unit_export_data import extract_quiz_nodes

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit


# ---------------------------------------------------------------------------
# Helpers — build TipTap content_json structures
# ---------------------------------------------------------------------------


def _quiz_node(
    *,
    question_text: str = "Sample question?",
    question_type: str = "multiple_choice",
    options: list[dict[str, Any]] | None = None,
    feedback: str | None = None,
    points: float = 1.0,
    question_id: str | None = None,
) -> dict[str, Any]:
    """Build a quizQuestion TipTap node."""
    if options is None:
        options = [
            {"text": "Option A", "correct": True},
            {"text": "Option B", "correct": False},
        ]
    return {
        "type": "quizQuestion",
        "attrs": {
            "questionId": question_id or str(uuid.uuid4()),
            "questionText": question_text,
            "questionType": question_type,
            "options": options,
            "feedback": feedback,
            "points": points,
        },
    }


def _paragraph(text: str = "Hello world") -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}],
    }


def _doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


# ---------------------------------------------------------------------------
# extract_quiz_nodes tests
# ---------------------------------------------------------------------------


class TestExtractQuizNodes:
    def test_multiple_choice(self) -> None:
        doc = _doc(
            _quiz_node(
                question_text="What is 2+2?",
                question_type="multiple_choice",
                options=[
                    {"text": "3", "correct": False},
                    {"text": "4", "correct": True},
                    {"text": "5", "correct": False},
                ],
            )
        )
        result = extract_quiz_nodes(doc)
        assert len(result) == 1
        q = result[0]
        assert q.question_text == "What is 2+2?"
        assert q.question_type == "multiple_choice"
        assert len(q.options or []) == 3
        assert q.correct_answers == ["4"]
        assert q.points == 1.0

    def test_true_false(self) -> None:
        doc = _doc(
            _quiz_node(
                question_text="The sky is blue.",
                question_type="true_false",
                options=[
                    {"text": "True", "correct": True},
                    {"text": "False", "correct": False},
                ],
            )
        )
        result = extract_quiz_nodes(doc)
        assert len(result) == 1
        assert result[0].question_type == "true_false"
        assert result[0].correct_answers == ["True"]

    def test_multi_select(self) -> None:
        doc = _doc(
            _quiz_node(
                question_text="Select all prime numbers.",
                question_type="multi_select",
                options=[
                    {"text": "2", "correct": True},
                    {"text": "4", "correct": False},
                    {"text": "5", "correct": True},
                    {"text": "9", "correct": False},
                ],
            )
        )
        result = extract_quiz_nodes(doc)
        assert len(result) == 1
        q = result[0]
        assert q.question_type == "multi_select"
        assert q.correct_answers == ["2", "5"]

    def test_short_answer(self) -> None:
        doc = _doc(
            _quiz_node(
                question_text="Name the capital of Australia.",
                question_type="short_answer",
                options=[],
                feedback="Canberra is the capital.",
            )
        )
        result = extract_quiz_nodes(doc)
        assert len(result) == 1
        q = result[0]
        assert q.question_type == "short_answer"
        assert q.answer_explanation == "Canberra is the capital."
        assert q.correct_answers == []

    def test_fill_in_blank(self) -> None:
        doc = _doc(
            _quiz_node(
                question_text="The chemical symbol for water is ___.",
                question_type="fill_in_blank",
                options=[
                    {"text": "H2O", "correct": True},
                ],
                points=2.0,
            )
        )
        result = extract_quiz_nodes(doc)
        assert len(result) == 1
        q = result[0]
        assert q.question_type == "fill_in_blank"
        assert q.correct_answers == ["H2O"]
        assert q.points == 2.0

    def test_mixed_content(self) -> None:
        """Paragraphs and quiz nodes interleaved."""
        doc = _doc(
            _paragraph("Introduction text"),
            _quiz_node(question_text="Q1?"),
            _paragraph("Middle text"),
            _quiz_node(question_text="Q2?"),
            _paragraph("Conclusion"),
        )
        result = extract_quiz_nodes(doc)
        assert len(result) == 2
        assert result[0].question_text == "Q1?"
        assert result[1].question_text == "Q2?"
        assert result[0].order_index == 0
        assert result[1].order_index == 1

    def test_empty_content_json(self) -> None:
        assert extract_quiz_nodes({}) == []
        assert extract_quiz_nodes({"content": []}) == []

    def test_no_quiz_nodes(self) -> None:
        doc = _doc(_paragraph("Just text"))
        assert extract_quiz_nodes(doc) == []

    def test_question_id_preserved(self) -> None:
        qid = str(uuid.uuid4())
        doc = _doc(_quiz_node(question_id=qid))
        result = extract_quiz_nodes(doc)
        assert result[0].id == qid

    def test_nested_quiz_node(self) -> None:
        """Quiz node inside a wrapper node (e.g. blockquote)."""
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "blockquote",
                    "content": [
                        _quiz_node(question_text="Nested?"),
                    ],
                }
            ],
        }
        result = extract_quiz_nodes(doc)
        assert len(result) == 1
        assert result[0].question_text == "Nested?"


# ---------------------------------------------------------------------------
# Multi-select QTI output tests
# ---------------------------------------------------------------------------


class _FakeQuestion:
    """Lightweight stand-in for QuizQuestion without SQLAlchemy instrumentation."""

    def __init__(
        self,
        *,
        text: str,
        q_type: str,
        options: list[object] | None = None,
        correct: list[object] | None = None,
        explanation: str | None = None,
        points: float = 1.0,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.content_id = str(uuid.uuid4())
        self.question_text = text
        self.question_type = q_type
        self.order_index = 0
        self.options = options
        self.correct_answers = correct
        self.answer_explanation = explanation
        self.points = points
        self.feedback: dict[str, object] | None = None
        self.partial_credit: dict[str, object] | None = None
        self.difficulty_level: str | None = None
        self.bloom_level: str | None = None
        self.learning_objective: str | None = None
        self.question_metadata: dict[str, object] | None = None


def _make_multi_select_question() -> QuizQuestion:
    """Create a multi-select QuizQuestion for QTI export tests."""
    return _FakeQuestion(  # type: ignore[return-value]
        text="Select all even numbers.",
        q_type=QuestionType.MULTI_SELECT.value,
        options=[{"text": "A"}, {"text": "B"}, {"text": "C"}, {"text": "D"}],
        correct=["B", "D"],
        points=2.0,
    )


class TestMultiSelectQTI12:
    def test_rcardinality_multiple(self) -> None:
        q = _make_multi_select_question()
        xml_str = qti_exporter.export_qti12([q], "Multi-select Quiz")
        root = ET.fromstring(xml_str)

        # Find the response_lid element
        response_lid = root.find(".//response_lid")
        assert response_lid is not None
        assert response_lid.get("rcardinality") == "Multiple"

    def test_multiple_correct_respconditions(self) -> None:
        q = _make_multi_select_question()
        xml_str = qti_exporter.export_qti12([q], "Multi-select Quiz")
        root = ET.fromstring(xml_str)

        # Should have respconditions for both correct answers (opt_1 and opt_3)
        respconditions = root.findall(".//respcondition")
        correct_opts = []
        for rc in respconditions:
            ve = rc.find(".//varequal")
            if ve is not None and ve.text:
                correct_opts.append(ve.text)
        assert "opt_1" in correct_opts  # "B" is at index 1
        assert "opt_3" in correct_opts  # "D" is at index 3


class TestMultiSelectQTI21:
    def test_max_choices_zero(self) -> None:
        q = _make_multi_select_question()
        buf = qti_exporter.export_qti21_zip([q], "Multi-select Quiz")
        import zipfile
        from io import BytesIO

        with zipfile.ZipFile(BytesIO(buf.read()), "r") as zf:
            # Find the item XML file (not the manifest)
            item_files = [n for n in zf.namelist() if n != "imsmanifest.xml"]
            assert len(item_files) == 1
            item_xml = zf.read(item_files[0]).decode()

        root = ET.fromstring(item_xml)
        ns = {"qti": "http://www.imsglobal.org/xsd/imsqti_v2p1"}

        # choiceInteraction should have maxChoices="0"
        ci = root.find(".//qti:choiceInteraction", ns)
        assert ci is not None
        assert ci.get("maxChoices") == "0"

        # responseDeclaration should have cardinality="multiple"
        rd = root.find(".//qti:responseDeclaration", ns)
        assert rd is not None
        assert rd.get("cardinality") == "multiple"

        # correctResponse should have two values
        cr = root.find(".//qti:correctResponse", ns)
        assert cr is not None
        values = cr.findall(f"{{{ns['qti']}}}value")
        assert len(values) == 2


# ---------------------------------------------------------------------------
# Integration: extract_quiz_nodes → QTI export
# ---------------------------------------------------------------------------


class TestExtractToQTIRoundTrip:
    def test_extracted_questions_export_to_qti12(self) -> None:
        """Questions extracted from content_json can be exported as QTI 1.2."""
        doc = _doc(
            _quiz_node(
                question_text="What is Python?",
                question_type="multiple_choice",
                options=[
                    {"text": "A snake", "correct": False},
                    {"text": "A language", "correct": True},
                ],
            ),
            _quiz_node(
                question_text="Select truths.",
                question_type="multi_select",
                options=[
                    {"text": "1+1=2", "correct": True},
                    {"text": "1+1=3", "correct": False},
                    {"text": "2+2=4", "correct": True},
                ],
            ),
        )
        questions = extract_quiz_nodes(doc)
        assert len(questions) == 2

        xml_str = qti_exporter.export_qti12(questions, "Test Quiz")
        root = ET.fromstring(xml_str)

        items = root.findall(".//item")
        assert len(items) == 2


# ---------------------------------------------------------------------------
# gather_unit_export_data integration (requires DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gather_populates_quiz_questions_by_material(
    test_db: Session,
    test_unit: Unit,
) -> None:
    """gather_unit_export_data populates quiz_questions_by_material."""
    from app.models.weekly_material import WeeklyMaterial
    from app.services.unit_export_data import gather_unit_export_data

    mat = WeeklyMaterial(
        id=str(uuid.uuid4()),
        unit_id=str(test_unit.id),
        week_number=1,
        title="Quiz Material",
        type="lecture",
        content_json=_doc(
            _quiz_node(question_text="DB test question?"),
        ),
    )
    test_db.add(mat)
    test_db.commit()

    data = gather_unit_export_data(str(test_unit.id), test_db)
    assert str(mat.id) in data.quiz_questions_by_material
    questions = data.quiz_questions_by_material[str(mat.id)]
    assert len(questions) == 1
    assert questions[0].question_text == "DB test question?"


@pytest.mark.asyncio
async def test_gather_no_quiz_questions_when_no_content_json(
    test_db: Session,
    test_unit: Unit,
) -> None:
    """Materials without content_json produce no quiz_questions_by_material entries."""
    from app.models.weekly_material import WeeklyMaterial
    from app.services.unit_export_data import gather_unit_export_data

    mat = WeeklyMaterial(
        id=str(uuid.uuid4()),
        unit_id=str(test_unit.id),
        week_number=1,
        title="Plain Material",
        type="lecture",
        content_json=None,
    )
    test_db.add(mat)
    test_db.commit()

    data = gather_unit_export_data(str(test_unit.id), test_db)
    assert str(mat.id) not in data.quiz_questions_by_material
