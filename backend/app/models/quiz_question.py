"""
Quiz question model for detailed quiz support
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class QuestionType(str, Enum):
    """Question type enumeration"""

    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"
    FILL_IN_BLANK = "fill_in_blank"
    CASE_STUDY = "case_study"
    SCENARIO = "scenario"


class QuizQuestion(Base):
    """Quiz question model for detailed quiz support"""

    __tablename__ = "quiz_questions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Basic question information
    content_id = Column(GUID(), ForeignKey("contents.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)  # Markdown format
    question_type = Column(String(20), nullable=False, index=True)  # QuestionType enum
    order_index = Column(Integer, default=0, nullable=False)

    # Question options and answers (JSON format for flexibility)
    options = Column(JSON, nullable=True)  # List of options for MC questions
    correct_answers = Column(JSON, nullable=True)  # Correct answer(s)
    answer_explanation = Column(Text, nullable=True)  # Explanation in markdown

    # Grading and feedback
    points = Column(Float, default=1.0, nullable=False)
    partial_credit = Column(JSON, nullable=True)  # Partial credit rules
    feedback = Column(JSON, nullable=True)  # Feedback for different answers

    # Educational metadata
    difficulty_level = Column(String(20), nullable=True)
    bloom_level = Column(String(20), nullable=True)  # Associated Bloom's level
    learning_objective = Column(Text, nullable=True)

    # Additional metadata
    question_metadata = Column(JSON, nullable=True)  # Custom fields, settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    content = relationship("Content", back_populates="quiz_questions")

    def __repr__(self):
        return f"<QuizQuestion(id={self.id}, type='{self.question_type}', text='{self.question_text[:50]}...')>"

    @property
    def is_multiple_choice(self) -> bool:
        """Check if question is multiple choice"""
        return self.question_type == QuestionType.MULTIPLE_CHOICE.value

    @property
    def is_open_ended(self) -> bool:
        """Check if question is open-ended (requires text response)"""
        open_ended_types = [
            QuestionType.SHORT_ANSWER.value,
            QuestionType.LONG_ANSWER.value,
            QuestionType.CASE_STUDY.value,
            QuestionType.SCENARIO.value,
        ]
        return self.question_type in open_ended_types

    @property
    def has_partial_credit(self) -> bool:
        """Check if question supports partial credit"""
        partial_credit = self.partial_credit  # type: ignore[assignment]
        return partial_credit is not None and len(partial_credit) > 0  # type: ignore[arg-type]

    @property
    def option_count(self) -> int:
        """Get number of options for multiple choice questions"""
        if not self.options or not isinstance(self.options, list):
            return 0
        return len(self.options)
