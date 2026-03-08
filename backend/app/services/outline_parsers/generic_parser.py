"""
Generic LLM-powered outline parser — works with any institution or document format.

Sends the extracted document text to an LLM with a structured prompt, then
validates the response against ``OutlineParseResult``.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from app.services.outline_parsers.base import (
    ExtractedAssessment,
    ExtractedSnippet,
    ExtractedTextbook,
    ExtractedULO,
    ExtractedWeek,
    OutlineParser,
    OutlineParseResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM response schema (mirrors OutlineParseResult but is self-contained so
# the JSON schema sent to the LLM is clean and unambiguous)
# ---------------------------------------------------------------------------


class _LLMUlo(BaseModel):
    code: str = Field(description="e.g. ULO1, ULO2")
    description: str
    bloom_level: str = Field(
        description="One of: remember, understand, apply, analyse, evaluate, create"
    )


class _LLMWeek(BaseModel):
    week_number: int
    topic: str
    activities: list[str] = Field(default_factory=list)
    readings: list[str] = Field(default_factory=list)


class _LLMAssessment(BaseModel):
    title: str
    category: str = Field(description="e.g. exam, assignment, quiz, project, report")
    weight: float = Field(description="Percentage weight, e.g. 30.0")
    due_week: int | None = None
    description: str = ""


class _LLMTextbook(BaseModel):
    title: str
    authors: str = ""
    isbn: str = ""
    required: bool = True


class _LLMSnippet(BaseModel):
    heading: str
    content: str


class _LLMOutlineExtraction(BaseModel):
    """Schema given to the LLM for structured output."""

    unit_code: str | None = None
    unit_title: str | None = None
    description: str | None = None
    credit_points: int | None = None
    duration_weeks: int | None = None
    year: int | None = None
    semester: str | None = None
    prerequisites: str | None = None
    delivery_mode: str | None = None
    teaching_pattern: str | None = None
    learning_outcomes: list[_LLMUlo] = Field(default_factory=list)
    weekly_schedule: list[_LLMWeek] = Field(default_factory=list)
    assessments: list[_LLMAssessment] = Field(default_factory=list)
    textbooks: list[_LLMTextbook] = Field(default_factory=list)
    supplementary_info: list[_LLMSnippet] = Field(default_factory=list)
    confidence: float = Field(
        default=0.5, description="0.0-1.0 how confident you are in the extraction"
    )


# ---------------------------------------------------------------------------
# Parser implementation
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert curriculum analyst. You extract structured data from \
university unit outline documents. Be thorough but only extract information \
that is clearly present — do not invent data. If a field is not found, leave \
it null or empty. Place any content that doesn't fit the structured fields \
into supplementary_info with a descriptive heading."""

_USER_PROMPT_TEMPLATE = """\
Extract structured curriculum data from the following unit outline document.

The document may be from any university or educational institution.
Extract as much as you can identify:

- **Unit metadata**: code, title, description, credit points, duration (weeks), \
year, semester, prerequisites, delivery mode (e.g. face-to-face, online, hybrid), \
teaching pattern (e.g. "2hr lecture + 1hr tutorial per week")
- **Learning outcomes**: with Bloom's taxonomy level \
(remember/understand/apply/analyse/evaluate/create)
- **Weekly schedule**: week numbers, topic titles, activities, readings
- **Assessments**: title, category, percentage weight, due week
- **Textbooks**: title, authors, ISBN, required vs recommended
- **Supplementary info**: any other useful sections \
(e.g. policies, graduate attributes, special requirements)

--- DOCUMENT START ---
{document_text}
--- DOCUMENT END ---"""


def _extract_text(file_content: bytes, file_type: str) -> str:
    """Extract plain text from the uploaded file."""
    import io  # noqa: PLC0415

    if file_type == "pdf":
        try:
            import pypdf  # noqa: PLC0415

            reader = pypdf.PdfReader(io.BytesIO(file_content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except Exception as exc:
            logger.warning("pypdf extraction failed, trying PyPDF2: %s", exc)
            try:
                import PyPDF2  # type: ignore[import-untyped]  # noqa: PLC0415

                reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n\n".join(pages)
            except Exception:
                raise ValueError("Could not extract text from PDF") from exc

    if file_type == "docx":
        try:
            import docx  # type: ignore[import-untyped]  # noqa: PLC0415

            doc = docx.Document(io.BytesIO(file_content))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as exc:
            raise ValueError("Could not extract text from DOCX") from exc

    # txt / md / fallback
    return file_content.decode("utf-8", errors="ignore")


class GenericOutlineParser(OutlineParser):
    name = "generic"
    display_name = "Generic (AI-Powered)"
    description = (
        "Uses AI to extract structure from any unit outline document. "
        "Works with any institution or format."
    )
    supported_formats: ClassVar[list[str]] = ["pdf", "docx", "txt"]

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> OutlineParseResult:
        text = _extract_text(file_content, file_type)

        if not text.strip():
            return OutlineParseResult(
                confidence=0.0,
                parser_used=self.name,
                warnings=["Document appears to be empty or could not be read."],
            )

        # Truncate to ~60k chars to stay within context limits
        max_chars = 60_000
        if len(text) > max_chars:
            text = text[:max_chars]
            truncated = True
        else:
            truncated = False

        # Import LLMService lazily to avoid circular imports
        from app.services.llm_service import LLMService  # noqa: PLC0415

        llm = LLMService()

        user: Any = None
        db: Any = None
        if user_context:
            user = user_context.get("user")
            db = user_context.get("db")

        prompt = _USER_PROMPT_TEMPLATE.format(document_text=text)

        result, error = await llm.generate_structured_content(
            prompt=prompt,
            response_model=_LLMOutlineExtraction,
            user=user,
            db=db,
            temperature=0.3,
            max_retries=2,
        )

        if error or result is None:
            return OutlineParseResult(
                confidence=0.0,
                parser_used=self.name,
                warnings=[error or "LLM returned no result."],
            )

        assert isinstance(result, _LLMOutlineExtraction)

        warnings: list[str] = []
        if truncated:
            warnings.append(
                f"Document was truncated to {max_chars:,} characters — "
                "some content near the end may not have been extracted."
            )

        return OutlineParseResult(
            unit_code=result.unit_code,
            unit_title=result.unit_title,
            description=result.description,
            credit_points=result.credit_points,
            duration_weeks=result.duration_weeks,
            year=result.year,
            semester=result.semester,
            prerequisites=result.prerequisites,
            delivery_mode=result.delivery_mode,
            teaching_pattern=result.teaching_pattern,
            learning_outcomes=[
                ExtractedULO(
                    code=u.code, description=u.description, bloom_level=u.bloom_level
                )
                for u in result.learning_outcomes
            ],
            weekly_schedule=[
                ExtractedWeek(
                    week_number=w.week_number,
                    topic=w.topic,
                    activities=w.activities,
                    readings=w.readings,
                )
                for w in result.weekly_schedule
            ],
            assessments=[
                ExtractedAssessment(
                    title=a.title,
                    category=a.category,
                    weight=a.weight,
                    due_week=a.due_week,
                    description=a.description,
                )
                for a in result.assessments
            ],
            textbooks=[
                ExtractedTextbook(
                    title=t.title,
                    authors=t.authors,
                    isbn=t.isbn,
                    required=t.required,
                )
                for t in result.textbooks
            ],
            supplementary_info=[
                ExtractedSnippet(heading=s.heading, content=s.content)
                for s in result.supplementary_info
            ],
            confidence=result.confidence,
            parser_used=self.name,
            warnings=warnings,
        )
