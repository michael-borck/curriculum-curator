"""
Unit tests for Assessments service.

Tests mock the DB session and validate CRUD operations, grade distribution,
weight validation, timeline, workload analysis, and mapping operations.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

import pytest

# Set test environment before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy.exc import IntegrityError

from app.models.assessment import Assessment, AssessmentType
from app.models.learning_outcome import AssessmentLearningOutcome
from app.schemas.assessments import (
    AssessmentCreate,
    AssessmentMapping,
    AssessmentMaterialLink,
    AssessmentUpdate,
    Rubric,
    RubricCriterion,
)
from app.schemas.learning_outcomes import ALOCreate
from app.services.assessments_service import AssessmentsService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UNIT_ID = str(uuid4())


def make_mock_assessment(
    *,
    title: str = "Quiz 1",
    assessment_type: str = AssessmentType.FORMATIVE.value,
    category: str = "quiz",
    weight: float = 20.0,
    due_week: int | None = 4,
    due_date: object | None = None,
    assessment_id: str | None = None,
) -> Mock:
    """Create a mock Assessment model instance."""
    a = Mock(spec=Assessment)
    a.id = assessment_id or str(uuid4())
    a.unit_id = UNIT_ID
    a.title = title
    a.type = assessment_type
    a.category = category
    a.weight = weight
    a.due_week = due_week
    a.due_date = due_date
    a.description = f"Description for {title}"
    a.release_week = (due_week - 2) if due_week and due_week > 2 else 1
    a.status = "draft"
    return a


def make_assessment_create(
    *,
    title: str = "Quiz 1",
    assessment_type: str = AssessmentType.FORMATIVE.value,
    category: str = "quiz",
    weight: float = 20.0,
    due_week: int | None = 4,
    rubric: Rubric | None = None,
) -> AssessmentCreate:
    return AssessmentCreate(
        title=title,
        type=assessment_type,
        category=category,
        weight=weight,
        due_week=due_week,
        rubric=rubric,
    )


def make_three_assessments() -> list[Mock]:
    """Return 3 mock assessments totalling 100%."""
    return [
        make_mock_assessment(
            title="Quiz 1",
            assessment_type=AssessmentType.FORMATIVE.value,
            category="quiz",
            weight=20.0,
            due_week=4,
        ),
        make_mock_assessment(
            title="Project",
            assessment_type=AssessmentType.SUMMATIVE.value,
            category="project",
            weight=40.0,
            due_week=8,
        ),
        make_mock_assessment(
            title="Final Exam",
            assessment_type=AssessmentType.SUMMATIVE.value,
            category="exam",
            weight=40.0,
            due_week=12,
        ),
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def service() -> AssessmentsService:
    return AssessmentsService()


@pytest.fixture()
def mock_db() -> Mock:
    """A mock SQLAlchemy Session with chainable query."""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.delete = Mock()
    db.execute = Mock()
    return db


def _setup_query_returns(db: Mock, result: object) -> None:
    """Configure db.query(...).filter(...).first() to return `result`."""
    query_chain = Mock()
    query_chain.filter.return_value = query_chain
    query_chain.options.return_value = query_chain
    query_chain.first.return_value = result
    query_chain.order_by.return_value = query_chain
    query_chain.all.return_value = result if isinstance(result, list) else [result]
    db.query.return_value = query_chain


def _setup_query_returns_scalar(db: Mock, scalar_value: object) -> None:
    """Configure db.query(...).filter(...).scalar() to return a value."""
    query_chain = Mock()
    query_chain.filter.return_value = query_chain
    query_chain.scalar.return_value = scalar_value
    db.query.return_value = query_chain


# ---------------------------------------------------------------------------
# TestCreateAssessment
# ---------------------------------------------------------------------------


class TestCreateAssessment:
    @pytest.mark.asyncio
    async def test_create_success(self, service: AssessmentsService, mock_db: Mock) -> None:
        data = make_assessment_create()

        def fake_refresh(obj: object) -> None:
            obj.title = data.title  # type: ignore[union-attr]

        mock_db.refresh.side_effect = fake_refresh

        result = await service.create_assessment(mock_db, uuid4(), data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert isinstance(result, Assessment)

    @pytest.mark.asyncio
    async def test_create_with_rubric(self, service: AssessmentsService, mock_db: Mock) -> None:
        rubric = Rubric(
            criteria=[
                RubricCriterion(
                    name="Quality",
                    description="Work quality",
                    points=10.0,
                    levels=["Fail", "Pass", "Credit", "Distinction"],
                )
            ],
            total_points=10.0,
        )
        data = make_assessment_create(rubric=rubric)

        await service.create_assessment(mock_db, uuid4(), data)

        # The Assessment constructor was called with rubric as a dict
        add_call_args = mock_db.add.call_args
        created_obj = add_call_args[0][0]
        assert isinstance(created_obj, Assessment)

    @pytest.mark.asyncio
    async def test_create_integrity_error(self, service: AssessmentsService, mock_db: Mock) -> None:
        mock_db.commit.side_effect = IntegrityError("dup", {}, None)
        data = make_assessment_create()

        with pytest.raises(ValueError, match="Failed to create assessment"):
            await service.create_assessment(mock_db, uuid4(), data)

        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# TestUpdateAssessment
# ---------------------------------------------------------------------------


class TestUpdateAssessment:
    @pytest.mark.asyncio
    async def test_update_success(self, service: AssessmentsService, mock_db: Mock) -> None:
        existing = make_mock_assessment()
        _setup_query_returns(mock_db, existing)

        update_data = AssessmentUpdate(title="Updated Quiz", weight=25.0)
        result = await service.update_assessment(mock_db, uuid4(), update_data)

        assert result is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, service: AssessmentsService, mock_db: Mock) -> None:
        _setup_query_returns(mock_db, None)

        update_data = AssessmentUpdate(title="Updated Quiz")
        result = await service.update_assessment(mock_db, uuid4(), update_data)

        assert result is None
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_integrity_error(self, service: AssessmentsService, mock_db: Mock) -> None:
        existing = make_mock_assessment()
        _setup_query_returns(mock_db, existing)
        mock_db.commit.side_effect = IntegrityError("dup", {}, None)

        update_data = AssessmentUpdate(title="Bad Update")

        with pytest.raises(ValueError, match="Update would violate constraints"):
            await service.update_assessment(mock_db, uuid4(), update_data)

        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# TestDeleteAssessment
# ---------------------------------------------------------------------------


class TestDeleteAssessment:
    @pytest.mark.asyncio
    async def test_delete_success(self, service: AssessmentsService, mock_db: Mock) -> None:
        existing = make_mock_assessment()
        _setup_query_returns(mock_db, existing)

        result = await service.delete_assessment(mock_db, uuid4())

        assert result is True
        mock_db.delete.assert_called_once_with(existing)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, service: AssessmentsService, mock_db: Mock) -> None:
        _setup_query_returns(mock_db, None)

        result = await service.delete_assessment(mock_db, uuid4())

        assert result is False
        mock_db.delete.assert_not_called()


# ---------------------------------------------------------------------------
# TestGetAssessments
# ---------------------------------------------------------------------------


class TestGetAssessments:
    @pytest.mark.asyncio
    async def test_get_assessment_by_id(self, service: AssessmentsService, mock_db: Mock) -> None:
        expected = make_mock_assessment()
        _setup_query_returns(mock_db, expected)

        result = await service.get_assessment(mock_db, uuid4())

        assert result is expected

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(self, service: AssessmentsService, mock_db: Mock) -> None:
        _setup_query_returns(mock_db, None)

        result = await service.get_assessment(mock_db, uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_assessments_by_unit(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = make_three_assessments()
        _setup_query_returns(mock_db, assessments)

        result = await service.get_assessments_by_unit(mock_db, uuid4())

        assert len(result) == 3


# ---------------------------------------------------------------------------
# TestGradeDistribution
# ---------------------------------------------------------------------------


class TestGradeDistribution:
    @pytest.mark.asyncio
    async def test_distribution_valid_100pct(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = make_three_assessments()
        _setup_query_returns(mock_db, assessments)

        result = await service.calculate_grade_distribution(mock_db, uuid4())

        assert result.is_valid is True
        assert result.total_weight == 100.0

    @pytest.mark.asyncio
    async def test_distribution_invalid_under(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = [make_mock_assessment(weight=30.0)]
        _setup_query_returns(mock_db, assessments)

        result = await service.calculate_grade_distribution(mock_db, uuid4())

        assert result.is_valid is False
        assert result.total_weight == 30.0

    @pytest.mark.asyncio
    async def test_distribution_by_category(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = make_three_assessments()
        _setup_query_returns(mock_db, assessments)

        result = await service.calculate_grade_distribution(mock_db, uuid4())

        assert result.assessments_by_category["quiz"] == 20.0
        assert result.assessments_by_category["project"] == 40.0
        assert result.assessments_by_category["exam"] == 40.0

    @pytest.mark.asyncio
    async def test_distribution_by_type(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = make_three_assessments()
        _setup_query_returns(mock_db, assessments)

        result = await service.calculate_grade_distribution(mock_db, uuid4())

        assert result.assessments_by_type[AssessmentType.FORMATIVE.value] == 1
        assert result.assessments_by_type[AssessmentType.SUMMATIVE.value] == 2

    @pytest.mark.asyncio
    async def test_distribution_empty(self, service: AssessmentsService, mock_db: Mock) -> None:
        _setup_query_returns(mock_db, [])

        result = await service.calculate_grade_distribution(mock_db, uuid4())

        assert result.total_weight == 0.0
        assert result.formative_weight == 0.0
        assert result.summative_weight == 0.0
        assert result.is_valid is False


# ---------------------------------------------------------------------------
# TestValidateWeights
# ---------------------------------------------------------------------------


class TestValidateWeights:
    @pytest.mark.asyncio
    async def test_valid_weights(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = make_three_assessments()
        _setup_query_returns(mock_db, assessments)

        result = await service.validate_weights(mock_db, uuid4())

        assert result["is_valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_under_100_error(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = [make_mock_assessment(weight=60.0)]
        _setup_query_returns(mock_db, assessments)

        result = await service.validate_weights(mock_db, uuid4())

        assert result["is_valid"] is False
        assert any("60.0%" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_over_100_error(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = [
            make_mock_assessment(
                title="Exam",
                assessment_type=AssessmentType.SUMMATIVE.value,
                category="exam",
                weight=70.0,
            ),
            make_mock_assessment(
                title="Project",
                assessment_type=AssessmentType.SUMMATIVE.value,
                category="project",
                weight=50.0,
            ),
        ]
        _setup_query_returns(mock_db, assessments)

        result = await service.validate_weights(mock_db, uuid4())

        assert result["is_valid"] is False
        assert any("exceeds 100%" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_warnings(self, service: AssessmentsService, mock_db: Mock) -> None:
        # Formative > 40%, summative < 50%, only 2 categories
        assessments = [
            make_mock_assessment(
                title="Quiz 1",
                assessment_type=AssessmentType.FORMATIVE.value,
                category="quiz",
                weight=45.0,
            ),
            make_mock_assessment(
                title="Quiz 2",
                assessment_type=AssessmentType.FORMATIVE.value,
                category="quiz",
                weight=10.0,
            ),
            make_mock_assessment(
                title="Project",
                assessment_type=AssessmentType.SUMMATIVE.value,
                category="project",
                weight=45.0,
            ),
        ]
        _setup_query_returns(mock_db, assessments)

        result = await service.validate_weights(mock_db, uuid4())

        assert any("Formative" in w for w in result["warnings"])
        assert any("Summative" in w for w in result["warnings"])
        assert any("varied" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# TestTimeline
# ---------------------------------------------------------------------------


class TestTimeline:
    @pytest.mark.asyncio
    async def test_timeline_groups_by_week(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = make_three_assessments()
        _setup_query_returns(mock_db, assessments)

        result = await service.get_assessment_timeline(mock_db, uuid4())

        # 3 assessments in 3 different weeks → 3 groups
        assert len(result) == 3
        weeks = [entry["week_number"] for entry in result]
        assert weeks == sorted(weeks)

    @pytest.mark.asyncio
    async def test_timeline_skips_no_due_week(self, service: AssessmentsService, mock_db: Mock) -> None:
        assessments = [
            make_mock_assessment(due_week=4),
            make_mock_assessment(title="No Week", due_week=None),
        ]
        _setup_query_returns(mock_db, assessments)

        result = await service.get_assessment_timeline(mock_db, uuid4())

        assert len(result) == 1
        assert result[0]["week_number"] == 4

    @pytest.mark.asyncio
    async def test_workload_heavy_weeks(self, service: AssessmentsService, mock_db: Mock) -> None:
        # Two heavy assessments in week 12
        assessments = [
            make_mock_assessment(title="Exam", weight=40.0, due_week=12),
            make_mock_assessment(title="Project", weight=30.0, due_week=12),
            make_mock_assessment(title="Quiz", weight=10.0, due_week=4),
        ]
        _setup_query_returns(mock_db, assessments)

        result = await service.get_assessment_workload(mock_db, uuid4())

        assert 12 in result["heavy_weeks"]
        assert len(result["recommendations"]) > 0
        assert result["max_weight_in_week"] == 70.0


# ---------------------------------------------------------------------------
# TestMappingsAndOutcomes
# ---------------------------------------------------------------------------


class TestMappingsAndOutcomes:
    @pytest.mark.asyncio
    async def test_update_ulo_mappings(self, service: AssessmentsService, mock_db: Mock) -> None:
        existing = make_mock_assessment()
        _setup_query_returns(mock_db, existing)

        mapping_data = AssessmentMapping(ulo_ids=["ulo-1", "ulo-2"])
        await service.update_ulo_mappings(mock_db, uuid4(), mapping_data)

        # Should call execute for delete + 2 inserts = at least 3 calls
        assert mock_db.execute.call_count >= 3
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_ulo_mappings_not_found(self, service: AssessmentsService, mock_db: Mock) -> None:
        _setup_query_returns(mock_db, None)

        mapping_data = AssessmentMapping(ulo_ids=["ulo-1"])

        with pytest.raises(ValueError, match="not found"):
            await service.update_ulo_mappings(mock_db, uuid4(), mapping_data)

    @pytest.mark.asyncio
    async def test_add_assessment_outcome(self, service: AssessmentsService, mock_db: Mock) -> None:
        existing = make_mock_assessment()

        # First call returns assessment, second call returns max_order scalar
        call_count = 0
        first_query_chain = Mock()
        first_query_chain.filter.return_value = first_query_chain
        first_query_chain.options.return_value = first_query_chain
        first_query_chain.first.return_value = existing

        second_query_chain = Mock()
        second_query_chain.filter.return_value = second_query_chain
        second_query_chain.scalar.return_value = 2  # max existing order_index

        def side_effect(*args: object) -> Mock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_query_chain
            return second_query_chain

        mock_db.query.side_effect = side_effect

        outcome_data = ALOCreate(description="Demonstrate understanding of testing", order_index=0)
        result = await service.add_assessment_outcome(mock_db, uuid4(), outcome_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert isinstance(result, AssessmentLearningOutcome)
