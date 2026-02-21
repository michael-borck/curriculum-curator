"""
Tests for Assessments service using in-memory SQLite.

Validates CRUD operations, grade distribution, weight validation,
timeline grouping, workload analysis, and ULO mapping operations.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from app.models.assessment import Assessment, AssessmentType
from app.models.learning_outcome import AssessmentLearningOutcome, UnitLearningOutcome
from app.schemas.assessments import (
    AssessmentCreate,
    AssessmentMapping,
    AssessmentUpdate,
    Rubric,
    RubricCriterion,
)
from app.schemas.learning_outcomes import ALOCreate
from app.services.assessments_service import AssessmentsService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.unit import Unit
    from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid(val: object) -> uuid.UUID:
    return uuid.UUID(str(val))


def _make_create(
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


def _insert_assessment(
    db: Session,
    unit: Unit,
    *,
    title: str = "Quiz 1",
    assessment_type: str = AssessmentType.FORMATIVE.value,
    category: str = "quiz",
    weight: float = 20.0,
    due_week: int | None = 4,
) -> Assessment:
    """Insert a real Assessment row."""
    a = Assessment(
        id=str(uuid.uuid4()),
        unit_id=unit.id,
        title=title,
        type=assessment_type,
        category=category,
        weight=weight,
        due_week=due_week,
        description=f"Description for {title}",
        release_week=(due_week - 2) if due_week and due_week > 2 else 1,
        status="draft",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _insert_three_assessments(db: Session, unit: Unit) -> list[Assessment]:
    """Insert 3 assessments totalling 100%."""
    return [
        _insert_assessment(
            db,
            unit,
            title="Quiz 1",
            assessment_type=AssessmentType.FORMATIVE.value,
            category="quiz",
            weight=20.0,
            due_week=4,
        ),
        _insert_assessment(
            db,
            unit,
            title="Project",
            assessment_type=AssessmentType.SUMMATIVE.value,
            category="project",
            weight=40.0,
            due_week=8,
        ),
        _insert_assessment(
            db,
            unit,
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


# ---------------------------------------------------------------------------
# TestCreateAssessment
# ---------------------------------------------------------------------------


class TestCreateAssessment:
    @pytest.mark.asyncio
    async def test_create_success(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        data = _make_create()
        result = await service.create_assessment(test_db, _uid(test_unit.id), data)

        assert result.title == "Quiz 1"
        assert result.type == AssessmentType.FORMATIVE.value
        assert result.weight == 20.0
        assert result.unit_id == test_unit.id

        # Verify it persisted
        from_db = test_db.query(Assessment).filter(Assessment.id == result.id).first()
        assert from_db is not None
        assert from_db.title == "Quiz 1"

    @pytest.mark.asyncio
    async def test_create_with_rubric(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
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
        data = _make_create(rubric=rubric)
        result = await service.create_assessment(test_db, _uid(test_unit.id), data)

        assert result.rubric is not None
        assert result.rubric["total_points"] == 10.0
        assert len(result.rubric["criteria"]) == 1


# ---------------------------------------------------------------------------
# TestUpdateAssessment
# ---------------------------------------------------------------------------


class TestUpdateAssessment:
    @pytest.mark.asyncio
    async def test_update_success(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        existing = _insert_assessment(test_db, test_unit)

        update_data = AssessmentUpdate(title="Updated Quiz", weight=25.0)
        result = await service.update_assessment(
            test_db, _uid(existing.id), update_data
        )

        assert result is not None
        assert result.title == "Updated Quiz"
        assert result.weight == 25.0

    @pytest.mark.asyncio
    async def test_update_not_found(
        self, service: AssessmentsService, test_db: Session
    ) -> None:
        update_data = AssessmentUpdate(title="Updated Quiz")
        result = await service.update_assessment(test_db, uuid.uuid4(), update_data)
        assert result is None


# ---------------------------------------------------------------------------
# TestDeleteAssessment
# ---------------------------------------------------------------------------


class TestDeleteAssessment:
    @pytest.mark.asyncio
    async def test_delete_success(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        existing = _insert_assessment(test_db, test_unit)
        existing_id = str(existing.id)
        result = await service.delete_assessment(test_db, _uid(existing_id))

        assert result is True
        assert (
            test_db.query(Assessment).filter(Assessment.id == existing_id).first()
            is None
        )

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self, service: AssessmentsService, test_db: Session
    ) -> None:
        result = await service.delete_assessment(test_db, uuid.uuid4())
        assert result is False


# ---------------------------------------------------------------------------
# TestGetAssessments
# ---------------------------------------------------------------------------


class TestGetAssessments:
    @pytest.mark.asyncio
    async def test_get_assessment_by_id(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        expected = _insert_assessment(test_db, test_unit)
        result = await service.get_assessment(test_db, _uid(expected.id))
        assert result is not None
        assert result.id == expected.id

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(
        self, service: AssessmentsService, test_db: Session
    ) -> None:
        result = await service.get_assessment(test_db, uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_assessments_by_unit(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_three_assessments(test_db, test_unit)
        result = await service.get_assessments_by_unit(test_db, _uid(test_unit.id))
        assert len(result) == 3


# ---------------------------------------------------------------------------
# TestGradeDistribution
# ---------------------------------------------------------------------------


class TestGradeDistribution:
    @pytest.mark.asyncio
    async def test_distribution_valid_100pct(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_three_assessments(test_db, test_unit)
        result = await service.calculate_grade_distribution(test_db, _uid(test_unit.id))

        assert result.is_valid is True
        assert result.total_weight == 100.0

    @pytest.mark.asyncio
    async def test_distribution_invalid_under(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_assessment(test_db, test_unit, weight=30.0)
        result = await service.calculate_grade_distribution(test_db, _uid(test_unit.id))

        assert result.is_valid is False
        assert result.total_weight == 30.0

    @pytest.mark.asyncio
    async def test_distribution_by_category(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_three_assessments(test_db, test_unit)
        result = await service.calculate_grade_distribution(test_db, _uid(test_unit.id))

        assert result.assessments_by_category["quiz"] == 20.0
        assert result.assessments_by_category["project"] == 40.0
        assert result.assessments_by_category["exam"] == 40.0

    @pytest.mark.asyncio
    async def test_distribution_by_type(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_three_assessments(test_db, test_unit)
        result = await service.calculate_grade_distribution(test_db, _uid(test_unit.id))

        assert result.assessments_by_type[AssessmentType.FORMATIVE.value] == 1
        assert result.assessments_by_type[AssessmentType.SUMMATIVE.value] == 2

    @pytest.mark.asyncio
    async def test_distribution_empty(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        result = await service.calculate_grade_distribution(test_db, _uid(test_unit.id))

        assert result.total_weight == 0.0
        assert result.formative_weight == 0.0
        assert result.summative_weight == 0.0
        assert result.is_valid is False


# ---------------------------------------------------------------------------
# TestValidateWeights
# ---------------------------------------------------------------------------


class TestValidateWeights:
    @pytest.mark.asyncio
    async def test_valid_weights(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_three_assessments(test_db, test_unit)
        result = await service.validate_weights(test_db, _uid(test_unit.id))

        assert result["is_valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_under_100_error(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_assessment(test_db, test_unit, weight=60.0)
        result = await service.validate_weights(test_db, _uid(test_unit.id))

        assert result["is_valid"] is False
        assert any("60.0%" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_over_100_error(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_assessment(
            test_db,
            test_unit,
            title="Exam",
            assessment_type=AssessmentType.SUMMATIVE.value,
            category="exam",
            weight=70.0,
        )
        _insert_assessment(
            test_db,
            test_unit,
            title="Project",
            assessment_type=AssessmentType.SUMMATIVE.value,
            category="project",
            weight=50.0,
        )
        result = await service.validate_weights(test_db, _uid(test_unit.id))

        assert result["is_valid"] is False
        assert any("exceeds 100%" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_warnings(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_assessment(
            test_db,
            test_unit,
            title="Quiz 1",
            assessment_type=AssessmentType.FORMATIVE.value,
            category="quiz",
            weight=45.0,
        )
        _insert_assessment(
            test_db,
            test_unit,
            title="Quiz 2",
            assessment_type=AssessmentType.FORMATIVE.value,
            category="quiz",
            weight=10.0,
        )
        _insert_assessment(
            test_db,
            test_unit,
            title="Project",
            assessment_type=AssessmentType.SUMMATIVE.value,
            category="project",
            weight=45.0,
        )
        result = await service.validate_weights(test_db, _uid(test_unit.id))

        assert any("Formative" in w for w in result["warnings"])
        assert any("Summative" in w for w in result["warnings"])
        assert any("varied" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# TestTimeline
# ---------------------------------------------------------------------------


class TestTimeline:
    @pytest.mark.asyncio
    async def test_timeline_groups_by_week(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_three_assessments(test_db, test_unit)
        result = await service.get_assessment_timeline(test_db, _uid(test_unit.id))

        assert len(result) == 3
        weeks = [entry["week_number"] for entry in result]
        assert weeks == sorted(weeks)

    @pytest.mark.asyncio
    async def test_timeline_skips_no_due_week(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_assessment(test_db, test_unit, due_week=4)
        _insert_assessment(test_db, test_unit, title="No Week", due_week=None)

        result = await service.get_assessment_timeline(test_db, _uid(test_unit.id))

        assert len(result) == 1
        assert result[0]["week_number"] == 4

    @pytest.mark.asyncio
    async def test_workload_heavy_weeks(
        self, service: AssessmentsService, test_db: Session, test_unit: Unit
    ) -> None:
        _insert_assessment(test_db, test_unit, title="Exam", weight=40.0, due_week=12)
        _insert_assessment(
            test_db, test_unit, title="Project", weight=30.0, due_week=12
        )
        _insert_assessment(test_db, test_unit, title="Quiz", weight=10.0, due_week=4)

        result = await service.get_assessment_workload(test_db, _uid(test_unit.id))

        assert 12 in result["heavy_weeks"]
        assert len(result["recommendations"]) > 0
        assert result["max_weight_in_week"] == 70.0


# ---------------------------------------------------------------------------
# TestMappingsAndOutcomes
# ---------------------------------------------------------------------------


class TestMappingsAndOutcomes:
    @pytest.mark.asyncio
    async def test_update_ulo_mappings(
        self,
        service: AssessmentsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ) -> None:
        assessment = _insert_assessment(test_db, test_unit)

        # Create real ULOs to map to (commit each individually for GUID compat)
        ulo1 = UnitLearningOutcome(
            id=str(uuid.uuid4()),
            unit_id=test_unit.id,
            outcome_type="ulo",
            outcome_code="ULO1",
            outcome_text="Test ULO 1",
            bloom_level="APPLY",
            sequence_order=1,
            created_by_id=test_user.id,
        )
        test_db.add(ulo1)
        test_db.commit()

        ulo2 = UnitLearningOutcome(
            id=str(uuid.uuid4()),
            unit_id=test_unit.id,
            outcome_type="ulo",
            outcome_code="ULO2",
            outcome_text="Test ULO 2",
            bloom_level="ANALYZE",
            sequence_order=2,
            created_by_id=test_user.id,
        )
        test_db.add(ulo2)
        test_db.commit()

        mapping_data = AssessmentMapping(ulo_ids=[str(ulo1.id), str(ulo2.id)])
        result = await service.update_ulo_mappings(
            test_db, _uid(assessment.id), mapping_data
        )

        assert result is not None
        assert len(result.learning_outcomes) == 2

    @pytest.mark.asyncio
    async def test_update_ulo_mappings_not_found(
        self, service: AssessmentsService, test_db: Session
    ) -> None:
        mapping_data = AssessmentMapping(ulo_ids=["fake-id"])
        with pytest.raises(ValueError, match="not found"):
            await service.update_ulo_mappings(test_db, uuid.uuid4(), mapping_data)

    @pytest.mark.asyncio
    async def test_add_assessment_outcome(
        self,
        service: AssessmentsService,
        test_db: Session,
        test_unit: Unit,
    ) -> None:
        assessment = _insert_assessment(test_db, test_unit)

        outcome_data = ALOCreate(
            description="Demonstrate understanding of testing", order_index=0
        )
        result = await service.add_assessment_outcome(
            test_db, _uid(assessment.id), outcome_data
        )

        assert isinstance(result, AssessmentLearningOutcome)
        assert result.description == "Demonstrate understanding of testing"
        assert result.assessment_id == assessment.id
