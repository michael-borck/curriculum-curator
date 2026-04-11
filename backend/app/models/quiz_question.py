"""
Quiz question data class — used by the QTI and H5P export services
to represent quiz questions extracted from TipTap content_json nodes.

Historically this was a SQLAlchemy model with a foreign key to the
legacy Content table. After the Content model was removed in the
pre-MVP cleanup, it became a plain Python data class that lives
entirely in memory — constructed on-the-fly from ``quizQuestion``
TipTap nodes via ``extract_quiz_nodes`` in unit_export_data.py.

The class shape is preserved so existing export code with
``list[QuizQuestion]`` type hints doesn't need updating.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class QuestionType(str, Enum):
    """Question type enumeration."""

    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"
    FILL_IN_BLANK = "fill_in_blank"
    MULTI_SELECT = "multi_select"
    CASE_STUDY = "case_study"
    SCENARIO = "scenario"


class QuizQuestion:
    """Plain-Python quiz question data class.

    Duck-types the old SQLAlchemy model for the export path's attribute
    reads (question_text, question_type, options, correct_answers,
    answer_explanation, points, feedback, etc.) without any database
    or session state. Instances are built on-the-fly from TipTap
    ``quizQuestion`` nodes and never persisted.
    """

    def __init__(
        self,
        *,
        question_id: str = "",
        question_text: str = "",
        question_type: str = "multiple_choice",
        order_index: int = 0,
        options: list[dict[str, Any]] | None = None,
        correct_answers: list[Any] | None = None,
        answer_explanation: str | None = None,
        points: float = 1.0,
        partial_credit: dict[str, Any] | None = None,
        feedback: dict[str, Any] | None = None,
        difficulty_level: str | None = None,
        bloom_level: str | None = None,
        learning_objective: str | None = None,
        question_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.id = question_id
        self.content_id = ""  # Legacy duck-typed field — always empty
        self.question_text = question_text
        self.question_type = question_type
        self.order_index = order_index
        self.options = options
        self.correct_answers = correct_answers
        self.answer_explanation = answer_explanation
        self.points = points
        self.partial_credit = partial_credit
        self.feedback = feedback
        self.difficulty_level = difficulty_level
        self.bloom_level = bloom_level
        self.learning_objective = learning_objective
        self.question_metadata = question_metadata

    # Property helpers (preserved from the SQLAlchemy version)

    @property
    def is_multiple_choice(self) -> bool:
        """Check if question is multiple choice."""
        return self.question_type == QuestionType.MULTIPLE_CHOICE.value

    @property
    def is_open_ended(self) -> bool:
        """Check if question is open-ended (requires text response)."""
        open_ended = {
            QuestionType.SHORT_ANSWER.value,
            QuestionType.LONG_ANSWER.value,
            QuestionType.CASE_STUDY.value,
            QuestionType.SCENARIO.value,
        }
        return self.question_type in open_ended

    @property
    def has_partial_credit(self) -> bool:
        """Check if question supports partial credit."""
        return self.partial_credit is not None and len(self.partial_credit) > 0

    @property
    def option_count(self) -> int:
        """Get number of options for multiple choice questions."""
        if not self.options or not isinstance(self.options, list):
            return 0
        return len(self.options)

    def __repr__(self) -> str:
        text = str(self.question_text)
        return (
            f"<QuizQuestion(id={self.id}, type={self.question_type!r}, "
            f"text={text[:50]!r}...)>"
        )
