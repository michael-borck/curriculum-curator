"""
Tests for outline synthesis service (propose/apply).

Mocks llm_service.generate_structured_content() (external boundary). Tests:
- Scaffold includes source summaries in prompt
- Scaffold returns valid ScaffoldUnitResponse
- Compare fetches existing unit and identifies gaps
- Reading list returns matches with confidence scores
- Apply endpoints create correct DB records (uses test_db + test_unit fixtures)
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.research_source import ResearchSource
from app.models.unit import Unit
from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic
from app.schemas.ai import (
    ScaffoldAssessment,
    ScaffoldULO,
    ScaffoldUnitResponse,
    ScaffoldWeek,
)
from app.schemas.research import (
    ComparisonProposal,
    ComparisonWeek,
    ReadingListProposal,
    ResourceMatch,
    SourceInput,
    UnitWeekInfo,
)
from app.services.outline_synthesis_service import OutlineSynthesisService


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

SAMPLE_SOURCES = [
    SourceInput(
        title="Intro to ML",
        url="https://example.com/ml",
        summary="Covers supervised and unsupervised learning basics",
        key_points=["Classification", "Regression", "Clustering"],
    ),
    SourceInput(
        title="Deep Learning Overview",
        url="https://example.com/dl",
        summary="Neural network architectures and training",
        key_points=["CNNs", "RNNs", "Transformers"],
    ),
]

SAMPLE_SCAFFOLD = ScaffoldUnitResponse(
    title="Machine Learning Fundamentals",
    description="An introduction to ML concepts",
    ulos=[
        ScaffoldULO(
            code="ULO1",
            description="Explain supervised learning",
            bloom_level="UNDERSTAND",
        ),
        ScaffoldULO(
            code="ULO2",
            description="Implement classification algorithms",
            bloom_level="APPLY",
        ),
    ],
    weeks=[
        ScaffoldWeek(
            week_number=1, topic="Introduction to ML", activities=["Lecture", "Lab"]
        ),
        ScaffoldWeek(
            week_number=2, topic="Supervised Learning", activities=["Workshop"]
        ),
    ],
    assessments=[
        ScaffoldAssessment(title="Quiz 1", category="quiz", weight=20.0, due_week=4),
        ScaffoldAssessment(
            title="Final Project", category="project", weight=40.0, due_week=12
        ),
    ],
)


# ──────────────────────────────────────────────────────────────
# Propose scaffold
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_propose_scaffold(test_db: Session, test_user):
    service = OutlineSynthesisService()

    with patch(
        "app.services.outline_synthesis_service.llm_service.generate_structured_content",
        new_callable=AsyncMock,
        return_value=(SAMPLE_SCAFFOLD, None),
    ) as mock_llm:
        result = await service.propose_scaffold(
            sources=SAMPLE_SOURCES,
            unit_title="ML Fundamentals",
            unit_description="Intro to ML",
            duration_weeks=12,
            pedagogy_style="inquiry-based",
            unit_id=None,
            design_id=None,
            db=test_db,
        )

    assert result is not None
    assert result.title == "Machine Learning Fundamentals"
    assert len(result.ulos) == 2
    assert len(result.weeks) == 2
    assert len(result.assessments) == 2

    # Verify prompt includes source information
    call_args = mock_llm.call_args
    prompt = call_args.kwargs.get("prompt") or call_args.args[0]
    assert "Intro to ML" in prompt
    assert "Deep Learning Overview" in prompt
    assert "Classification" in prompt


@pytest.mark.asyncio
async def test_propose_scaffold_llm_failure(test_db: Session, test_user):
    service = OutlineSynthesisService()

    with patch(
        "app.services.outline_synthesis_service.llm_service.generate_structured_content",
        new_callable=AsyncMock,
        return_value=(None, "LLM service unavailable"),
    ):
        result = await service.propose_scaffold(
            sources=SAMPLE_SOURCES,
            unit_title="Test",
            unit_description="",
            duration_weeks=12,
            pedagogy_style="mixed_approach",
            unit_id=None,
            design_id=None,
            db=test_db,
        )

    assert result is None


# ──────────────────────────────────────────────────────────────
# Propose comparison
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_propose_comparison(test_db: Session, test_unit: Unit, test_user):
    """Compare requires existing unit with weekly topics."""
    from app.models.unit_outline import UnitOutline

    # Add an outline and topics
    outline = UnitOutline(
        id=str(uuid.uuid4()),
        unit_id=str(test_unit.id),
        title=test_unit.title,
        description="",
        duration_weeks=12,
        credit_points=6,
        status="planning",
        created_by_id=str(test_user.id),
    )
    test_db.add(outline)
    test_db.commit()

    topic = WeeklyTopic(
        id=str(uuid.uuid4()),
        unit_outline_id=str(outline.id),
        unit_id=str(test_unit.id),
        week_number=1,
        topic_title="HTML Basics",
        created_by_id=str(test_user.id),
    )
    test_db.add(topic)
    test_db.commit()

    mock_comparison = ComparisonProposal(
        unit_id=str(test_unit.id),
        weeks=[
            ComparisonWeek(
                week_number=1,
                topic="HTML Basics",
                coverage="partially_covered",
                matching_sources=["Intro to ML"],
            )
        ],
        gaps=["Deep learning not covered"],
        overlaps=[],
        suggestions=["Add a week on neural networks"],
    )

    service = OutlineSynthesisService()

    with patch(
        "app.services.outline_synthesis_service.llm_service.generate_structured_content",
        new_callable=AsyncMock,
        return_value=(mock_comparison, None),
    ) as mock_llm:
        result = await service.propose_comparison(
            sources=SAMPLE_SOURCES,
            unit_id=str(test_unit.id),
            db=test_db,
        )

    assert result is not None
    assert result.unit_id == str(test_unit.id)
    assert len(result.gaps) == 1

    # Verify prompt includes unit topics
    prompt = mock_llm.call_args.kwargs.get("prompt") or mock_llm.call_args.args[0]
    assert "HTML Basics" in prompt


@pytest.mark.asyncio
async def test_propose_comparison_unit_not_found(test_db: Session, test_user):
    service = OutlineSynthesisService()

    result = await service.propose_comparison(
        sources=SAMPLE_SOURCES,
        unit_id=str(uuid.uuid4()),  # Valid UUID that doesn't exist in DB
        db=test_db,
    )

    assert result is None


# ──────────────────────────────────────────────────────────────
# Propose reading list
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_propose_reading_list(test_db: Session, test_unit: Unit, test_user):
    from app.models.unit_outline import UnitOutline

    outline = UnitOutline(
        id=str(uuid.uuid4()),
        unit_id=str(test_unit.id),
        title=test_unit.title,
        description="",
        duration_weeks=12,
        credit_points=6,
        status="planning",
        created_by_id=str(test_user.id),
    )
    test_db.add(outline)
    test_db.commit()

    for wk in range(1, 4):
        test_db.add(
            WeeklyTopic(
                id=str(uuid.uuid4()),
                unit_outline_id=str(outline.id),
                unit_id=str(test_unit.id),
                week_number=wk,
                topic_title=f"Topic {wk}",
                created_by_id=str(test_user.id),
            )
        )
        test_db.commit()

    mock_reading_list = ReadingListProposal(
        unit_id=str(test_unit.id),
        matches=[
            ResourceMatch(
                url="https://example.com/ml",
                title="Intro to ML",
                suggested_week=1,
                confidence=0.9,
                reasoning="Covers foundational concepts taught in week 1",
            ),
            ResourceMatch(
                url="https://example.com/dl",
                title="Deep Learning Overview",
                suggested_week=2,
                confidence=0.7,
                reasoning="Advanced content for week 2",
            ),
        ],
    )

    service = OutlineSynthesisService()

    with patch(
        "app.services.outline_synthesis_service.llm_service.generate_structured_content",
        new_callable=AsyncMock,
        return_value=(mock_reading_list, None),
    ):
        result = await service.propose_reading_list(
            sources=SAMPLE_SOURCES,
            unit_id=str(test_unit.id),
            db=test_db,
        )

    assert result is not None
    assert result.unit_id == str(test_unit.id)
    assert len(result.unit_weeks) == 3  # 3 topics added
    assert len(result.matches) == 2
    assert result.avg_confidence == pytest.approx(0.8)
    assert result.unmatched_count == 0


# ──────────────────────────────────────────────────────────────
# Apply scaffold (HTTP endpoint)
# ──────────────────────────────────────────────────────────────


def test_apply_scaffold_creates_unit(client, test_db: Session):
    """POST /api/research/scaffold/apply creates unit + ULOs + topics."""
    payload = {
        "proposal": {
            "title": "New ML Unit",
            "description": "A unit about machine learning",
            "ulos": [
                {
                    "code": "ULO1",
                    "description": "Explain ML",
                    "bloomLevel": "UNDERSTAND",
                }
            ],
            "weeks": [
                {"weekNumber": 1, "topic": "Intro", "activities": ["Lecture"]},
                {"weekNumber": 2, "topic": "Regression", "activities": ["Lab"]},
            ],
            "assessments": [
                {"title": "Quiz", "category": "quiz", "weight": 20.0, "dueWeek": 4}
            ],
        }
    }

    response = client.post("/api/research/scaffold/apply", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["created"] is True
    assert "unitId" in data or "unit_id" in data

    unit_id = data.get("unitId") or data.get("unit_id")

    # Verify DB records
    unit = test_db.query(Unit).filter(Unit.id == unit_id).first()
    assert unit is not None
    assert unit.title == "New ML Unit"

    topics = test_db.query(WeeklyTopic).filter(WeeklyTopic.unit_id == unit_id).all()
    assert len(topics) == 2


# ──────────────────────────────────────────────────────────────
# Apply reading list (HTTP endpoint)
# ──────────────────────────────────────────────────────────────


def test_apply_reading_list_creates_sources(client, test_db: Session, test_unit: Unit):
    """POST /api/research/match-reading-list/apply creates ResearchSource + WeeklyMaterial."""
    payload = {
        "proposal": {
            "unitId": str(test_unit.id),
            "unitWeeks": [{"weekNumber": 1, "topic": "Intro"}],
            "matches": [
                {
                    "url": "https://example.com/paper",
                    "title": "Good Paper",
                    "suggestedWeek": 1,
                    "confidence": 0.85,
                    "reasoning": "Relevant to week 1",
                    "skipped": False,
                }
            ],
            "unmatchedCount": 0,
            "avgConfidence": 0.85,
        },
        "saveAsSources": True,
    }

    response = client.post("/api/research/match-reading-list/apply", json=payload)
    assert response.status_code == 200

    # Verify ResearchSource was created
    sources = (
        test_db.query(ResearchSource)
        .filter(ResearchSource.unit_id == str(test_unit.id))
        .all()
    )
    assert len(sources) == 1
    assert sources[0].url == "https://example.com/paper"

    # Verify WeeklyMaterial was created
    materials = (
        test_db.query(WeeklyMaterial)
        .filter(
            WeeklyMaterial.unit_id == str(test_unit.id),
            WeeklyMaterial.week_number == 1,
        )
        .all()
    )
    assert any(m.title == "Good Paper" for m in materials)


def test_apply_reading_list_skips_flagged(client, test_db: Session, test_unit: Unit):
    """Skipped matches should not create DB records."""
    payload = {
        "proposal": {
            "unitId": str(test_unit.id),
            "unitWeeks": [],
            "matches": [
                {
                    "url": "https://example.com/skip",
                    "title": "Skipped Paper",
                    "suggestedWeek": 1,
                    "confidence": 0.3,
                    "reasoning": "Low relevance",
                    "skipped": True,
                }
            ],
            "unmatchedCount": 1,
            "avgConfidence": 0.3,
        },
        "saveAsSources": True,
    }

    response = client.post("/api/research/match-reading-list/apply", json=payload)
    assert response.status_code == 200

    sources = (
        test_db.query(ResearchSource)
        .filter(ResearchSource.url == "https://example.com/skip")
        .all()
    )
    assert len(sources) == 0
