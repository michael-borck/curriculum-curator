"""
Quiz question model for detailed quiz support
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import GUID

if TYPE_CHECKING:
    from app.models.content import Content


class QuestionType(str, Enum):
    """Question type enumeration"""

    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"
    FILL_IN_BLANK = "fill_in_blank"
    MULTI_SELECT = "multi_select"
    CASE_STUDY = "case_study"
    SCENARIO = "scenario"


class QuizQuestion(Base):
    """Quiz question model for detailed quiz support"""

    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Basic question information
    content_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("contents.id"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown format
    question_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # QuestionType enum
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Question options and answers (JSON format for flexibility)
    options: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # List of options for MC questions
    correct_answers: Mapped[list[Any] | None] = mapped_column(
        JSON, default=None
    )  # Correct answer(s)
    answer_explanation: Mapped[str | None] = mapped_column(
        Text, default=None
    )  # Explanation in markdown

    # Grading and feedback
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    partial_credit: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Partial credit rules
    feedback: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Feedback for different answers

    # Educational metadata
    difficulty_level: Mapped[str | None] = mapped_column(String(20), default=None)
    bloom_level: Mapped[str | None] = mapped_column(
        String(20), default=None
    )  # Associated Bloom's level
    learning_objective: Mapped[str | None] = mapped_column(Text, default=None)

    # Additional metadata
    question_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, default=None
    )  # Custom fields, settings

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    content: Mapped[Content] = relationship("Content", back_populates="quiz_questions")

    def __repr__(self) -> str:
        question_text = str(self.question_text)
        return f"<QuizQuestion(id={self.id}, type='{self.question_type}', text='{question_text[:50]}...')>"

    @property
    def is_multiple_choice(self) -> bool:
        """Check if question is multiple choice"""
        return str(self.question_type) == QuestionType.MULTIPLE_CHOICE.value

    @property
    def is_open_ended(self) -> bool:
        """Check if question is open-ended (requires text response)"""
        open_ended_types = [
            QuestionType.SHORT_ANSWER.value,
            QuestionType.LONG_ANSWER.value,
            QuestionType.CASE_STUDY.value,
            QuestionType.SCENARIO.value,
        ]
        return str(self.question_type) in open_ended_types

    @property
    def has_partial_credit(self) -> bool:
        """Check if question supports partial credit"""
        partial_credit = self.partial_credit
        return partial_credit is not None and len(partial_credit) > 0

    @property
    def option_count(self) -> int:
        """Get number of options for multiple choice questions"""
        options = self.options
        if not options or not isinstance(options, list):
            return 0
        return len(options)
