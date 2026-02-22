"""
Tests for QTI import/export service.

Covers:
- QTI 1.2 export (MC, T/F, short answer, essay, matching)
- QTI 2.1 export as ZIP
- QTI 1.2 import (parse back to ParsedQuestion)
- QTI 2.1 import (parse assessmentItem files)
- Round-trip: export then import, verify data preserved
- Integration: DB-backed export/import via IMSCC service
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

from app.models.content import Content, ContentType
from app.models.quiz_question import QuestionType, QuizQuestion
from app.services.qti_service import (
    qti_exporter,
    qti_importer,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit


# ---------------------------------------------------------------------------
# Helpers to build QuizQuestion objects without DB
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


def _make_question(
    *,
    text: str,
    q_type: str,
    options: list[object] | None = None,
    correct: list[object] | None = None,
    explanation: str | None = None,
    points: float = 1.0,
) -> QuizQuestion:
    """Create a fake QuizQuestion for export tests (no DB needed)."""
    return _FakeQuestion(  # type: ignore[return-value]
        text=text,
        q_type=q_type,
        options=options,
        correct=correct,
        explanation=explanation,
        points=points,
    )


# ---------------------------------------------------------------------------
# QTI 1.2 Export Tests
# ---------------------------------------------------------------------------


class TestQTI12Export:
    """Tests for QTI 1.2 XML export."""

    def test_mc_export(self) -> None:
        q = _make_question(
            text="What is 2+2?",
            q_type=QuestionType.MULTIPLE_CHOICE.value,
            options=["3", "4", "5"],
            correct=["4"],
        )
        xml_str = qti_exporter.export_qti12([q], "Test Quiz")
        root = ET.fromstring(xml_str)

        assert root.tag == "questestinterop"
        items = list(root.iter("item"))
        assert len(items) == 1

        # Check render_choice has 3 options
        choices = list(root.iter("response_label"))
        assert len(choices) == 3

    def test_tf_export(self) -> None:
        q = _make_question(
            text="The sky is blue.",
            q_type=QuestionType.TRUE_FALSE.value,
            options=["True", "False"],
            correct=["True"],
        )
        xml_str = qti_exporter.export_qti12([q], "TF Quiz")
        root = ET.fromstring(xml_str)
        choices = list(root.iter("response_label"))
        assert len(choices) == 2

    def test_short_answer_export(self) -> None:
        q = _make_question(
            text="Capital of Australia?",
            q_type=QuestionType.SHORT_ANSWER.value,
            correct=["Canberra"],
        )
        xml_str = qti_exporter.export_qti12([q], "SA Quiz")
        root = ET.fromstring(xml_str)

        # Should have response_str + render_fib
        resp_str = list(root.iter("response_str"))
        assert len(resp_str) == 1
        fib = list(root.iter("render_fib"))
        assert len(fib) == 1

    def test_essay_export(self) -> None:
        q = _make_question(
            text="Discuss the impact of AI.",
            q_type=QuestionType.LONG_ANSWER.value,
        )
        xml_str = qti_exporter.export_qti12([q], "Essay Quiz")
        root = ET.fromstring(xml_str)

        fib = list(root.iter("render_fib"))
        assert len(fib) == 1
        assert fib[0].get("rows") == "15"

    def test_matching_export(self) -> None:
        q = _make_question(
            text="Match the items.",
            q_type=QuestionType.MATCHING.value,
            options=[
                {"left": "A", "right": "1"},
                {"left": "B", "right": "2"},
            ],
        )
        xml_str = qti_exporter.export_qti12([q], "Match Quiz")
        root = ET.fromstring(xml_str)

        # Should have 2 response_lid elements (one per left item)
        lids = list(root.iter("response_lid"))
        assert len(lids) == 2

    def test_feedback_export(self) -> None:
        q = _make_question(
            text="What is 2+2?",
            q_type=QuestionType.MULTIPLE_CHOICE.value,
            options=["3", "4"],
            correct=["4"],
            explanation="The answer is 4.",
        )
        xml_str = qti_exporter.export_qti12([q], "FB Quiz")
        root = ET.fromstring(xml_str)

        feedback = list(root.iter("itemfeedback"))
        assert len(feedback) == 1

    def test_multiple_questions(self) -> None:
        questions = [
            _make_question(
                text="Q1",
                q_type=QuestionType.MULTIPLE_CHOICE.value,
                options=["A", "B"],
                correct=["A"],
            ),
            _make_question(
                text="Q2", q_type=QuestionType.SHORT_ANSWER.value, correct=["ans"]
            ),
            _make_question(text="Q3", q_type=QuestionType.LONG_ANSWER.value),
        ]
        xml_str = qti_exporter.export_qti12(questions, "Multi Quiz")
        root = ET.fromstring(xml_str)
        items = list(root.iter("item"))
        assert len(items) == 3

    def test_case_study_exports_as_essay(self) -> None:
        q = _make_question(
            text="Analyze this case.",
            q_type=QuestionType.CASE_STUDY.value,
        )
        xml_str = qti_exporter.export_qti12([q], "Case Quiz")
        root = ET.fromstring(xml_str)
        fib = list(root.iter("render_fib"))
        assert len(fib) == 1
        assert fib[0].get("rows") == "15"


# ---------------------------------------------------------------------------
# QTI 2.1 Export Tests
# ---------------------------------------------------------------------------


class TestQTI21Export:
    """Tests for QTI 2.1 ZIP export."""

    def test_zip_structure(self) -> None:
        questions = [
            _make_question(
                text="What is 2+2?",
                q_type=QuestionType.MULTIPLE_CHOICE.value,
                options=["3", "4"],
                correct=["4"],
            ),
            _make_question(
                text="Capital?",
                q_type=QuestionType.SHORT_ANSWER.value,
                correct=["Canberra"],
            ),
        ]
        buf = qti_exporter.export_qti21_zip(questions, "Test Quiz")
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            # Should have 2 item XML files
            item_files = [
                n for n in names if n.endswith(".xml") and n != "imsmanifest.xml"
            ]
            assert len(item_files) == 2

    def test_mc_qti21_item(self) -> None:
        q = _make_question(
            text="Pick one.",
            q_type=QuestionType.MULTIPLE_CHOICE.value,
            options=["A", "B", "C"],
            correct=["B"],
        )
        buf = qti_exporter.export_qti21_zip([q], "MC Quiz")
        with zipfile.ZipFile(buf, "r") as zf:
            item_files = [n for n in zf.namelist() if n != "imsmanifest.xml"]
            xml_text = zf.read(item_files[0]).decode("utf-8")
            root = ET.fromstring(xml_text)

            # Root should be assessmentItem
            assert "assessmentItem" in root.tag

    def test_essay_qti21_item(self) -> None:
        q = _make_question(
            text="Write an essay.",
            q_type=QuestionType.LONG_ANSWER.value,
        )
        buf = qti_exporter.export_qti21_zip([q], "Essay Quiz")
        with zipfile.ZipFile(buf, "r") as zf:
            item_files = [n for n in zf.namelist() if n != "imsmanifest.xml"]
            xml_text = zf.read(item_files[0]).decode("utf-8")
            assert "extendedTextInteraction" in xml_text

    def test_empty_questions(self) -> None:
        buf = qti_exporter.export_qti21_zip([], "Empty Quiz")
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            item_files = [n for n in names if n != "imsmanifest.xml"]
            assert len(item_files) == 0


# ---------------------------------------------------------------------------
# QTI Import Tests
# ---------------------------------------------------------------------------


class TestQTI12Import:
    """Tests for QTI 1.2 XML import."""

    def test_parse_mc(self) -> None:
        q = _make_question(
            text="What is 2+2?",
            q_type=QuestionType.MULTIPLE_CHOICE.value,
            options=["3", "4", "5"],
            correct=["4"],
            explanation="Basic math.",
        )
        xml_str = qti_exporter.export_qti12([q], "Test")

        # Wrap in a ZIP
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("assessment.xml", xml_str)
        buf.seek(0)

        with zipfile.ZipFile(buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        assert len(results) == 1
        _filename, questions = results[0]
        assert len(questions) == 1
        pq = questions[0]
        assert pq.question_text == "What is 2+2?"
        assert pq.question_type == QuestionType.MULTIPLE_CHOICE.value
        assert len(pq.options) == 3
        assert "4" in pq.correct_answers

    def test_parse_tf(self) -> None:
        q = _make_question(
            text="Is the sky blue?",
            q_type=QuestionType.TRUE_FALSE.value,
            options=["True", "False"],
            correct=["True"],
        )
        xml_str = qti_exporter.export_qti12([q], "Test")

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("tf.xml", xml_str)
        buf.seek(0)

        with zipfile.ZipFile(buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        pq = results[0][1][0]
        assert pq.question_type == QuestionType.TRUE_FALSE.value
        assert len(pq.options) == 2

    def test_parse_short_answer(self) -> None:
        q = _make_question(
            text="Capital of France?",
            q_type=QuestionType.SHORT_ANSWER.value,
            correct=["Paris"],
        )
        xml_str = qti_exporter.export_qti12([q], "Test")

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("sa.xml", xml_str)
        buf.seek(0)

        with zipfile.ZipFile(buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        pq = results[0][1][0]
        assert pq.question_type == QuestionType.SHORT_ANSWER.value
        assert "Paris" in pq.correct_answers

    def test_parse_essay(self) -> None:
        q = _make_question(
            text="Discuss AI ethics.",
            q_type=QuestionType.LONG_ANSWER.value,
        )
        xml_str = qti_exporter.export_qti12([q], "Test")

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("essay.xml", xml_str)
        buf.seek(0)

        with zipfile.ZipFile(buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        pq = results[0][1][0]
        assert pq.question_type == QuestionType.LONG_ANSWER.value

    def test_parse_feedback(self) -> None:
        q = _make_question(
            text="Q?",
            q_type=QuestionType.MULTIPLE_CHOICE.value,
            options=["A", "B"],
            correct=["A"],
            explanation="A is correct.",
        )
        xml_str = qti_exporter.export_qti12([q], "Test")

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("fb.xml", xml_str)
        buf.seek(0)

        with zipfile.ZipFile(buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        pq = results[0][1][0]
        assert pq.answer_explanation == "A is correct."


class TestQTI21Import:
    """Tests for QTI 2.1 import."""

    def test_parse_mc_from_zip(self) -> None:
        questions = [
            _make_question(
                text="Pick the right answer.",
                q_type=QuestionType.MULTIPLE_CHOICE.value,
                options=["X", "Y", "Z"],
                correct=["Y"],
            ),
        ]
        zip_buf = qti_exporter.export_qti21_zip(questions, "MC Quiz")

        with zipfile.ZipFile(zip_buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        # Should parse the item file
        assert len(results) >= 1
        all_qs = [q for _, qs in results for q in qs]
        assert len(all_qs) == 1
        pq = all_qs[0]
        assert pq.question_type == QuestionType.MULTIPLE_CHOICE.value
        assert len(pq.options) == 3

    def test_parse_text_entry_from_zip(self) -> None:
        questions = [
            _make_question(
                text="What is Python?",
                q_type=QuestionType.SHORT_ANSWER.value,
                correct=["programming language"],
            ),
        ]
        zip_buf = qti_exporter.export_qti21_zip(questions, "SA Quiz")

        with zipfile.ZipFile(zip_buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        all_qs = [q for _, qs in results for q in qs]
        assert len(all_qs) == 1
        assert all_qs[0].question_type == QuestionType.SHORT_ANSWER.value

    def test_parse_essay_from_zip(self) -> None:
        questions = [
            _make_question(
                text="Write about climate change.",
                q_type=QuestionType.LONG_ANSWER.value,
            ),
        ]
        zip_buf = qti_exporter.export_qti21_zip(questions, "Essay Quiz")

        with zipfile.ZipFile(zip_buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        all_qs = [q for _, qs in results for q in qs]
        assert len(all_qs) == 1
        assert all_qs[0].question_type == QuestionType.LONG_ANSWER.value


# ---------------------------------------------------------------------------
# Round-trip Tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """Export then import, verify data preserved."""

    def test_mc_round_trip_qti12(self) -> None:
        q = _make_question(
            text="What color is the ocean?",
            q_type=QuestionType.MULTIPLE_CHOICE.value,
            options=["Red", "Blue", "Green"],
            correct=["Blue"],
            explanation="The ocean appears blue.",
        )

        # Export
        xml_str = qti_exporter.export_qti12([q], "RT Quiz")

        # Import
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("quiz.xml", xml_str)
        buf.seek(0)

        with zipfile.ZipFile(buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        pq = results[0][1][0]
        assert pq.question_text == "What color is the ocean?"
        assert pq.question_type == QuestionType.MULTIPLE_CHOICE.value
        assert len(pq.options) == 3
        assert "Blue" in pq.correct_answers
        assert pq.answer_explanation == "The ocean appears blue."

    def test_mc_round_trip_qti21(self) -> None:
        q = _make_question(
            text="What is the largest planet?",
            q_type=QuestionType.MULTIPLE_CHOICE.value,
            options=["Earth", "Jupiter", "Mars"],
            correct=["Jupiter"],
        )

        # Export as QTI 2.1
        zip_buf = qti_exporter.export_qti21_zip([q], "RT Quiz")

        # Import
        with zipfile.ZipFile(zip_buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        all_qs = [q for _, qs in results for q in qs]
        assert len(all_qs) == 1
        pq = all_qs[0]
        assert pq.question_text == "What is the largest planet?"
        assert pq.question_type == QuestionType.MULTIPLE_CHOICE.value

    def test_mixed_types_round_trip(self) -> None:
        questions = [
            _make_question(
                text="MC Q",
                q_type=QuestionType.MULTIPLE_CHOICE.value,
                options=["A", "B"],
                correct=["A"],
            ),
            _make_question(
                text="SA Q",
                q_type=QuestionType.SHORT_ANSWER.value,
                correct=["answer"],
            ),
            _make_question(
                text="Essay Q",
                q_type=QuestionType.LONG_ANSWER.value,
            ),
        ]

        xml_str = qti_exporter.export_qti12(questions, "Mixed")

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("mixed.xml", xml_str)
        buf.seek(0)

        with zipfile.ZipFile(buf, "r") as zf:
            results = qti_importer.parse_qti_from_zip(zf)

        all_qs = [q for _, qs in results for q in qs]
        assert len(all_qs) == 3
        types = {q.question_type for q in all_qs}
        assert QuestionType.MULTIPLE_CHOICE.value in types
        assert QuestionType.SHORT_ANSWER.value in types
        assert QuestionType.LONG_ANSWER.value in types


# ---------------------------------------------------------------------------
# Integration Tests (with DB)
# ---------------------------------------------------------------------------


class TestQTIIntegration:
    """Integration tests using DB fixtures."""

    def test_export_with_db_questions(
        self,
        test_db: Session,
        test_quiz_content: tuple[Content, list[QuizQuestion]],
    ) -> None:
        """Test QTI 1.2 export with real DB QuizQuestion rows."""
        _content, questions = test_quiz_content
        xml_str = qti_exporter.export_qti12(questions, "DB Quiz")
        root = ET.fromstring(xml_str)

        items = list(root.iter("item"))
        assert len(items) == 3  # MC + TF + SA

    def test_export_qti21_with_db_questions(
        self,
        test_db: Session,
        test_quiz_content: tuple[Content, list[QuizQuestion]],
    ) -> None:
        """Test QTI 2.1 ZIP export with real DB QuizQuestion rows."""
        _content, questions = test_quiz_content
        buf = qti_exporter.export_qti21_zip(questions, "DB Quiz 2.1")

        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "imsmanifest.xml" in names
            item_files = [
                n for n in names if n.endswith(".xml") and n != "imsmanifest.xml"
            ]
            assert len(item_files) == 3

    def test_imscc_export_includes_qti(
        self,
        test_db: Session,
        test_unit: Unit,
        test_quiz_content: tuple[Content, list[QuizQuestion]],
    ) -> None:
        """Test that IMSCC export includes QTI XML files."""
        from app.services.imscc_service import imscc_export_service

        # Need unit outline for the export
        from app.models.unit_outline import UnitOutline

        outline = UnitOutline(
            unit_id=str(test_unit.id),
            title=str(test_unit.title),
            description="Test",
            duration_weeks=12,
            credit_points=6,
            status="planning",
            created_by_id=str(test_unit.owner_id),
        )
        test_db.add(outline)
        test_db.commit()

        buf, _filename = imscc_export_service.export_unit(str(test_unit.id), test_db)

        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            qti_files = [n for n in names if n.startswith("quizzes/")]
            assert len(qti_files) >= 1

            # Verify the QTI XML is valid
            for qf in qti_files:
                xml_text = zf.read(qf).decode("utf-8")
                root = ET.fromstring(xml_text)
                assert root.tag == "questestinterop"

            # Verify manifest references QTI
            manifest_text = zf.read("imsmanifest.xml").decode("utf-8")
            assert "imsqti_xmlv1p2" in manifest_text

    def test_import_creates_quiz_questions(
        self,
        test_db: Session,
        test_unit: Unit,
        test_quiz_content: tuple[Content, list[QuizQuestion]],
    ) -> None:
        """Test that importing a package with QTI creates QuizQuestion rows."""
        from app.services.package_import_service import PackageImportService

        _content, questions = test_quiz_content

        # Export QTI 1.2 and wrap in an IMSCC-like ZIP
        xml_str = qti_exporter.export_qti12(questions, "Import Test")

        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("quizzes/quiz1/assessment.xml", xml_str)
            # Minimal imsmanifest.xml
            manifest = """<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
          identifier="test_import">
  <metadata>
    <schema>IMS Common Cartridge</schema>
    <schemaversion>1.1.0</schemaversion>
  </metadata>
  <organizations>
    <organization identifier="org_1" structure="rooted-hierarchy">
      <item identifier="root">
        <item identifier="week_01">
          <title>Week 1</title>
        </item>
      </item>
    </organization>
  </organizations>
  <resources/>
</manifest>"""
            zf.writestr("imsmanifest.xml", manifest)

        zip_bytes = zip_buf.getvalue()

        svc = PackageImportService()
        result = svc.create_unit_from_package(
            zip_bytes,
            str(test_unit.owner_id),
            test_db,
        )

        assert result.quiz_question_count == 3

        # Verify QuizQuestion rows exist in DB
        imported_qs = (
            test_db.query(QuizQuestion)
            .filter(
                QuizQuestion.content_id.in_(
                    test_db.query(Content.id).filter(
                        Content.unit_id == result.unit_id,
                        Content.type == ContentType.QUIZ.value,
                    )
                )
            )
            .all()
        )
        assert len(imported_qs) == 3
