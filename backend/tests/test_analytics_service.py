"""
Tests for Analytics service using in-memory SQLite.
"""

import uuid
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, AssessmentStatus
from app.models.learning_outcome import BloomLevel, OutcomeType, UnitLearningOutcome
from app.models.mappings import assessment_ulo_mappings, material_ulo_mappings
from app.models.unit import Unit
from app.models.user import User
from app.models.weekly_material import MaterialStatus, WeeklyMaterial
from app.services.analytics_service import AnalyticsService


def _uid(val: str | UUID) -> UUID:
    if isinstance(val, UUID):
        return val
    return UUID(str(val))


@pytest.fixture
def analytics() -> AnalyticsService:
    return AnalyticsService()


def _add_ulo(db: Session, unit: Unit, user: User, code: str = "ULO1") -> UnitLearningOutcome:
    ulo = UnitLearningOutcome(
        unit_id=unit.id,
        outcome_type=OutcomeType.ULO.value,
        outcome_code=code,
        outcome_text=f"Outcome {code}",
        bloom_level=BloomLevel.APPLY.value,
        sequence_order=0,
        created_by_id=user.id,
        is_active=True,
        is_measurable=True,
    )
    db.add(ulo)
    db.commit()
    db.refresh(ulo)
    return ulo


def _add_material(
    db: Session,
    unit: Unit,
    week: int = 1,
    title: str = "Lecture",
    status: str = MaterialStatus.DRAFT.value,
    duration: int = 60,
) -> WeeklyMaterial:
    m = WeeklyMaterial(
        unit_id=unit.id,
        week_number=week,
        title=title,
        type="lecture",
        status=status,
        duration_minutes=duration,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def _add_assessment(
    db: Session,
    unit: Unit,
    title: str = "Exam",
    weight: float = 50.0,
    status: str = AssessmentStatus.DRAFT.value,
    due_week: int | None = None,
    duration: str | None = None,
) -> Assessment:
    a = Assessment(
        unit_id=unit.id,
        title=title,
        type="summative",
        category="exam",
        weight=weight,
        status=status,
        due_week=due_week,
        duration=duration,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


# ─── UNIT OVERVIEW ───────────────────────────────────────────


class TestUnitOverview:
    @pytest.mark.asyncio
    async def test_empty_unit(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.get_unit_overview(test_db, _uid(test_unit.id))
        assert result["ulo_count"] == 0
        assert result["materials"]["total"] == 0
        assert result["assessments"]["total"] == 0
        assert result["total_assessment_weight"] == 0.0
        assert result["weeks_with_content"] == 0

    @pytest.mark.asyncio
    async def test_unit_with_content(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        _add_ulo(test_db, test_unit, test_user)
        _add_material(test_db, test_unit, status=MaterialStatus.DRAFT.value)
        _add_material(test_db, test_unit, week=2, status=MaterialStatus.PUBLISHED.value)
        _add_assessment(test_db, test_unit, weight=60.0)
        _add_assessment(test_db, test_unit, title="Quiz", weight=40.0)

        result = await analytics.get_unit_overview(test_db, _uid(test_unit.id))
        assert result["ulo_count"] == 1
        assert result["materials"]["total"] == 2
        assert result["assessments"]["total"] == 2
        assert result["total_assessment_weight"] == 100.0


# ─── UNIT PROGRESS ───────────────────────────────────────────


class TestUnitProgress:
    @pytest.mark.asyncio
    async def test_empty_progress(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.get_unit_progress(test_db, _uid(test_unit.id))
        assert result["materials"]["total"] == 0
        assert result["overall_completion"] == 0

    @pytest.mark.asyncio
    async def test_progress_with_published(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
    ):
        _add_material(test_db, test_unit, status=MaterialStatus.PUBLISHED.value)
        _add_material(test_db, test_unit, status=MaterialStatus.DRAFT.value)
        _add_assessment(test_db, test_unit, status=AssessmentStatus.PUBLISHED.value)

        result = await analytics.get_unit_progress(test_db, _uid(test_unit.id))
        assert result["materials"]["published"] == 1
        assert result["materials"]["draft"] == 1
        assert result["materials"]["completion_percentage"] == 50.0
        assert result["assessments"]["published"] == 1

    @pytest.mark.asyncio
    async def test_progress_with_details(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
    ):
        _add_material(test_db, test_unit, title="Draft Mat", status=MaterialStatus.DRAFT.value)
        _add_assessment(test_db, test_unit, title="Draft Assess", status=AssessmentStatus.DRAFT.value)

        result = await analytics.get_unit_progress(
            test_db, _uid(test_unit.id), include_details=True
        )
        assert "incomplete_items" in result
        assert len(result["incomplete_items"]["materials"]) == 1
        assert len(result["incomplete_items"]["assessments"]) == 1


# ─── COMPLETION REPORT ───────────────────────────────────────


class TestCompletionReport:
    @pytest.mark.asyncio
    async def test_completion_empty(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.get_completion_report(test_db, _uid(test_unit.id))
        assert result["ulos_total"] == 0
        assert result["completion_percentage"] == 0

    @pytest.mark.asyncio
    async def test_completion_with_coverage(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        ulo = _add_ulo(test_db, test_unit, test_user)
        material = _add_material(test_db, test_unit)
        assessment = _add_assessment(test_db, test_unit)

        # Map ULO to material and assessment
        test_db.execute(
            material_ulo_mappings.insert().values(material_id=material.id, ulo_id=ulo.id)
        )
        test_db.execute(
            assessment_ulo_mappings.insert().values(assessment_id=assessment.id, ulo_id=ulo.id)
        )
        test_db.commit()

        result = await analytics.get_completion_report(test_db, _uid(test_unit.id))
        assert result["ulos_total"] == 1
        assert result["ulos_fully_covered"] == 1
        assert result["completion_percentage"] == 100.0


# ─── ALIGNMENT REPORT ────────────────────────────────────────


class TestAlignmentReport:
    @pytest.mark.asyncio
    async def test_alignment_empty(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.get_alignment_report(test_db, _uid(test_unit.id))
        assert result["summary"]["total_ulos"] == 0

    @pytest.mark.asyncio
    async def test_alignment_unaligned(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        _add_ulo(test_db, test_unit, test_user)
        result = await analytics.get_alignment_report(test_db, _uid(test_unit.id))

        assert result["summary"]["total_ulos"] == 1
        assert result["summary"]["unaligned"] == 1
        assert result["summary"]["fully_aligned"] == 0
        assert len(result["recommendations"]) > 0


# ─── WEEKLY WORKLOAD ─────────────────────────────────────────


class TestWeeklyWorkload:
    @pytest.mark.asyncio
    async def test_workload_empty(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.get_weekly_workload(test_db, _uid(test_unit.id), 1, 4)
        assert result == []

    @pytest.mark.asyncio
    async def test_workload_with_data(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
    ):
        _add_material(test_db, test_unit, week=1, duration=60)
        _add_material(test_db, test_unit, week=1, duration=30)
        _add_assessment(test_db, test_unit, due_week=1, duration="120")

        result = await analytics.get_weekly_workload(test_db, _uid(test_unit.id), 1, 2)
        assert len(result) == 1
        week_data = result[0]
        assert week_data["week_number"] == 1
        assert week_data["material_count"] == 2
        assert week_data["material_duration_minutes"] == 90
        assert week_data["assessment_count"] == 1


# ─── RECOMMENDATIONS ─────────────────────────────────────────


class TestRecommendations:
    @pytest.mark.asyncio
    async def test_recommendations_weight_issue(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
    ):
        _add_assessment(test_db, test_unit, weight=30.0)
        result = await analytics.get_recommendations(test_db, _uid(test_unit.id))
        issues = [r["issue"] for r in result["recommendations"]]
        assert any("100%" in i for i in issues)


# ─── VALIDATE UNIT ───────────────────────────────────────────


class TestValidateUnit:
    @pytest.mark.asyncio
    async def test_validate_empty_unit(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.validate_unit(test_db, _uid(test_unit.id))
        assert result["is_valid"] is False
        assert any("No Unit Learning Outcomes" in e for e in result["errors"])
        assert any("No weekly materials" in e for e in result["errors"])
        assert any("No assessments" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_weight_mismatch(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        _add_ulo(test_db, test_unit, test_user)
        _add_material(test_db, test_unit)
        _add_assessment(test_db, test_unit, weight=50.0)

        result = await analytics.validate_unit(test_db, _uid(test_unit.id))
        assert result["is_valid"] is False
        assert any("not 100%" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_strict_mode_few_ulos(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        _add_ulo(test_db, test_unit, test_user, code="ULO1")
        _add_material(test_db, test_unit)
        _add_assessment(test_db, test_unit, weight=100.0)

        result = await analytics.validate_unit(test_db, _uid(test_unit.id), strict_mode=True)
        assert any("Only 1 ULO" in w for w in result["warnings"])


# ─── QUALITY SCORE ───────────────────────────────────────────


class TestQualityScore:
    @pytest.mark.asyncio
    async def test_quality_score_empty(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.calculate_quality_score(test_db, _uid(test_unit.id))
        assert result["overall_score"] == 0.0
        assert result["grade"] == "F"

    @pytest.mark.asyncio
    async def test_quality_score_perfect(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        ulo = _add_ulo(test_db, test_unit, test_user)
        mat = _add_material(test_db, test_unit, status=MaterialStatus.PUBLISHED.value)
        ass = _add_assessment(test_db, test_unit, weight=100.0, status=AssessmentStatus.PUBLISHED.value)

        # Map ULO
        test_db.execute(material_ulo_mappings.insert().values(material_id=mat.id, ulo_id=ulo.id))
        test_db.execute(assessment_ulo_mappings.insert().values(assessment_id=ass.id, ulo_id=ulo.id))
        test_db.commit()

        result = await analytics.calculate_quality_score(test_db, _uid(test_unit.id))
        assert result["overall_score"] > 50.0
        assert result["sub_scores"]["assessment_weights"] == 100.0


# ─── UNIT STATISTICS ─────────────────────────────────────────


class TestUnitStatistics:
    @pytest.mark.asyncio
    async def test_statistics(
        self,
        analytics: AnalyticsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        _add_ulo(test_db, test_unit, test_user)
        _add_material(test_db, test_unit, week=1, duration=60)
        _add_assessment(test_db, test_unit, weight=100.0)

        result = await analytics.get_unit_statistics(test_db, _uid(test_unit.id))
        assert result["materials"]["total"] == 1
        assert result["assessments"]["total"] == 1
        assert result["learning_outcomes"]["total_ulos"] == 1


# ─── EXPORT ──────────────────────────────────────────────────


class TestExport:
    @pytest.mark.asyncio
    async def test_export_json(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.export_unit_data(test_db, _uid(test_unit.id), "json")
        assert result["format"] == "json"
        assert "data" in result

    @pytest.mark.asyncio
    async def test_export_csv(
        self, analytics: AnalyticsService, test_db: Session, test_unit: Unit
    ):
        result = await analytics.export_unit_data(test_db, _uid(test_unit.id), "csv")
        assert result["csv_ready"] is True


# ─── PRIVATE METHODS ─────────────────────────────────────────


class TestPrivateMethods:
    def test_score_to_grade(self, analytics: AnalyticsService):
        assert analytics._score_to_grade(95) == "A"
        assert analytics._score_to_grade(85) == "B"
        assert analytics._score_to_grade(75) == "C"
        assert analytics._score_to_grade(65) == "D"
        assert analytics._score_to_grade(45) == "F"

    def test_workload_variance_empty(self, analytics: AnalyticsService):
        assert analytics._calculate_workload_variance([]) == 0.0

    def test_workload_variance_uniform(self, analytics: AnalyticsService):
        workload = [{"total_duration_minutes": 60}] * 3
        assert analytics._calculate_workload_variance(workload) == 0.0
