"""
Tests for the H5P Question Set builder.

Covers:
- H5P package structure (ZIP contains h5p.json + content/content.json)
- Each question type maps correctly to H5P library
- multi_select produces singleAnswer: false
- h5p.json has correct preloadedDependencies for question types used
- Empty questions list produces valid but empty question set
"""

from __future__ import annotations

import json
import uuid
import zipfile
from io import BytesIO
from typing import Any

from app.services.h5p_service import H5PQuestionSetBuilder, h5p_builder


# ---------------------------------------------------------------------------
# Helpers — fake quiz questions
# ---------------------------------------------------------------------------


class _FakeQuestion:
    """Lightweight stand-in for QuizQuestion."""

    def __init__(
        self,
        *,
        text: str,
        q_type: str,
        options: list[dict[str, str]] | None = None,
        correct: list[str] | None = None,
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
        self.feedback: dict[str, Any] | None = None
        self.partial_credit: dict[str, Any] | None = None
        self.difficulty_level: str | None = None
        self.bloom_level: str | None = None
        self.learning_objective: str | None = None
        self.question_metadata: dict[str, Any] | None = None


def _mc_question(text: str = "What is 2+2?") -> _FakeQuestion:
    return _FakeQuestion(
        text=text,
        q_type="multiple_choice",
        options=[{"text": "3"}, {"text": "4"}, {"text": "5"}],
        correct=["4"],
    )


def _tf_question(text: str = "The sky is blue.") -> _FakeQuestion:
    return _FakeQuestion(
        text=text,
        q_type="true_false",
        options=[{"text": "True"}, {"text": "False"}],
        correct=["True"],
    )


def _multi_select_question() -> _FakeQuestion:
    return _FakeQuestion(
        text="Select all primes.",
        q_type="multi_select",
        options=[{"text": "2"}, {"text": "4"}, {"text": "5"}, {"text": "9"}],
        correct=["2", "5"],
    )


def _short_answer_question() -> _FakeQuestion:
    return _FakeQuestion(
        text="Name the capital of Australia.",
        q_type="short_answer",
        options=[],
        correct=["Canberra"],
        explanation="Canberra is the capital.",
    )


def _fill_blank_question() -> _FakeQuestion:
    return _FakeQuestion(
        text="The chemical symbol for water is ___.",
        q_type="fill_in_blank",
        options=[{"text": "H2O"}],
        correct=["H2O"],
        points=2.0,
    )


# ---------------------------------------------------------------------------
# Helper to unpack H5P ZIP
# ---------------------------------------------------------------------------


def _unpack_h5p(buf: BytesIO) -> tuple[dict[str, Any], dict[str, Any]]:
    """Unpack h5p.json and content/content.json from a .h5p ZIP."""
    buf.seek(0)
    with zipfile.ZipFile(buf, "r") as zf:
        h5p_json = json.loads(zf.read("h5p.json"))
        content_json = json.loads(zf.read("content/content.json"))
    return h5p_json, content_json


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestH5PPackageStructure:
    def test_zip_contains_required_files(self) -> None:
        buf = h5p_builder.build([_mc_question()], "Test Quiz")
        buf.seek(0)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
        assert "h5p.json" in names
        assert "content/content.json" in names

    def test_h5p_json_structure(self) -> None:
        buf = h5p_builder.build([_mc_question()], "My Quiz")
        h5p_json, _ = _unpack_h5p(buf)

        assert h5p_json["title"] == "My Quiz"
        assert h5p_json["mainLibrary"] == "H5P.QuestionSet"
        assert h5p_json["language"] == "en"
        assert "div" in h5p_json["embedTypes"]

    def test_content_json_structure(self) -> None:
        buf = h5p_builder.build([_mc_question()], "Test")
        _, content = _unpack_h5p(buf)

        assert content["introPage"]["showIntroPage"] is False
        assert content["passPercentage"] == 50
        assert len(content["questions"]) == 1
        assert content["endGame"]["showResultPage"] is True


class TestQuestionTypeMapping:
    def test_multiple_choice(self) -> None:
        buf = h5p_builder.build([_mc_question()], "MC Quiz")
        _, content = _unpack_h5p(buf)

        q = content["questions"][0]
        assert q["library"] == "H5P.MultiChoice 1.16"
        assert q["params"]["behaviour"]["singleAnswer"] is True
        assert len(q["params"]["answers"]) == 3
        # Check correct answer marked
        correct = [a for a in q["params"]["answers"] if a["correct"]]
        assert len(correct) == 1
        assert "4" in correct[0]["text"]

    def test_true_false(self) -> None:
        buf = h5p_builder.build([_tf_question()], "TF Quiz")
        _, content = _unpack_h5p(buf)

        q = content["questions"][0]
        assert q["library"] == "H5P.TrueFalse 1.8"
        assert q["params"]["correct"] == "true"

    def test_multi_select_single_answer_false(self) -> None:
        buf = h5p_builder.build([_multi_select_question()], "MS Quiz")
        _, content = _unpack_h5p(buf)

        q = content["questions"][0]
        assert q["library"] == "H5P.MultiChoice 1.16"
        assert q["params"]["behaviour"]["singleAnswer"] is False
        # Both correct answers marked
        correct = [a for a in q["params"]["answers"] if a["correct"]]
        assert len(correct) == 2

    def test_short_answer(self) -> None:
        buf = h5p_builder.build([_short_answer_question()], "SA Quiz")
        _, content = _unpack_h5p(buf)

        q = content["questions"][0]
        assert q["library"] == "H5P.Essay 1.5"
        assert "capital" in q["params"]["taskDescription"]
        assert len(q["params"]["keywords"]) == 1
        assert q["params"]["keywords"][0]["keyword"] == "Canberra"

    def test_fill_in_blank(self) -> None:
        buf = h5p_builder.build([_fill_blank_question()], "FB Quiz")
        _, content = _unpack_h5p(buf)

        q = content["questions"][0]
        assert q["library"] == "H5P.Blanks 1.14"
        assert "*H2O*" in q["params"]["text"]


class TestDependencies:
    def test_single_type_dependencies(self) -> None:
        buf = h5p_builder.build([_mc_question()], "Test")
        h5p_json, _ = _unpack_h5p(buf)

        deps = h5p_json["preloadedDependencies"]
        machine_names = [d["machineName"] for d in deps]
        assert "H5P.QuestionSet" in machine_names
        assert "H5P.MultiChoice" in machine_names

    def test_mixed_types_dependencies(self) -> None:
        questions = [_mc_question(), _tf_question(), _short_answer_question()]
        buf = h5p_builder.build(questions, "Mixed")  # type: ignore[arg-type]
        h5p_json, _ = _unpack_h5p(buf)

        deps = h5p_json["preloadedDependencies"]
        machine_names = [d["machineName"] for d in deps]
        assert "H5P.QuestionSet" in machine_names
        assert "H5P.MultiChoice" in machine_names
        assert "H5P.TrueFalse" in machine_names
        assert "H5P.Essay" in machine_names

    def test_no_duplicate_dependencies(self) -> None:
        questions = [_mc_question("Q1"), _mc_question("Q2")]
        buf = h5p_builder.build(questions, "Dupes")  # type: ignore[arg-type]
        h5p_json, _ = _unpack_h5p(buf)

        deps = h5p_json["preloadedDependencies"]
        machine_names = [d["machineName"] for d in deps]
        assert machine_names.count("H5P.MultiChoice") == 1


class TestEmptyQuestionSet:
    def test_empty_questions(self) -> None:
        buf = h5p_builder.build([], "Empty Quiz")
        h5p_json, content = _unpack_h5p(buf)

        assert h5p_json["title"] == "Empty Quiz"
        assert content["questions"] == []
        # Still has QuestionSet in dependencies
        deps = h5p_json["preloadedDependencies"]
        assert any(d["machineName"] == "H5P.QuestionSet" for d in deps)


class TestFeedback:
    def test_mc_feedback(self) -> None:
        q = _FakeQuestion(
            text="Q?",
            q_type="multiple_choice",
            options=[{"text": "A"}, {"text": "B"}],
            correct=["A"],
            explanation="A is correct because...",
        )
        buf = h5p_builder.build([q], "Test")  # type: ignore[arg-type]
        _, content = _unpack_h5p(buf)
        assert "overallFeedback" in content["questions"][0]["params"]

    def test_tf_feedback(self) -> None:
        q = _FakeQuestion(
            text="True?",
            q_type="true_false",
            options=[{"text": "True"}, {"text": "False"}],
            correct=["True"],
            explanation="Because reasons.",
        )
        buf = h5p_builder.build([q], "Test")  # type: ignore[arg-type]
        _, content = _unpack_h5p(buf)
        assert content["questions"][0]["params"]["feedbackOnCorrect"] == "Because reasons."


class TestSubContentIds:
    def test_unique_subcontent_ids(self) -> None:
        questions = [_mc_question("Q1"), _mc_question("Q2"), _tf_question()]
        buf = h5p_builder.build(questions, "Test")  # type: ignore[arg-type]
        _, content = _unpack_h5p(buf)

        ids = [q["subContentId"] for q in content["questions"]]
        assert len(ids) == len(set(ids))  # all unique
