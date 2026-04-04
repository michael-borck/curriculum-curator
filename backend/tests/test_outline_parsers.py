"""
Tests for the outline parser system (ADR-063).

Covers:
- Parser registry (list_parsers, get_parser)
- Curtin parser (regex extraction, fallback to generic)
- Generic parser (mocked LLM)
- Apply endpoint (creates unit + ULOs + weeks + assessments)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.user import User

from app.models.assessment import Assessment
from app.models.learning_outcome import UnitLearningOutcome
from app.models.unit import Unit
from app.models.weekly_topic import WeeklyTopic
from app.services.outline_parsers import get_parser, list_parsers
from app.services.outline_parsers.base import (
    ExtractedAssessment,
    ExtractedSnippet,
    ExtractedTextbook,
    ExtractedULO,
    ExtractedWeek,
    OutlineParseResult,
)
from app.services.outline_parsers.curtin_parser import (
    CurtinOutlineParser,
    _guess_bloom,
)


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestParserRegistry:
    def test_list_parsers_returns_both(self) -> None:
        parsers = list_parsers()
        ids = {p["id"] for p in parsers}
        assert "generic" in ids
        assert "curtin" in ids

    def test_list_parsers_has_required_keys(self) -> None:
        for p in list_parsers():
            assert "id" in p
            assert "displayName" in p
            assert "description" in p
            assert "supportedFormats" in p

    def test_get_parser_generic(self) -> None:
        parser = get_parser("generic")
        assert parser.name == "generic"

    def test_get_parser_curtin(self) -> None:
        parser = get_parser("curtin")
        assert parser.name == "curtin"

    def test_get_parser_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown parser"):
            get_parser("nonexistent")


# ---------------------------------------------------------------------------
# Bloom guessing
# ---------------------------------------------------------------------------


class TestBloomGuessing:
    def test_remember(self) -> None:
        assert _guess_bloom("List the key features of object-oriented programming") == "remember"

    def test_understand(self) -> None:
        assert _guess_bloom("Describe the principles of software testing") == "understand"

    def test_apply(self) -> None:
        assert _guess_bloom("Apply sorting algorithms to datasets") == "apply"

    def test_analyse(self) -> None:
        assert _guess_bloom("Analyse the performance of different approaches") == "analyse"

    def test_evaluate(self) -> None:
        assert _guess_bloom("Evaluate the suitability of cloud platforms") == "evaluate"

    def test_create(self) -> None:
        assert _guess_bloom("Design a RESTful API for the application") == "create"

    def test_fallback(self) -> None:
        assert _guess_bloom("Foobar something unusual") == "understand"


# ---------------------------------------------------------------------------
# Curtin parser — regex extraction
# ---------------------------------------------------------------------------

_CURTIN_DOC = """\
Curtin University
Unit Outline
curtin.edu.au

COMP1001 (V.1) Introduction to Programming
Credit Points: 25
Semester 1, 2026

Syllabus
This unit introduces students to the fundamentals of programming using Python.

Unit Learning Outcomes
On successful completion of this unit student can:
Graduate Capabilities addressed
1
Describe the basic concepts of programming
2
Apply programming techniques to solve simple problems
3
Design and implement small programs

Assessment Summary
1
Quiz 1
20 %
Week:4
2
Final Exam
50 %
Week:14
3
Project
30 %
Week:12

Teaching Schedule
Week 1: Introduction to Python
Week 2: Variables and Data Types
Week 3: Control Structures

Learning Resources
Matthes, E. (2019). Python Crash Course. No Starch Press.
Essential:Yes
ISBN: 978-1-59327-928-8

Academic Integrity
Students must follow Curtin's Academic Integrity policy.
"""


class TestCurtinParser:
    @pytest.mark.asyncio
    async def test_parses_curtin_doc(self) -> None:
        parser = CurtinOutlineParser()
        result = await parser.parse(
            file_content=_CURTIN_DOC.encode(),
            filename="outline.txt",
            file_type="txt",
        )
        assert result.parser_used == "curtin"
        assert result.unit_code == "COMP1001"
        assert result.credit_points == 25
        assert result.year == 2026
        assert result.semester == "semester_1"
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_extracts_ulos(self) -> None:
        parser = CurtinOutlineParser()
        result = await parser.parse(
            file_content=_CURTIN_DOC.encode(),
            filename="outline.txt",
            file_type="txt",
        )
        assert len(result.learning_outcomes) >= 2
        codes = [u.code for u in result.learning_outcomes]
        assert "ULO1" in codes

    @pytest.mark.asyncio
    async def test_extracts_assessments(self) -> None:
        parser = CurtinOutlineParser()
        result = await parser.parse(
            file_content=_CURTIN_DOC.encode(),
            filename="outline.txt",
            file_type="txt",
        )
        assert len(result.assessments) >= 2
        weights = [a.weight for a in result.assessments]
        assert 50.0 in weights

    @pytest.mark.asyncio
    async def test_extracts_weeks(self) -> None:
        parser = CurtinOutlineParser()
        result = await parser.parse(
            file_content=_CURTIN_DOC.encode(),
            filename="outline.txt",
            file_type="txt",
        )
        assert len(result.weekly_schedule) >= 2
        topics = [w.topic for w in result.weekly_schedule]
        assert any("Python" in t for t in topics)

    @pytest.mark.asyncio
    async def test_extracts_textbooks(self) -> None:
        parser = CurtinOutlineParser()
        result = await parser.parse(
            file_content=_CURTIN_DOC.encode(),
            filename="outline.txt",
            file_type="txt",
        )
        assert len(result.textbooks) >= 1
        assert any("Python" in t.title for t in result.textbooks)

    @pytest.mark.asyncio
    async def test_extracts_supplementary(self) -> None:
        parser = CurtinOutlineParser()
        result = await parser.parse(
            file_content=_CURTIN_DOC.encode(),
            filename="outline.txt",
            file_type="txt",
        )
        headings = [s.heading for s in result.supplementary_info]
        assert "Academic Integrity" in headings

    @pytest.mark.asyncio
    async def test_empty_doc_returns_zero_confidence(self) -> None:
        parser = CurtinOutlineParser()
        result = await parser.parse(
            file_content=b"   ",
            filename="empty.txt",
            file_type="txt",
        )
        assert result.confidence == 0.0
        assert any("empty" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_non_curtin_falls_back_to_generic(self) -> None:
        """Non-Curtin doc should trigger fallback — we mock the generic parser."""
        non_curtin = b"University of Example\nSome random outline content here."

        mock_result = OutlineParseResult(
            unit_code="EX101",
            confidence=0.7,
            parser_used="generic",
        )

        with patch(
            "app.services.outline_parsers.generic_parser.GenericOutlineParser.parse",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            parser = CurtinOutlineParser()
            result = await parser.parse(
                file_content=non_curtin,
                filename="other.txt",
                file_type="txt",
            )
            assert result.parser_used == "generic"
            assert any("generic" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Generic parser — LLM mocked
# ---------------------------------------------------------------------------


class TestGenericParser:
    @pytest.mark.asyncio
    async def test_empty_doc(self) -> None:
        from app.services.outline_parsers.generic_parser import GenericOutlineParser

        parser = GenericOutlineParser()
        result = await parser.parse(
            file_content=b"",
            filename="empty.txt",
            file_type="txt",
        )
        assert result.confidence == 0.0
        assert any("empty" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_successful_parse_with_mocked_llm(self) -> None:
        from app.services.outline_parsers.generic_parser import (
            GenericOutlineParser,
            _LLMOutlineExtraction,
        )

        mock_extraction = _LLMOutlineExtraction(
            unit_code="TEST101",
            unit_title="Test Unit",
            description="A test description",
            credit_points=6,
            duration_weeks=12,
            confidence=0.85,
        )

        with patch(
            "app.services.llm_service.LLMService"
        ) as MockLLMService:
            instance = MockLLMService.return_value
            instance.generate_structured_content = AsyncMock(
                return_value=(mock_extraction, None)
            )

            parser = GenericOutlineParser()
            result = await parser.parse(
                file_content=b"Some unit outline text here with details",
                filename="outline.txt",
                file_type="txt",
            )
            assert result.unit_code == "TEST101"
            assert result.unit_title == "Test Unit"
            assert result.confidence == 0.85
            assert result.parser_used == "generic"

    @pytest.mark.asyncio
    async def test_llm_error_returns_zero_confidence(self) -> None:
        from app.services.outline_parsers.generic_parser import GenericOutlineParser

        with patch(
            "app.services.llm_service.LLMService"
        ) as MockLLMService:
            instance = MockLLMService.return_value
            instance.generate_structured_content = AsyncMock(
                return_value=(None, "LLM service unavailable")
            )

            parser = GenericOutlineParser()
            result = await parser.parse(
                file_content=b"Some text content",
                filename="outline.txt",
                file_type="txt",
            )
            assert result.confidence == 0.0
            assert any("unavailable" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_truncation_warning(self) -> None:
        from app.services.outline_parsers.generic_parser import (
            GenericOutlineParser,
            _LLMOutlineExtraction,
        )

        mock_extraction = _LLMOutlineExtraction(unit_code="BIG101", confidence=0.5)

        with patch(
            "app.services.llm_service.LLMService"
        ) as MockLLMService:
            instance = MockLLMService.return_value
            instance.generate_structured_content = AsyncMock(
                return_value=(mock_extraction, None)
            )

            parser = GenericOutlineParser()
            # 70k chars exceeds the 60k limit
            result = await parser.parse(
                file_content=("x" * 70_000).encode(),
                filename="huge.txt",
                file_type="txt",
            )
            assert any("truncated" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Apply endpoint (integration test via TestClient)
# ---------------------------------------------------------------------------


class TestApplyEndpoint:
    def test_apply_creates_unit(self, client, test_db: Session, test_user: User) -> None:  # type: ignore[no-untyped-def]
        payload = {
            "unitCode": "NEW101",
            "unitTitle": "Imported Unit",
            "description": "Imported from outline",
            "creditPoints": 25,
            "durationWeeks": 13,
            "year": 2026,
            "semester": "semester_1",
            "pedagogyType": "direct_instruction",
            "learningOutcomes": [
                {"code": "ULO1", "description": "Describe basics", "bloomLevel": "understand"},
                {"code": "ULO2", "description": "Apply techniques", "bloomLevel": "apply"},
            ],
            "weeklySchedule": [
                {"weekNumber": 1, "topic": "Introduction"},
                {"weekNumber": 2, "topic": "Fundamentals"},
            ],
            "assessments": [
                {"title": "Quiz 1", "category": "quiz", "weight": 30.0, "dueWeek": 4},
                {"title": "Final Exam", "category": "exam", "weight": 70.0},
            ],
            "textbooks": [
                {"title": "Test Book", "authors": "Author A", "isbn": "123", "required": True},
            ],
            "supplementaryInfo": [
                {"heading": "Policy", "content": "Some policy text", "keep": True},
                {"heading": "Dropped", "content": "Not needed", "keep": False},
            ],
            "parserUsed": "curtin",
        }

        resp = client.post("/api/import/outline/apply", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["code"] == "NEW101"
        assert data["ulosCreated"] == 2
        assert data["weeksCreated"] == 2
        assert data["assessmentsCreated"] == 2

        # Verify DB records
        unit = test_db.query(Unit).filter(Unit.code == "NEW101").first()
        assert unit is not None
        assert unit.credit_points == 25

        ulos = test_db.query(UnitLearningOutcome).filter(
            UnitLearningOutcome.unit_id == unit.id
        ).all()
        assert len(ulos) == 2

        weeks = test_db.query(WeeklyTopic).filter(
            WeeklyTopic.unit_id == unit.id
        ).all()
        assert len(weeks) == 2

        assessments = test_db.query(Assessment).filter(
            Assessment.unit_id == unit.id
        ).all()
        assert len(assessments) == 2

        # Textbooks stored in metadata
        assert unit.unit_metadata is not None
        assert "textbooks" in unit.unit_metadata
        assert len(unit.unit_metadata["textbooks"]) == 1

        # Supplementary: only kept items
        assert "supplementary_info" in unit.unit_metadata
        assert len(unit.unit_metadata["supplementary_info"]) == 1
        assert unit.unit_metadata["supplementary_info"][0]["heading"] == "Policy"

    def test_apply_duplicate_rejected(self, client, test_db: Session, test_user: User) -> None:  # type: ignore[no-untyped-def]
        payload = {
            "unitCode": "DUP101",
            "unitTitle": "First Unit",
            "creditPoints": 6,
            "durationWeeks": 12,
            "year": 2026,
            "semester": "semester_1",
            "parserUsed": "generic",
        }

        resp1 = client.post("/api/import/outline/apply", json=payload)
        assert resp1.status_code == 200

        resp2 = client.post("/api/import/outline/apply", json=payload)
        assert resp2.status_code == 409

    def test_apply_missing_required_fields(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post("/api/import/outline/apply", json={"unitCode": "", "unitTitle": ""})
        assert resp.status_code == 422

    def test_list_parsers_endpoint(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.get("/api/import/outline/parsers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        ids = {p["id"] for p in data}
        assert "generic" in ids
        assert "curtin" in ids

    def test_parse_no_file(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post("/api/import/outline/parse")
        assert resp.status_code == 422

    def test_parse_unsupported_extension(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post(
            "/api/import/outline/parse",
            files={"file": ("outline.exe", b"content", "application/octet-stream")},
            data={"parser_id": "generic"},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    def test_parse_empty_file(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post(
            "/api/import/outline/parse",
            files={"file": ("outline.txt", b"", "text/plain")},
            data={"parser_id": "generic"},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_parse_unknown_parser(self, client) -> None:  # type: ignore[no-untyped-def]
        resp = client.post(
            "/api/import/outline/parse",
            files={"file": ("outline.txt", b"content", "text/plain")},
            data={"parser_id": "nonexistent"},
        )
        assert resp.status_code == 400
        assert "Unknown parser" in resp.json()["detail"]
