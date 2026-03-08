"""
Curtin University outline parser — regex-based extraction for Curtin's
standard unit outline PDF format.

Falls back to the generic LLM parser if the document doesn't look like a
Curtin outline.
"""

from __future__ import annotations

import io
import logging
import re
from typing import ClassVar

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
# Helpers
# ---------------------------------------------------------------------------

_BLOOM_KEYWORDS: dict[str, list[str]] = {
    "remember": ["list", "define", "identify", "recall", "name", "state", "recognise"],
    "understand": [
        "describe",
        "explain",
        "summarise",
        "interpret",
        "discuss",
        "classify",
        "compare",
    ],
    "apply": ["apply", "demonstrate", "use", "implement", "solve", "calculate"],
    "analyse": ["analyse", "analyze", "examine", "differentiate", "investigate"],
    "evaluate": [
        "evaluate",
        "assess",
        "justify",
        "critique",
        "judge",
        "recommend",
    ],
    "create": ["create", "design", "develop", "construct", "produce", "propose"],
}


def _guess_bloom(text: str) -> str:
    """Guess Bloom's level from the first verb in the outcome text."""
    lower = text.lower().strip()
    for level, keywords in reversed(list(_BLOOM_KEYWORDS.items())):
        for kw in keywords:
            if lower.startswith(kw) or re.search(rf"\b{kw}\b", lower[:60]):
                return level
    return "understand"


def _extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        import pypdf  # noqa: PLC0415

        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        try:
            import PyPDF2  # type: ignore[import-untyped]  # noqa: PLC0415

            reader = PyPDF2.PdfReader(io.BytesIO(content))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError("Could not extract text from PDF") from exc


def _extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        import docx  # type: ignore[import-untyped]  # noqa: PLC0415

        doc = docx.Document(io.BytesIO(content))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as exc:
        raise ValueError("Could not extract text from DOCX") from exc


# ---------------------------------------------------------------------------
# Section extraction regexes (Curtin-specific headings)
# ---------------------------------------------------------------------------

# Curtin outlines typically use these section headings
_CURTIN_MARKERS = [
    "curtin university",
    "unit outline",
    "curtin.edu.au",
    "oasis.curtin",
]

_UNIT_CODE_RE = re.compile(
    r"\b([A-Z]{2,6}\s*\d{3,5})\b"
)

_ULO_SECTION_RE = re.compile(
    r"(?:Unit\s+Learning\s+Outcomes?|Learning\s+Outcomes?)\s*[\n:]",
    re.IGNORECASE,
)

_ULO_ITEM_RE = re.compile(
    r"(?:ULO\s*(\d+)|(\d+)\s*[.)]\s*)",
    re.IGNORECASE,
)

_ASSESSMENT_SECTION_RE = re.compile(
    r"(?:Assessment\s+(?:Summary|Overview|Details|Tasks?)|Summary\s+of\s+Assessment)",
    re.IGNORECASE,
)

_SCHEDULE_SECTION_RE = re.compile(
    r"(?:Teaching\s+Schedule|Unit\s+Schedule|Weekly\s+Schedule|Schedule\s+of\s+Activities)",
    re.IGNORECASE,
)

_TEXTBOOK_SECTION_RE = re.compile(
    r"(?:Prescribed\s+Text|Required\s+Text|Textbook|Recommended\s+Reading|Reading\s+List)",
    re.IGNORECASE,
)

_CREDIT_RE = re.compile(r"Credit\s+Points?\s*[:\-]?\s*(\d+)", re.IGNORECASE)

_SEMESTER_RE = re.compile(
    r"(?:Semester|Study\s+Period)\s*[:\-]?\s*(\d|[A-Za-z]+)",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"\b(20\d{2})\b")

_WEEK_ROW_RE = re.compile(
    r"(?:Week|Wk)\s*(\d{1,2})\s*[:\-|]?\s*(.+)",
    re.IGNORECASE,
)

_ASSESSMENT_ROW_RE = re.compile(
    r"(.+?)\s+(\d{1,3})\s*%",
    re.IGNORECASE,
)


def _section_between(
    text: str, start_re: re.Pattern[str], end_markers: list[re.Pattern[str]]
) -> str | None:
    """Extract text between a start heading and the next known heading."""
    m = start_re.search(text)
    if not m:
        return None
    start = m.end()
    end = len(text)
    for marker in end_markers:
        n = marker.search(text, start)
        if n and n.start() < end:
            end = n.start()
    return text[start:end].strip()


# All major section patterns used as end markers
_ALL_SECTIONS: list[re.Pattern[str]] = [
    _ULO_SECTION_RE,
    _ASSESSMENT_SECTION_RE,
    _SCHEDULE_SECTION_RE,
    _TEXTBOOK_SECTION_RE,
    re.compile(
        r"(?:Academic\s+Integrity|Special\s+Consideration|"
        r"Disability\s+Adjust|Student\s+Rights|"
        r"Referencing\s+Style|Graduate\s+Attributes)",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class CurtinOutlineParser(OutlineParser):
    name = "curtin"
    display_name = "Curtin University"
    description = (
        "Purpose-built parser for Curtin University's standard unit outline format. "
        "Higher accuracy for Curtin documents; falls back to Generic for others."
    )
    supported_formats: ClassVar[list[str]] = ["pdf", "docx", "txt"]

    def _is_curtin(self, text: str) -> bool:
        lower = text[:3000].lower()
        return any(marker in lower for marker in _CURTIN_MARKERS)

    def _extract_metadata(
        self, text: str
    ) -> tuple[str | None, str | None, int | None, int | None, str | None]:
        """Return (code, title, credit_points, year, semester)."""
        code_match = _UNIT_CODE_RE.search(text[:2000])
        unit_code = code_match.group(1).replace(" ", "") if code_match else None

        unit_title: str | None = None
        if code_match:
            after_code = text[code_match.end() : code_match.end() + 300]
            lines = [ln.strip() for ln in after_code.split("\n") if ln.strip()]
            if lines:
                unit_title = lines[0][:200]

        credit_match = _CREDIT_RE.search(text[:5000])
        credit_points = int(credit_match.group(1)) if credit_match else None

        year_match = _YEAR_RE.search(text[:3000])
        year = int(year_match.group(1)) if year_match else None

        sem_match = _SEMESTER_RE.search(text[:3000])
        semester_raw = sem_match.group(1) if sem_match else None
        semester: str | None = None
        if semester_raw:
            sem_map = {"1": "semester_1", "One": "semester_1", "2": "semester_2", "Two": "semester_2"}
            semester = sem_map.get(semester_raw, semester_raw.lower())

        return unit_code, unit_title, credit_points, year, semester

    def _extract_ulos(self, text: str) -> list[ExtractedULO]:
        ulo_section = _section_between(text, _ULO_SECTION_RE, _ALL_SECTIONS)
        if not ulo_section:
            return []
        items = re.split(r"(?:ULO\s*\d+|(?:\d+)\s*[.)])\s*", ulo_section)
        items = [item.strip() for item in items if item.strip() and len(item) > 10]
        ulos: list[ExtractedULO] = []
        for i, item in enumerate(items, 1):
            desc = item.split("\n")[0].strip()[:500]
            if desc:
                ulos.append(ExtractedULO(code=f"ULO{i}", description=desc, bloom_level=_guess_bloom(desc)))
        return ulos

    def _extract_assessments(self, text: str) -> list[ExtractedAssessment]:
        assess_section = _section_between(text, _ASSESSMENT_SECTION_RE, _ALL_SECTIONS)
        if not assess_section:
            return []
        assessments: list[ExtractedAssessment] = []
        for m in _ASSESSMENT_ROW_RE.finditer(assess_section):
            title = m.group(1).strip().rstrip("|").strip()
            weight = float(m.group(2))
            if title and weight > 0:
                due_match = re.search(
                    r"[Ww](?:ee)?k\s*(\d{1,2})", assess_section[m.start() : m.end() + 100]
                )
                assessments.append(ExtractedAssessment(
                    title=title, category="assignment", weight=weight,
                    due_week=int(due_match.group(1)) if due_match else None,
                ))
        return assessments

    def _extract_weeks(self, text: str) -> list[ExtractedWeek]:
        sched_section = _section_between(text, _SCHEDULE_SECTION_RE, _ALL_SECTIONS)
        if not sched_section:
            return []
        weeks: list[ExtractedWeek] = []
        for m in _WEEK_ROW_RE.finditer(sched_section):
            topic = m.group(2).strip().split("\n")[0].strip()[:300]
            if topic:
                weeks.append(ExtractedWeek(week_number=int(m.group(1)), topic=topic))
        return weeks

    def _extract_textbooks(self, text: str) -> list[ExtractedTextbook]:
        tb_section = _section_between(text, _TEXTBOOK_SECTION_RE, _ALL_SECTIONS)
        if not tb_section:
            return []
        textbooks: list[ExtractedTextbook] = []
        for raw_line in tb_section.split("\n"):
            line = raw_line.strip()
            if len(line) > 15 and not line.lower().startswith(("note", "student")):
                pos = text.find(line)
                required = "recommended" not in text[max(0, pos - 200) : pos].lower()
                textbooks.append(ExtractedTextbook(title=line[:300], required=required))
        return textbooks

    def _extract_supplementary(self, text: str) -> list[ExtractedSnippet]:
        supplementary: list[ExtractedSnippet] = []
        headings = [
            (r"Academic\s+Integrity", "Academic Integrity"),
            (r"Graduate\s+Attributes", "Graduate Attributes"),
            (r"Special\s+Consideration", "Special Consideration"),
            (r"Referencing\s+Style", "Referencing Style"),
        ]
        for pattern_str, heading in headings:
            pat = re.compile(pattern_str, re.IGNORECASE)
            section = _section_between(text, pat, _ALL_SECTIONS)
            if section and len(section) > 20:
                supplementary.append(ExtractedSnippet(heading=heading, content=section[:1000]))
        return supplementary

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        *,
        user_context: dict[str, object] | None = None,
    ) -> OutlineParseResult:
        # --- extract raw text ---
        if file_type == "pdf":
            text = _extract_text_from_pdf(file_content)
        elif file_type == "docx":
            text = _extract_text_from_docx(file_content)
        else:
            text = file_content.decode("utf-8", errors="ignore")

        if not text.strip():
            return OutlineParseResult(
                confidence=0.0, parser_used=self.name,
                warnings=["Document appears to be empty."],
            )

        # --- check if this looks like a Curtin outline ---
        if not self._is_curtin(text):
            logger.info("Document does not appear to be a Curtin outline - falling back to generic.")
            from app.services.outline_parsers.generic_parser import GenericOutlineParser  # noqa: PLC0415, I001

            result = await GenericOutlineParser().parse(
                file_content, filename, file_type, user_context=user_context
            )
            result.warnings.insert(0, "Document did not match Curtin format - used generic AI parser instead.")
            return result

        warnings: list[str] = []
        unit_code, unit_title, credit_points, year, semester = self._extract_metadata(text)
        ulos = self._extract_ulos(text)
        if not ulos:
            warnings.append("Could not extract learning outcomes.")
        assessments = self._extract_assessments(text)
        if not assessments:
            warnings.append("Could not extract assessments.")
        weeks = self._extract_weeks(text)
        if not weeks:
            warnings.append("Could not extract weekly schedule.")

        desc_pat = re.compile(r"Unit\s+Description\s*[:\n]", re.IGNORECASE)
        description = _section_between(text, desc_pat, _ALL_SECTIONS)
        if description:
            description = description[:2000]

        fields_found = sum([bool(unit_code), bool(unit_title), bool(ulos), bool(weeks), bool(assessments)])
        confidence = min(1.0, 0.4 + fields_found * 0.12)

        return OutlineParseResult(
            unit_code=unit_code, unit_title=unit_title, description=description,
            credit_points=credit_points, duration_weeks=len(weeks) if weeks else None,
            year=year, semester=semester,
            learning_outcomes=ulos, weekly_schedule=weeks, assessments=assessments,
            textbooks=self._extract_textbooks(text),
            supplementary_info=self._extract_supplementary(text),
            confidence=confidence, parser_used=self.name, warnings=warnings,
        )
