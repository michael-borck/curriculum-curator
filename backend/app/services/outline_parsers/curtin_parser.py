"""
Curtin University outline parser — regex-based extraction for Curtin's
standard unit outline PDF format (OASIS-generated).

Key insight: Curtin's OASIS PDFs use NotoSansSCThin with a broken CMap that
maps digits to \x00 when extracted by pypdf/pdfplumber.  pymupdf (MuPDF)
handles this correctly, so it is used as the primary PDF extractor here.

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
    """Extract text from PDF bytes.

    Prefers pymupdf (MuPDF) because Curtin's OASIS PDFs use a NotoSansSCThin
    font with a broken CMap — pypdf/pdfplumber silently drop all digits.
    """
    # Try pymupdf first (handles Curtin's broken font encoding)
    try:
        import pymupdf  # noqa: PLC0415

        doc = pymupdf.open(stream=content, filetype="pdf")
        # pymupdf's get_text() is typed as returning Any — coerce to str
        # explicitly so the join call has an iterable of real strings.
        return "\n\n".join(str(page.get_text()) for page in doc)
    except ImportError:
        logger.warning("pymupdf not installed — falling back to pypdf (digits may be missing from Curtin PDFs)")
    except Exception:
        logger.warning("pymupdf extraction failed — falling back to pypdf")

    # Fallback to pypdf
    try:
        import pypdf  # noqa: PLC0415

        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        pass

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
# Curtin detection markers
# ---------------------------------------------------------------------------

_CURTIN_MARKERS = [
    "curtin university",
    "unit outline",
    "curtin.edu.au",
    "oasis.curtin",
    "oasis",
    "cricos provider code",
]

# ---------------------------------------------------------------------------
# Section heading patterns
# ---------------------------------------------------------------------------

_ULO_SECTION_RE = re.compile(
    r"(?:Unit\s+Learning\s+Outcomes?|Learning\s+Outcomes?)\s*\n",
    re.IGNORECASE,
)

_ASSESSMENT_SECTION_RE = re.compile(
    r"(?:Assessment\s+Schedule|Assessment\s+(?:Summary|Overview|Details|Tasks?)"
    r"|Summary\s+of\s+Assessment)\s*\n",
    re.IGNORECASE,
)

_DETAILED_ASSESSMENT_RE = re.compile(
    r"Detailed\s+Information\s+on\s+assessment\s+tasks?\s*\n",
    re.IGNORECASE,
)

_SCHEDULE_SECTION_RE = re.compile(
    r"(?:Program\s+Calendar|Teaching\s+Schedule|Unit\s+Schedule"
    r"|Weekly\s+Schedule|Schedule\s+of\s+Activities)\s*\n",
    re.IGNORECASE,
)

_TEXTBOOK_SECTION_RE = re.compile(
    r"(?:Learning\s+Resources|Prescribed\s+Text|Required\s+Text"
    r"|Textbook|Recommended\s+Reading|Reading\s+List)\s*\n",
    re.IGNORECASE,
)

_SYLLABUS_RE = re.compile(r"(?<=\n)Syllabus\s*\n")
_INTRODUCTION_RE = re.compile(r"(?<=\n)Introduction\s*\n")

_CREDIT_RE = re.compile(r"Credit\s+(?:value|Points?)\s*[:\-]?\s*\n?\s*(\d+)", re.IGNORECASE)

_SEMESTER_RE = re.compile(
    r"Semester\s+(\d)\s*,\s*(20\d{2})",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"\b(20\d{2})\b")

# Pattern for "ISYS6020 (V.1) Title Here" on the first few lines
_TITLE_LINE_RE = re.compile(
    r"^([A-Z]{2,6}\d{3,5})\s*\(V\.\d+\)\s*(.+)$",
    re.MULTILINE,
)

# Fallback: just a unit code
_UNIT_CODE_RE = re.compile(r"\b([A-Z]{2,6}\d{3,5})\b")

# Assessment schedule rows: "1\nAI Implementation Proposal\n40 %\nWeek:6"
# Title may span multiple lines (e.g. "Group Report and Prototype AI\nApplication")
_ASSESS_TASK_RE = re.compile(
    r"(?:^|\n)\s*(\d+)\s*\n"              # task number
    r"((?:(?!\d{1,3}\s*%).)+?)\n"          # title (everything up to the line before weight)
    r"\s*(\d{1,3})\s*%\s*\n"              # weight (e.g. "40 %" or "60 %")
    r"\s*(?:Week\s*:\s*([\d, ]+))?",        # optional week(s) — no newlines
    re.IGNORECASE | re.DOTALL,
)

# Week rows in Program Calendar: "1\n24\nFeb\nTopic Name\n..."
# or simpler "Week N ... Topic"
_CALENDAR_WEEK_RE = re.compile(
    r"(?:^|\n)\s*(\d{1,2})\s+\d{1,2}\s*\n?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(.+?)(?=\n\s*\d{1,2}\s+\d{1,2}\s*\n?\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|\nFaculty\s+of|\Z)",
    re.IGNORECASE | re.DOTALL,
)

# Simpler week pattern for "Week N: Topic" or just "N  Topic" in schedule
_WEEK_ROW_RE = re.compile(
    r"(?:Week|Wk)\s*(\d{1,2})\s*[:\-|]?\s*(.+)",
    re.IGNORECASE,
)

# Textbook pattern: "Author (Year). Title. Publisher."
_TEXTBOOK_ENTRY_RE = re.compile(
    r"([A-Z][a-z]+(?:,\s*[A-Z]\.?\s*(?:[A-Z]\.?\s*)?)?(?:,?\s*&\s*[A-Z][a-z]+(?:,\s*[A-Z]\.?\s*(?:[A-Z]\.?\s*)?)?)*)"
    r"\s*\((\d{4})\)\.\s*"
    r"(.+?)\.\s*"
    r"(.+?)\.",
    re.DOTALL,
)

_ISBN_RE = re.compile(r"ISBN\s*:\s*([\d\-]+)")


# All major section patterns used as end markers
_ALL_SECTIONS: list[re.Pattern[str]] = [
    _ULO_SECTION_RE,
    _ASSESSMENT_SECTION_RE,
    _DETAILED_ASSESSMENT_RE,
    _SCHEDULE_SECTION_RE,
    _TEXTBOOK_SECTION_RE,
    _SYLLABUS_RE,
    _INTRODUCTION_RE,
    re.compile(
        r"(?:Academic\s+Integrity|Special\s+Consideration|"
        r"Disability\s+Adjust|Student\s+Rights|"
        r"Referencing\s+Style|"
        r"(?<=\n)Curtin's\s+Graduate\s+Capabilities\n|"  # heading only (own line)
        r"Learning\s+Activities|Assessment\s+Moderation|"
        r"Pass\s+requirements|Late\s+Assessment|"
        r"Program\s+Calendar|Additional\s+information|"
        r"Recent\s+Unit\s+Changes|Design\s+Philosophy)",
        re.IGNORECASE,
    ),
]


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


def _strip_page_footers(text: str) -> str:
    """Remove Curtin's repeated page footer blocks.

    Pattern (pymupdf output):
        Faculty of Business and Law
        School of Management and Marketing
        ISYS6020 Artificial Intelligence in Business: Strategy and Management
        Bentley Perth Campus
        09 Feb 2026
        School of Management and Marketing
        Page 1 of 10
        CRICOS Provider Code 00301J
        The only authoritative version of this Unit Outline is to be found online in OASIS
    """
    return re.sub(
        r"Faculty of [^\n]+\n"
        r"School of [^\n]+\n"
        r"[A-Z]{2,6}\d{3,5}\s+[^\n]+\n"  # unit code + title
        r"[^\n]*Campus\n"
        r"\d{2}\s+\w+\s+\d{4}\n"  # date
        r"(?:School of [^\n]+\n)?"  # optional second school line
        r"(?:Page\s+\d+\s+of\s+\d+\n)?"  # optional page number
        r"CRICOS[^\n]*\n"
        r"[^\n]*OASIS\s*\n*",
        "\n",
        text,
    )


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
        lower = text[:5000].lower()
        matches = sum(1 for marker in _CURTIN_MARKERS if marker in lower)
        return matches >= 2

    def _extract_metadata(
        self, text: str
    ) -> tuple[str | None, str | None, int | None, int | None, str | None]:
        """Return (code, title, credit_points, year, semester)."""
        # Try the "CODE (V.N) Full Title" pattern first
        title_match = _TITLE_LINE_RE.search(text[:2000])
        if title_match:
            unit_code = title_match.group(1)
            unit_title = title_match.group(2).strip()
        else:
            code_match = _UNIT_CODE_RE.search(text[:2000])
            unit_code = code_match.group(1) if code_match else None
            unit_title = None

        # Credit points: "Credit value:\n25" or "Credit Points: 25"
        credit_match = _CREDIT_RE.search(text[:5000])
        credit_points = int(credit_match.group(1)) if credit_match else None

        # Semester and year: "Semester 1, 2026"
        sem_match = _SEMESTER_RE.search(text[:3000])
        if sem_match:
            semester_num = sem_match.group(1)
            year = int(sem_match.group(2))
            semester = f"semester_{semester_num}"
        else:
            year_match = _YEAR_RE.search(text[:3000])
            year = int(year_match.group(1)) if year_match else None
            semester = None

        return unit_code, unit_title, credit_points, year, semester

    def _extract_description(self, text: str) -> str | None:
        """Extract unit description from Syllabus and/or Introduction sections."""
        parts: list[str] = []

        syllabus = _section_between(text, _SYLLABUS_RE, _ALL_SECTIONS)
        if syllabus:
            parts.append(syllabus[:2000])

        intro = _section_between(text, _INTRODUCTION_RE, _ALL_SECTIONS)
        if intro:
            parts.append(intro[:2000])

        if not parts:
            return None
        combined = "\n\n".join(parts)
        return combined[:3000]

    def _extract_ulos(self, text: str) -> list[ExtractedULO]:
        """Extract ULOs from the 'Unit Learning Outcomes' section.

        Curtin format has a table like:
            On successful completion of this unit student can:
            Graduate Capabilities addressed
            1
            Critically and ethically analyse opportunities for...
            2
            Evaluate and plan implementation of AI applications...
        """
        ulo_section = _section_between(text, _ULO_SECTION_RE, _ALL_SECTIONS)
        if not ulo_section:
            return []

        # Skip the preamble about Graduate Capabilities
        # Look for "On successful completion" as the real start
        completion_match = re.search(
            r"On\s+successful\s+completion\s+of\s+this\s+unit\s+student\s+can:",
            ulo_section,
            re.IGNORECASE,
        )
        if completion_match:
            ulo_section = ulo_section[completion_match.end():]

        # Remove the "Graduate Capabilities addressed" header if present
        ulo_section = re.sub(
            r"Graduate\s+Capabilities\s+addressed\s*\n?", "", ulo_section, flags=re.IGNORECASE
        )

        # Remove repeated "On successful completion..." headers (from page breaks)
        ulo_section = re.sub(
            r"On\s+successful\s+completion\s+of\s+this\s+unit\s+student\s+can:\s*\n?",
            "\n",
            ulo_section,
            flags=re.IGNORECASE,
        )

        # Remove GC references (GC1, GC2, etc.) and the GC description block
        ulo_section = re.sub(r"GC\d+\s*:[^\n]*\n?", "", ulo_section)
        ulo_section = re.sub(r"Find\s+out\s+more\s+about\s+Curtin.*$", "", ulo_section, flags=re.IGNORECASE | re.DOTALL)

        # Now split by numbered items: a line that is just a digit
        # The pattern is: "\n1\nDescription text\n2\nDescription text\n"
        items = re.split(r"\n\s*(\d+)\s*\n", ulo_section)

        ulos: list[ExtractedULO] = []
        # items[0] is before the first number, then alternating: number, text
        i = 1
        while i < len(items) - 1:
            num = items[i].strip()
            desc_raw = items[i + 1].strip()
            # Clean up: join lines, remove extra whitespace
            desc = " ".join(desc_raw.split())
            if desc and len(desc) > 5:
                ulos.append(ExtractedULO(
                    code=f"ULO{num}",
                    description=desc[:500],
                    bloom_level=_guess_bloom(desc),
                ))
            i += 2

        return ulos

    def _extract_assessments(self, text: str) -> list[ExtractedAssessment]:
        """Extract assessments from the Assessment Schedule table.

        Curtin format:
            Task  Value%  Date Due  ULOs  Late?  Extensions?
            1
            AI Implementation Proposal
            40 %
            Week:6
            Day:Friday 27 March 2026
            ...
        """
        # Use specific end markers for assessment schedule — the generic _ALL_SECTIONS
        # matches column headers like "Late Assessments Accepted?" inside the table.
        assess_end_markers = [
            _DETAILED_ASSESSMENT_RE,
            re.compile(r"\*Please\s+refer\s+to", re.IGNORECASE),
            _SCHEDULE_SECTION_RE,
        ]
        assess_section = _section_between(text, _ASSESSMENT_SECTION_RE, assess_end_markers)
        if not assess_section:
            return []

        assessments: list[ExtractedAssessment] = []

        # Try structured pattern: "N\nTitle\nNN %\nWeek:N"
        for m in _ASSESS_TASK_RE.finditer(assess_section):
            title = " ".join(m.group(2).split())  # normalize whitespace
            weight = float(m.group(3))
            due_week_raw = m.group(4)

            # Parse due week — may be "6" or "11,13, Exam Period"
            due_week: int | None = None
            if due_week_raw:
                first_num = re.search(r"\d+", due_week_raw)
                if first_num:
                    due_week = int(first_num.group())

            if title and weight > 0:
                category = self._guess_assessment_category(title)
                assessments.append(ExtractedAssessment(
                    title=title, category=category, weight=weight, due_week=due_week,
                ))

        # If structured pattern didn't work, try "Title NN%" fallback
        if not assessments:
            fallback_re = re.compile(r"(.+?)\s+(\d{1,3})\s*%", re.IGNORECASE)
            for m in fallback_re.finditer(assess_section):
                title = m.group(1).strip().rstrip("|").strip()
                weight = float(m.group(2))
                if title and weight > 0 and len(title) > 3:
                    due_match = re.search(
                        r"[Ww](?:ee)?k\s*:?\s*(\d{1,2})",
                        assess_section[m.start():m.end() + 150],
                    )
                    assessments.append(ExtractedAssessment(
                        title=title,
                        category=self._guess_assessment_category(title),
                        weight=weight,
                        due_week=int(due_match.group(1)) if due_match else None,
                    ))

        return assessments

    @staticmethod
    def _guess_assessment_category(title: str) -> str:
        """Guess assessment category from title keywords."""
        lower = title.lower()
        if any(w in lower for w in ("exam", "test", "quiz")):
            return "exam"
        if any(w in lower for w in ("report", "essay", "paper")):
            return "report"
        if any(w in lower for w in ("project", "prototype", "application")):
            return "project"
        if any(w in lower for w in ("presentation", "dragon", "pitch")):
            return "presentation"
        if "proposal" in lower:
            return "assignment"
        return "assignment"

    def _extract_weeks(self, text: str) -> list[ExtractedWeek]:  # noqa: PLR0912
        """Extract weekly schedule from Program Calendar.

        Curtin format is a table with columns:
            Week | Begin Date | Topic | Content | Before the Lab | Readings | Assessment Due

        In pymupdf text it appears as:
            O  24 Feb  Orientation  Unit introduction...
            1  24\nFeb  AI Transformation Landscape  Three Horizons...
        """
        sched_section = _section_between(text, _SCHEDULE_SECTION_RE, _ALL_SECTIONS)
        if not sched_section:
            return []

        # Strip page footers that may appear mid-table
        sched_section = _strip_page_footers(sched_section)

        weeks: list[ExtractedWeek] = []

        # The Program Calendar in pymupdf output looks like:
        #   O\n9 Feb\nOrientation\n...
        #   1\n16\nFeb\nAI\nTransformation\nLandscape\n...
        #   2\n23\nFeb\nOpportunity\nIdentification &\nEthics\n...
        # Each week block starts with a number (or "O") at the start of a line,
        # followed by a date, then topic/content columns as successive lines.

        lines = sched_section.split("\n")

        # Skip column headers (Week, Begin Date, Topic, etc.)
        start = 0
        for i, line in enumerate(lines):
            if re.search(r"Assessment\s*\n?Due|Due$", line, re.IGNORECASE):
                start = i + 1
                break
            if re.search(r"^Topic$|^Content$", line.strip(), re.IGNORECASE) and i > 0:
                start = i + 1

        # Week-start detection: a line that is just a number (or "O"),
        # followed within 1-2 lines by a date (day + month name).
        # This distinguishes week numbers (1, 2, 3...) from day numbers (16, 23, 30...).
        _month_re = re.compile(
            r"^\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
            re.IGNORECASE,
        )

        # Find all week boundaries
        week_starts: list[tuple[int, str]] = []  # (line_index, week_id)
        for i in range(start, len(lines)):
            line = lines[i].strip()

            # Check for inline format: "O  9 Feb  ..."
            m_inline = re.match(
                r"^\s*(O|\d{1,2})\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
                line,
                re.IGNORECASE,
            )
            if m_inline:
                week_starts.append((i, m_inline.group(1)))
                continue

            # Check for split format: line is just "1", next line is "16", then "Feb"
            m_num = re.match(r"^\s*(O|\d{1,2})\s*$", line)
            if m_num:
                week_id = m_num.group(1)
                # Look ahead: is the next non-empty line a day number, followed by a month?
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    next_line = lines[j].strip()
                    # next_line should be a day number (e.g. "16") or "N Mon" (e.g. "9 Feb")
                    if re.match(r"^\d{1,2}$", next_line):
                        # Check if line after that is a month
                        k = j + 1
                        while k < len(lines) and not lines[k].strip():
                            k += 1
                        if k < len(lines) and _month_re.match(lines[k].strip()):
                            week_starts.append((i, week_id))
                            continue
                    elif re.match(r"^\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", next_line, re.IGNORECASE):
                        week_starts.append((i, week_id))
                        continue

        # Extract topic from each week block
        for idx, (line_idx, week_id) in enumerate(week_starts):
            if week_id == "O":
                continue
            if not week_id.isdigit():
                continue

            # Determine block end
            block_end = week_starts[idx + 1][0] if idx + 1 < len(week_starts) else len(lines)
            block_lines = [ln.strip() for ln in lines[line_idx + 1:block_end] if ln.strip()]

            # Skip date lines (e.g. "16", "Feb", "9 Feb", "2 Mar")
            _date_part_re = re.compile(
                r"^\d{1,2}$"
                r"|^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*$"
                r"|^\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
                re.IGNORECASE,
            )
            content_start = 0
            for j, bl in enumerate(block_lines):
                if _date_part_re.match(bl):
                    content_start = j + 1
                else:
                    break

            content_lines = block_lines[content_start:]
            if not content_lines:
                continue

            # The topic is the first column — typically 1-3 short words split
            # across lines. The next column ("Content") tends to have longer
            # descriptive phrases with commas. Join short lines as topic.
            topic_parts: list[str] = []
            for cl in content_lines:
                # Stop at obvious non-topic content
                if cl == "—" or re.match(r"^(?:AIM|AAI|Assessment|Compile|Review|No scheduled|Teams)", cl):
                    break
                # Stop if this line contains commas (likely Content column)
                if topic_parts and "," in cl:
                    break
                topic_parts.append(cl)
                joined = " ".join(topic_parts)
                # Topic column is narrow — typically 1-3 short lines.
                # Once we have a reasonable phrase, stop before the Content column.
                if len(topic_parts) >= 2 and len(joined) > 18:
                    break
                if len(joined) > 28:
                    break

            topic = " ".join(topic_parts).strip().rstrip("&").strip()[:300]
            if topic:
                # Collect remaining lines as activities (first 2-3)
                activity_lines = content_lines[len(topic_parts):len(topic_parts) + 3]
                activities = [" ".join(al.split()) for al in activity_lines if len(al) > 5 and al != "—"]

                weeks.append(ExtractedWeek(
                    week_number=int(week_id),
                    topic=topic,
                    activities=activities[:3],
                ))

        # Fallback: try simpler "Week N: Topic" pattern
        if not weeks:
            for m in _WEEK_ROW_RE.finditer(sched_section):
                topic = m.group(2).strip().split("\n")[0].strip()[:300]
                if topic:
                    weeks.append(ExtractedWeek(week_number=int(m.group(1)), topic=topic))

        return weeks

    def _extract_textbooks(self, text: str) -> list[ExtractedTextbook]:
        """Extract textbooks from Learning Resources section.

        Curtin format:
            Author, F. (2021). Title. Publisher. (Abbreviated as X)
            Electronic:No
            Essential:Yes
            Resource Type: Book
            ISBN: 978-...
        """
        tb_section = _section_between(text, _TEXTBOOK_SECTION_RE, _ALL_SECTIONS)
        if not tb_section:
            return []

        textbooks: list[ExtractedTextbook] = []

        # Find author-year-title entries
        for m in _TEXTBOOK_ENTRY_RE.finditer(tb_section):
            authors = m.group(1).strip()
            year = m.group(2)
            title = m.group(3).strip()
            publisher = m.group(4).strip()

            # Look for Essential:Yes/No after this entry
            after = tb_section[m.end():m.end() + 200]
            essential_match = re.search(r"Essential\s*:\s*(Yes|No)", after, re.IGNORECASE)
            required = essential_match.group(1).lower() == "yes" if essential_match else True

            # Look for ISBN
            isbn_match = _ISBN_RE.search(after)
            isbn = isbn_match.group(1) if isbn_match else None

            # Clean up title (remove trailing parenthetical abbreviations)
            title = re.sub(r"\s*\(Abbreviated\s+as\s+\w+\)\s*$", "", title)

            full_title = f"{authors} ({year}). {title}. {publisher}"

            textbooks.append(ExtractedTextbook(
                title=full_title[:300],
                authors=authors,
                isbn=isbn or "",
                required=required,
            ))

        # If regex didn't match, try line-based fallback
        if not textbooks:
            for raw_line in tb_section.split("\n"):
                line = raw_line.strip()
                if len(line) > 30 and re.search(r"\(\d{4}\)", line):
                    textbooks.append(ExtractedTextbook(title=line[:300], required=True))

        return textbooks

    def _extract_supplementary(self, text: str) -> list[ExtractedSnippet]:
        supplementary: list[ExtractedSnippet] = []
        headings = [
            (r"Academic\s+Integrity\n", "Academic Integrity"),
            (r"Graduate\s+(?:Attributes|Capabilities)\n", "Graduate Capabilities"),
            (r"Special\s+Consideration\n", "Special Consideration"),
            (r"Referencing\s+(?:Style|style)\n", "Referencing Style"),
            (r"Design\s+Philosophy\n", "Design Philosophy"),
        ]
        for pattern_str, heading in headings:
            pat = re.compile(pattern_str, re.IGNORECASE)
            section = _section_between(text, pat, _ALL_SECTIONS)
            if section and len(section) > 20:
                supplementary.append(ExtractedSnippet(heading=heading, content=section[:1000]))
        return supplementary

    def _extract_prerequisites(self, text: str) -> str | None:
        """Extract prerequisites from the metadata section."""
        m = re.search(r"Pre-requisite\s+units?\s*:\s*\n?\s*(.+?)(?:\n|$)", text[:5000], re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            return val if val.lower() != "nil" else None
        return None

    def _extract_delivery_mode(self, text: str) -> str | None:
        """Extract mode of study (Internal/External/Online)."""
        m = re.search(r"Mode\s+of\s+study\s*:\s*\n?\s*(\w+)", text[:5000], re.IGNORECASE)
        return m.group(1).strip() if m else None

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

        # Strip page footers for cleaner parsing
        clean_text = _strip_page_footers(text)

        unit_code, unit_title, credit_points, year, semester = self._extract_metadata(clean_text)
        description = self._extract_description(clean_text)
        ulos = self._extract_ulos(clean_text)
        if not ulos:
            warnings.append("Could not extract learning outcomes.")
        assessments = self._extract_assessments(clean_text)
        if not assessments:
            warnings.append("Could not extract assessments.")
        weeks = self._extract_weeks(clean_text)
        if not weeks:
            warnings.append("Could not extract weekly schedule.")

        prerequisites = self._extract_prerequisites(text)
        delivery_mode = self._extract_delivery_mode(text)

        fields_found = sum([
            bool(unit_code), bool(unit_title), bool(ulos),
            bool(weeks), bool(assessments), bool(description),
        ])
        confidence = min(1.0, 0.3 + fields_found * 0.12)

        return OutlineParseResult(
            unit_code=unit_code,
            unit_title=unit_title,
            description=description,
            credit_points=credit_points,
            duration_weeks=len(weeks) if weeks else None,
            year=year,
            semester=semester,
            prerequisites=prerequisites,
            delivery_mode=delivery_mode,
            learning_outcomes=ulos,
            weekly_schedule=weeks,
            assessments=assessments,
            textbooks=self._extract_textbooks(text),
            supplementary_info=self._extract_supplementary(clean_text),
            confidence=confidence,
            parser_used=self.name,
            warnings=warnings,
        )
