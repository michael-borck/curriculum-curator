"""
Tests for DocumentAnalyzerService.

The analyzer is pure logic over ExtractedDocument dataclasses (no DB, no
external calls), so tests build synthetic documents and exercise heading
detection, structure extraction, learning outcome / assessment / weekly
content parsing, and the course-structure mapping. Integration coverage
for real file imports lives in test_unified_import_pptx.py and the
round-trip tests — not duplicated here.
"""

import pytest

from app.models import BloomLevel, OutcomeType
from app.services.document_analyzer_service import (
    AnalyzedSection,
    DocumentAnalysis,
    DocumentAnalyzerService,
    DocumentType,
    ExtractedAssessment,
    ExtractedLearningOutcome,
    ExtractedWeeklyContent,
)
from app.services.pdf_parser_service import (
    ExtractedDocument,
    ExtractedPage,
    PDFMetadata,
)


@pytest.fixture
def analyzer() -> DocumentAnalyzerService:
    return DocumentAnalyzerService()


def _make_doc(
    text: str = "",
    title: str | None = None,
    pages: list[ExtractedPage] | None = None,
    toc: list[dict[str, object]] | None = None,
) -> ExtractedDocument:
    if pages is None:
        pages = [ExtractedPage(page_number=1, text=text)] if text else []
    return ExtractedDocument(
        metadata=PDFMetadata(title=title, page_count=len(pages)),
        pages=pages,
        full_text=text,
        toc=toc,
        extraction_method="pypdf",
    )


def _empty_analysis(**overrides: object) -> DocumentAnalysis:
    defaults: dict[str, object] = {
        "document_type": DocumentType.UNKNOWN,
        "title": None,
        "sections": [],
        "learning_outcomes": [],
        "assessments": [],
        "weekly_content": [],
        "key_concepts": [],
        "prerequisites": [],
        "references": [],
        "metadata": {},
    }
    defaults.update(overrides)
    return DocumentAnalysis(**defaults)  # pyright: ignore[reportArgumentType]


# ─── Document type identification ────────────────────────────


class TestIdentifyDocumentType:
    @pytest.mark.parametrize(
        ("text", "title", "expected"),
        [
            ("This Unit Outline describes ISYS1001.", None, DocumentType.UNIT_OUTLINE),
            ("Some content here.", "Lecture 3: Databases", DocumentType.LECTURE_NOTES),
            ("Welcome to the tutorial guide.", None, DocumentType.TUTORIAL_GUIDE),
            ("See the assignment brief below.", None, DocumentType.ASSIGNMENT_BRIEF),
            ("Bibliography of core texts.", None, DocumentType.READING_LIST),
            ("Course syllabus for semester one.", None, DocumentType.SYLLABUS),
            ("Some content.", "Study Guide for Finals", DocumentType.STUDY_GUIDE),
            ("Just some unrelated prose.", None, DocumentType.UNKNOWN),
        ],
    )
    def test_identifies_type_from_text_or_title(
        self,
        analyzer: DocumentAnalyzerService,
        text: str,
        title: str | None,
        expected: DocumentType,
    ) -> None:
        doc = _make_doc(text=text, title=title)
        assert analyzer._identify_document_type(doc) == expected

    def test_unit_outline_wins_over_later_checks(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        # Contains both "unit outline" and "assignment"; first match wins
        doc = _make_doc(text="Unit Outline including assignment details")
        assert analyzer._identify_document_type(doc) == DocumentType.UNIT_OUTLINE


# ─── Title extraction ─────────────────────────────────────────


class TestExtractTitle:
    def test_metadata_title_takes_precedence(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        doc = _make_doc(text="INTRODUCTION TO TESTING\nbody", title="Official Title")
        assert analyzer._extract_title(doc) == "Official Title"

    def test_uppercase_line_on_first_page_used_as_title(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = "x\nINTRODUCTION TO SOFTWARE TESTING\nsome body text follows here"
        doc = _make_doc(text=text)
        assert analyzer._extract_title(doc) == "INTRODUCTION TO SOFTWARE TESTING"

    def test_no_pages_returns_none(self, analyzer: DocumentAnalyzerService) -> None:
        assert analyzer._extract_title(_make_doc()) is None

    def test_short_or_lowercase_lines_ignored(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        doc = _make_doc(text="short\njust ordinary lowercase prose, not a title.")
        assert analyzer._extract_title(doc) is None


# ─── Heading detection & levels ───────────────────────────────


class TestHeadingDetection:
    @pytest.mark.parametrize(
        "line",
        [
            "1. Getting Started",
            "WEEK OVERVIEW",
            "Week 3 Topics",
            "Chapter 2 Advanced Material",
            "Introduction",
            "Assessment Details",
        ],
    )
    def test_recognizes_headings(
        self, analyzer: DocumentAnalyzerService, line: str
    ) -> None:
        assert analyzer._is_section_heading(line) is True

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "ab",
            "this is a normal sentence about content.",
        ],
    )
    def test_rejects_non_headings(
        self, analyzer: DocumentAnalyzerService, line: str
    ) -> None:
        assert analyzer._is_section_heading(line) is False

    @pytest.mark.parametrize(
        ("text", "level"),
        [
            ("Chapter 1 Basics", 1),
            ("Unit 2 Foundations", 1),
            ("Section 3 Details", 2),
            ("Module 4 Practice", 2),
            ("Week 5 Topics", 3),
            ("1.2.3 Deep subsection", 3),
            ("1.2 Subsection", 2),
            ("3. Numbered section", 1),
            ("Overview", 2),  # default
        ],
    )
    def test_heading_levels(
        self, analyzer: DocumentAnalyzerService, text: str, level: int
    ) -> None:
        assert analyzer._get_heading_level(text) == level

    def test_major_heading_detection(self, analyzer: DocumentAnalyzerService) -> None:
        assert analyzer._is_major_heading("Week 3 Functions") is True
        assert analyzer._is_major_heading("Learning Outcomes") is True
        assert analyzer._is_major_heading("References") is True
        assert analyzer._is_major_heading("just some body prose.") is False


# ─── Section extraction ───────────────────────────────────────


class TestSectionExtraction:
    def test_sections_by_pattern_without_toc(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = (
            "1. Introduction\n"
            "Welcome to the unit.\n"
            "It covers testing.\n"
            "2. Assessment\n"
            "There is one exam.\n"
        )
        doc = _make_doc(text=text)
        sections = analyzer._extract_sections(doc)

        assert [s.title for s in sections] == ["1. Introduction", "2. Assessment"]
        assert "Welcome to the unit." in sections[0].content
        assert sections[0].word_count == len(sections[0].content.split())
        assert sections[0].page_start == 1
        assert all(s.section_type == "heading" for s in sections)

    def test_sections_from_toc(self, analyzer: DocumentAnalyzerService) -> None:
        pages = [
            ExtractedPage(page_number=1, text="Introduction\nWelcome to the unit."),
            ExtractedPage(page_number=2, text="More body content here."),
        ]
        doc = _make_doc(
            text="Introduction\nWelcome to the unit.\nMore body content here.",
            pages=pages,
            toc=[{"title": "Introduction", "page": 1, "level": 1}],
        )
        sections = analyzer._extract_sections(doc)

        assert len(sections) == 1
        assert sections[0].title == "Introduction"
        assert sections[0].level == 1
        assert "Welcome to the unit." in sections[0].content

    def test_empty_document_yields_no_sections(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        assert analyzer._extract_sections(_make_doc()) == []


# ─── List item extraction ─────────────────────────────────────


class TestExtractListItems:
    def test_bullets_numbers_and_letters(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = "- bullet item\n• dot item\n1. numbered item\na) lettered item"
        items = analyzer._extract_list_items(text)
        assert items == ["bullet item", "dot item", "numbered item", "lettered item"]

    def test_plain_lines_kept_but_colon_headers_skipped(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = "Topics covered:\nplain content line\n\n"
        items = analyzer._extract_list_items(text)
        assert items == ["plain content line"]


# ─── Learning outcome parsing ─────────────────────────────────


class TestLearningOutcomes:
    def test_too_short_returns_none(self, analyzer: DocumentAnalyzerService) -> None:
        assert analyzer._parse_learning_outcome("short") is None

    def test_bloom_level_and_verbs_detected(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        outcome = analyzer._parse_learning_outcome(
            "Explain the principles of Software Testing"
        )
        assert outcome is not None
        assert outcome.bloom_level == BloomLevel.UNDERSTAND
        assert outcome.verbs is not None
        assert "explain" in outcome.verbs
        assert outcome.outcome_type == OutcomeType.ULO  # default

    def test_outcome_type_from_keywords(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        course = analyzer._parse_learning_outcome(
            "Summarize the main themes of the course material"
        )
        weekly = analyzer._parse_learning_outcome(
            "Each week, summarize the assigned reading material"
        )
        assert course is not None and course.outcome_type == OutcomeType.CLO
        assert weekly is not None and weekly.outcome_type == OutcomeType.WLO

    def test_topics_limited_to_capitalized_phrases(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        outcome = analyzer._parse_learning_outcome(
            "Demonstrate proficiency in Machine Learning and Data Science"
        )
        assert outcome is not None
        assert outcome.topics is not None
        assert "Machine Learning" in outcome.topics
        assert "Data Science" in outcome.topics
        assert len(outcome.topics) <= 5

    def test_extract_outcomes_from_document_section(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = (
            "Learning Outcomes:\n"
            "- Explain the fundamentals of unit testing\n"
            "- Demonstrate debugging strategies in Python\n"
            "\n"
            "Unrelated paragraph follows here.\n"
        )
        outcomes = analyzer._extract_learning_outcomes(_make_doc(text=text))
        texts = [o.text for o in outcomes]
        assert "Explain the fundamentals of unit testing" in texts
        assert "Demonstrate debugging strategies in Python" in texts


# ─── Assessment extraction ────────────────────────────────────


class TestAssessments:
    def test_parse_assessment_fields(self, analyzer: DocumentAnalyzerService) -> None:
        parsed = analyzer._parse_assessment(
            "Assignment 1 is due in Week 5 and is worth 30% of the grade"
        )
        assert parsed is not None
        assert parsed.name == "Assignment 1"
        assert parsed.weight == 30.0
        assert parsed.due_week == 5
        assert parsed.assessment_type == "assignment"
        assert parsed.description is not None

    @pytest.mark.parametrize(
        ("text", "expected_type"),
        [
            ("Quiz 1 covering early material", "quiz"),
            ("Final exam held in Week 13", "exam"),
            ("Group project on web design", "project"),
            ("Oral presentation in front of peers", "presentation"),
        ],
    )
    def test_assessment_type_detection(
        self, analyzer: DocumentAnalyzerService, text: str, expected_type: str
    ) -> None:
        parsed = analyzer._parse_assessment(text)
        assert parsed is not None
        assert parsed.assessment_type == expected_type

    def test_parse_empty_assessment_returns_none(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        assert analyzer._parse_assessment("") is None

    def test_extract_assessments_from_document(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = "Assessment: Assignment 1 due Week 5 worth 30%\n\nOther body text.\n"
        assessments = analyzer._extract_assessments(_make_doc(text=text))
        assert len(assessments) >= 1
        first = assessments[0]
        assert first.weight == 30.0
        assert first.due_week == 5


# ─── Weekly content extraction ────────────────────────────────


class TestWeeklyContent:
    def test_weeks_topics_readings_and_activities(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = (
            "Week 1: Introduction to Testing\n"
            "Readings: Chapter 1\n"
            "\n"
            "Week 2: Unit Testing\n"
            "Pre-class: Watch the intro video\n"
            "\n"
        )
        weekly = analyzer._extract_weekly_content(_make_doc(text=text))

        assert [w.week_number for w in weekly] == [1, 2]
        assert weekly[0].topic == "Introduction to Testing"
        assert weekly[0].readings == ["Chapter 1"]
        assert weekly[1].topic == "Unit Testing"
        assert weekly[1].pre_class == ["Watch the intro video"]

    def test_week_without_topic_gets_default_label(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        weekly = analyzer._extract_weekly_content(_make_doc(text="Week 3:\n\n"))
        assert len(weekly) == 1
        assert weekly[0].topic == "Week 3"

    def test_topic_regex_swallows_newline_after_colon(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        # Known quirk: `[:\s]*` in the week pattern consumes the newline,
        # so the next body line is captured as the topic.
        weekly = analyzer._extract_weekly_content(
            _make_doc(text="Week 3:\nsome plain body content here\n\n")
        )
        assert len(weekly) == 1
        assert weekly[0].topic == "some plain body content here"

    def test_no_weeks_in_document(self, analyzer: DocumentAnalyzerService) -> None:
        assert analyzer._extract_weekly_content(_make_doc(text="No schedule.")) == []


# ─── Concepts, prerequisites, references ──────────────────────


class TestSupplementaryExtraction:
    def test_key_concepts(self, analyzer: DocumentAnalyzerService) -> None:
        text = "Key Concepts:\n- Unit testing\n- Test coverage\n\nMore text.\n"
        concepts = analyzer._extract_key_concepts(_make_doc(text=text))
        assert set(concepts) == {"Unit testing", "Test coverage"}

    def test_prerequisites(self, analyzer: DocumentAnalyzerService) -> None:
        text = "Prerequisites:\n- Basic programming knowledge\n\nOther section.\n"
        prereqs = analyzer._extract_prerequisites(_make_doc(text=text))
        assert prereqs == ["Basic programming knowledge"]

    def test_references_author_year(self, analyzer: DocumentAnalyzerService) -> None:
        text = "References:\nSmith, J. (2020) Introduction to Testing. Press.\n\n"
        refs = analyzer._extract_references(_make_doc(text=text))
        assert refs
        assert any("Smith" in ref and "2020" in ref for ref in refs)


# ─── End-to-end analysis ──────────────────────────────────────


class TestAnalyzeDocument:
    @pytest.mark.asyncio
    async def test_analyze_full_synthetic_outline(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        text = (
            "UNIT OUTLINE FOR ISYS1001\n"
            "Learning Outcomes:\n"
            "- Explain the fundamentals of unit testing\n"
            "\n"
            "Assessment: Assignment 1 worth 30% of the final grade\n"
            "\n"
            "Week 1: Introduction to Testing\n"
            "Readings: Chapter 1\n"
            "\n"
        )
        analysis = await analyzer.analyze_document(_make_doc(text=text))

        assert analysis.document_type == DocumentType.UNIT_OUTLINE
        assert analysis.title == "UNIT OUTLINE FOR ISYS1001"
        assert analysis.learning_outcomes
        assert analysis.assessments
        assert analysis.assessments[0].weight == 30.0
        assert [w.week_number for w in analysis.weekly_content] == [1]
        assert analysis.metadata["page_count"] == 1
        assert analysis.metadata["has_toc"] is False
        assert analysis.metadata["extraction_method"] == "pypdf"
        assert analysis.metadata["word_count"] == len(text.split())

    @pytest.mark.asyncio
    async def test_analyze_empty_document(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        analysis = await analyzer.analyze_document(_make_doc())

        assert analysis.document_type == DocumentType.UNKNOWN
        assert analysis.title is None
        assert analysis.sections == []
        assert analysis.learning_outcomes == []
        assert analysis.assessments == []
        assert analysis.weekly_content == []
        assert analysis.metadata["word_count"] == 0


# ─── Mapping to course structure ──────────────────────────────


class TestMapToCourseStructure:
    @pytest.mark.asyncio
    async def test_maps_outcomes_weeks_and_assessments(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        analysis = _empty_analysis(
            document_type=DocumentType.UNIT_OUTLINE,
            title="Testing 101",
            learning_outcomes=[
                ExtractedLearningOutcome(
                    text="Explain unit testing",
                    outcome_type=OutcomeType.ULO,
                    bloom_level=BloomLevel.UNDERSTAND,
                )
            ],
            weekly_content=[
                ExtractedWeeklyContent(
                    week_number=1,
                    topic="Intro",
                    in_class=["Lab exercise"],
                    readings=["Chapter 1"],
                ),
                ExtractedWeeklyContent(week_number=2, topic="Advanced"),
            ],
            assessments=[
                ExtractedAssessment(
                    name="Assignment 1",
                    assessment_type="assignment",
                    weight=30.0,
                    due_week=5,
                )
            ],
        )
        mapping = await analyzer.map_to_course_structure(analysis)

        assert mapping["course_outline"]["title"] == "Testing 101"
        assert mapping["course_outline"]["duration_weeks"] == 2

        assert mapping["learning_outcomes"] == [
            {
                "outcome_type": OutcomeType.ULO,
                "outcome_text": "Explain unit testing",
                "bloom_level": BloomLevel.UNDERSTAND.value,
            }
        ]

        week1 = mapping["weekly_topics"][0]
        assert week1["week_number"] == 1
        assert week1["in_class_activities"][0]["description"] == "Lab exercise"
        assert week1["required_readings"] == [
            {"title": "Chapter 1", "type": "required"}
        ]

        assert mapping["assessments"][0]["weight_percentage"] == 30.0
        assert mapping["assessments"][0]["due_week"] == 5

        # Suggestions: syllabus (unit outline) + slides per week +
        # worksheet (in-class week) + assignment per assessment
        reasons = [s["reason"] for s in mapping["content_suggestions"]]
        assert "Unit outline detected - syllabus needed" in reasons
        assert "In-class activities detected" in reasons
        assert "Assessment: assignment" in reasons
        titles = [s["title"] for s in mapping["content_suggestions"]]
        assert "Week 1: Intro" in titles
        assert "Week 2: Advanced" in titles

    @pytest.mark.asyncio
    async def test_duration_defaults_to_twelve_weeks(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        mapping = await analyzer.map_to_course_structure(_empty_analysis())
        assert mapping["course_outline"]["duration_weeks"] == 12

    def test_generate_description_with_and_without_content(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        empty = analyzer._generate_description(_empty_analysis())
        assert empty == "Course content extracted from document"

        rich = analyzer._generate_description(
            _empty_analysis(
                title="Testing 101",
                learning_outcomes=[
                    ExtractedLearningOutcome(
                        text="Explain testing", outcome_type=OutcomeType.ULO
                    )
                ],
                key_concepts=["Unit testing"],
            )
        )
        assert "Course: Testing 101" in rich
        assert "1 learning outcomes" in rich
        assert "Unit testing" in rich

    def test_format_activities_truncates_title(
        self, analyzer: DocumentAnalyzerService
    ) -> None:
        long_activity = "x" * 150
        formatted = analyzer._format_activities([long_activity])
        assert formatted[0]["title"] == "x" * 100
        assert formatted[0]["description"] == long_activity
        assert formatted[0]["duration_minutes"] == 30
        assert analyzer._format_activities(None) == []
        assert analyzer._format_readings(None) == []


# ─── Dataclass sanity ─────────────────────────────────────────


def test_analyzed_section_defaults() -> None:
    section = AnalyzedSection(
        title="Intro",
        content="body",
        section_type="heading",
        level=1,
        page_start=1,
        page_end=1,
        word_count=1,
    )
    assert section.metadata is None
