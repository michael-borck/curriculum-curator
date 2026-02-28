"""
H5P Question Set package builder.

Generates .h5p (ZIP) archives containing a Question Set from quiz questions.
The package contains only content.json + h5p.json — the H5P player JS/CSS
is managed by the LMS (Moodle, WordPress, etc.).
"""

import json
import uuid
import zipfile
from io import BytesIO
from typing import Any, ClassVar

from app.models.quiz_question import QuizQuestion

# H5P library version dicts (module-level to avoid ClassVar complexity)
_QUESTION_SET_LIB: dict[str, Any] = {"machineName": "H5P.QuestionSet", "majorVersion": 1, "minorVersion": 20}
_MULTI_CHOICE_LIB: dict[str, Any] = {"machineName": "H5P.MultiChoice", "majorVersion": 1, "minorVersion": 16}
_TRUE_FALSE_LIB: dict[str, Any] = {"machineName": "H5P.TrueFalse", "majorVersion": 1, "minorVersion": 8}
_ESSAY_LIB: dict[str, Any] = {"machineName": "H5P.Essay", "majorVersion": 1, "minorVersion": 5}
_BLANKS_LIB: dict[str, Any] = {"machineName": "H5P.Blanks", "majorVersion": 1, "minorVersion": 14}

# Question type → H5P library mapping
_TYPE_MAP: dict[str, dict[str, Any]] = {
    "multiple_choice": _MULTI_CHOICE_LIB,
    "multi_select": _MULTI_CHOICE_LIB,
    "true_false": _TRUE_FALSE_LIB,
    "short_answer": _ESSAY_LIB,
    "fill_in_blank": _BLANKS_LIB,
}

_TYPE_LABELS: dict[str, str] = {
    "multiple_choice": "Multiple Choice",
    "multi_select": "Multiple Choice",
    "true_false": "True/False",
    "short_answer": "Essay",
    "fill_in_blank": "Fill in the Blanks",
}


class H5PQuestionSetBuilder:
    """Builds an H5P Question Set package (.h5p ZIP) from quiz questions."""

    QUESTION_SET_LIB: ClassVar[dict[str, Any]] = _QUESTION_SET_LIB

    def build(self, questions: list[QuizQuestion], title: str) -> BytesIO:
        """Create .h5p ZIP with content.json + h5p.json.

        Args:
            questions: List of quiz questions (DB models or duck-typed equivalents).
            title: Title for the question set.

        Returns:
            BytesIO containing the .h5p ZIP archive.
        """
        h5p_questions: list[dict[str, Any]] = []
        used_libs: dict[str, dict[str, Any]] = {}

        for q in questions:
            q_type = str(q.question_type)
            lib = _TYPE_MAP.get(q_type, _MULTI_CHOICE_LIB)
            lib_key = lib["machineName"]
            used_libs[lib_key] = lib

            h5p_item = self._build_question(q, q_type, lib)
            h5p_questions.append(h5p_item)

        content_json = self._build_content_json(h5p_questions)
        h5p_json = self._build_h5p_json(title, used_libs)

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("h5p.json", json.dumps(h5p_json, indent=2))
            zf.writestr("content/content.json", json.dumps(content_json, indent=2))
        buf.seek(0)
        return buf

    def _build_question(
        self,
        q: QuizQuestion,
        q_type: str,
        lib: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a single H5P question item."""
        lib_string = f"{lib['machineName']} {lib['majorVersion']}.{lib['minorVersion']}"
        label = _TYPE_LABELS.get(q_type, "Multiple Choice")

        if q_type in ("multiple_choice", "multi_select"):
            params = self._build_multi_choice(q, single_answer=(q_type == "multiple_choice"))
        elif q_type == "true_false":
            params = self._build_true_false(q)
        elif q_type == "short_answer":
            params = self._build_essay(q)
        elif q_type == "fill_in_blank":
            params = self._build_blanks(q)
        else:
            params = self._build_multi_choice(q, single_answer=True)

        return {
            "library": lib_string,
            "params": params,
            "subContentId": str(uuid.uuid4()),
            "metadata": {
                "contentType": label,
                "title": str(q.question_text)[:100],
            },
        }

    def _build_multi_choice(self, q: QuizQuestion, *, single_answer: bool) -> dict[str, Any]:
        """Build H5P.MultiChoice params."""
        options = q.options or []
        correct_set = set(q.correct_answers or [])

        answers: list[dict[str, Any]] = []
        for opt in options:
            opt_text = str(opt.get("text", "")) if isinstance(opt, dict) else str(opt)
            answers.append({
                "text": f"<p>{opt_text}</p>",
                "correct": opt_text in correct_set,
                "tipsAndFeedback": {"tip": "", "chosenFeedback": "", "notChosenFeedback": ""},
            })

        params: dict[str, Any] = {
            "question": f"<p>{q.question_text}</p>",
            "answers": answers,
            "behaviour": {
                "singleAnswer": single_answer,
                "enableRetry": True,
                "enableSolutionsButton": True,
                "enableCheckButton": True,
                "type": "auto",
                "confirmCheckDialog": False,
                "confirmRetryDialog": False,
                "autoCheck": False,
                "passPercentage": 100,
                "showSolutionsRequiresInput": True,
            },
        }

        if q.answer_explanation:
            params["overallFeedback"] = [{"from": 0, "to": 100, "feedback": q.answer_explanation}]

        return params

    def _build_true_false(self, q: QuizQuestion) -> dict[str, Any]:
        """Build H5P.TrueFalse params."""
        correct_answers = q.correct_answers or []
        correct_text = correct_answers[0] if correct_answers else "True"
        correct = correct_text.lower() in ("true", "yes", "1")

        params: dict[str, Any] = {
            "question": f"<p>{q.question_text}</p>",
            "correct": "true" if correct else "false",
            "behaviour": {
                "enableRetry": True,
                "enableSolutionsButton": True,
                "enableCheckButton": True,
                "confirmCheckDialog": False,
                "confirmRetryDialog": False,
            },
            "l10n": {
                "trueText": "True",
                "falseText": "False",
            },
        }

        if q.answer_explanation:
            params["feedbackOnCorrect"] = q.answer_explanation
            params["feedbackOnWrong"] = q.answer_explanation

        return params

    def _build_essay(self, q: QuizQuestion) -> dict[str, Any]:
        """Build H5P.Essay params (for short answer questions)."""
        keywords: list[dict[str, Any]] = [
            {
                "keyword": answer,
                "alternatives": [],
                "forgiveMistakes": True,
                "caseSensitive": False,
            }
            for answer in (q.correct_answers or [])
        ]

        params: dict[str, Any] = {
            "taskDescription": f"<p>{q.question_text}</p>",
            "keywords": keywords,
            "behaviour": {
                "minimumLength": 1,
                "inputFieldSize": 10,
                "enableRetry": True,
                "ignoreScoring": False,
                "pointsHost": float(q.points),
            },
        }

        if q.answer_explanation:
            params["solution"] = {"sample": q.answer_explanation}

        return params

    def _build_blanks(self, q: QuizQuestion) -> dict[str, Any]:
        """Build H5P.Blanks params (for fill-in-the-blank questions)."""
        # Build the text with blanks — replace ___ with *answer*
        question_text = str(q.question_text)
        correct_answers = q.correct_answers or []

        if correct_answers and "___" in question_text:
            # Replace first ___ with the correct answer in asterisks
            blank_answer = "/".join(f"*{a}*" for a in correct_answers)
            question_text = question_text.replace("___", blank_answer, 1)
        elif correct_answers:
            # Append a blank at the end
            blank_answer = "/".join(f"*{a}*" for a in correct_answers)
            question_text = f"{question_text} {blank_answer}"

        params: dict[str, Any] = {
            "text": f"<p>{question_text}</p>",
            "questions": [f"<p>{question_text}</p>"],
            "behaviour": {
                "enableRetry": True,
                "enableSolutionsButton": True,
                "enableCheckButton": True,
                "caseSensitive": False,
                "autoCheck": False,
                "acceptSpellingErrors": True,
            },
        }

        if q.answer_explanation:
            params["overallFeedback"] = [{"from": 0, "to": 100, "feedback": q.answer_explanation}]

        return params

    def _build_content_json(self, questions: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the content/content.json structure."""
        return {
            "introPage": {"showIntroPage": False},
            "progressType": "dots",
            "passPercentage": 50,
            "questions": questions,
            "endGame": {
                "showResultPage": True,
                "showSolutionButton": True,
                "showRetryButton": True,
            },
            "override": {
                "checkButton": True,
            },
            "texts": {
                "prevButton": "Previous question",
                "nextButton": "Next question",
                "finishButton": "Finish",
                "textualProgress": "Question: @current of @total questions",
                "jumpToQuestion": "Question %d of %total",
                "questionLabel": "Question",
                "readSpeakerProgress": "Question @current of @total",
                "unansweredText": "Unanswered",
                "answeredText": "Answered",
                "currentQuestionText": "Current question",
            },
        }

    def _build_h5p_json(
        self,
        title: str,
        used_libs: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Build the h5p.json manifest."""
        dependencies = [_QUESTION_SET_LIB]
        dependencies.extend(
            lib for lib in used_libs.values() if lib["machineName"] != "H5P.QuestionSet"
        )

        return {
            "title": title,
            "mainLibrary": "H5P.QuestionSet",
            "language": "en",
            "embedTypes": ["div", "iframe"],
            "preloadedDependencies": dependencies,
        }


# Module-level singleton
h5p_builder = H5PQuestionSetBuilder()
