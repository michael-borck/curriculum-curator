"""
Tests for Materials service using in-memory SQLite.
"""

import uuid
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.learning_outcome import BloomLevel, OutcomeType, UnitLearningOutcome
from app.models.local_learning_outcome import LocalLearningOutcome
from app.models.mappings import material_ulo_mappings
from app.models.unit import Unit
from app.models.user import User
from app.models.weekly_material import MaterialStatus, WeeklyMaterial
from app.schemas.learning_outcomes import LLOCreate
from app.schemas.materials import (
    MaterialCreate,
    MaterialDuplicate,
    MaterialFilter,
    MaterialMapping,
    MaterialReorder,
    MaterialUpdate,
)
from app.services.materials_service import MaterialsService


def _uid(val: str | UUID) -> UUID:
    if isinstance(val, UUID):
        return val
    return UUID(str(val))


@pytest.fixture
def mat_service() -> MaterialsService:
    return MaterialsService()


def _make_material_create(
    week: int = 1,
    title: str = "Lecture 1",
    mat_type: str = "lecture",
    duration: int | None = 60,
    order: int = 0,
) -> MaterialCreate:
    return MaterialCreate(
        week_number=week,
        title=title,
        type=mat_type,
        description=f"Description for {title}",
        duration_minutes=duration,
        order_index=order,
        status=MaterialStatus.DRAFT.value,
    )


def _insert_ulo(
    db: Session, unit_id: str, user_id: str, code: str = "ULO1"
) -> UnitLearningOutcome:
    ulo = UnitLearningOutcome(
        unit_id=unit_id,
        outcome_type=OutcomeType.ULO.value,
        outcome_code=code,
        outcome_text="Test outcome",
        bloom_level=BloomLevel.APPLY.value,
        sequence_order=0,
        created_by_id=user_id,
        is_active=True,
        is_measurable=True,
    )
    db.add(ulo)
    db.commit()
    db.refresh(ulo)
    return ulo


# ─── CREATE ──────────────────────────────────────────────────


class TestCreateMaterial:
    @pytest.mark.asyncio
    async def test_create_material(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        data = _make_material_create(title="Week 1 Lecture")
        result = await mat_service.create_material(test_db, _uid(test_unit.id), data)

        assert result.title == "Week 1 Lecture"
        assert result.week_number == 1
        assert result.type == "lecture"
        assert result.unit_id == test_unit.id

    @pytest.mark.asyncio
    async def test_create_auto_order_index(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        d1 = MaterialCreate(week_number=1, title="M1", type="lecture", status="draft")
        d2 = MaterialCreate(week_number=1, title="M2", type="lecture", status="draft")
        m1 = await mat_service.create_material(test_db, uid, d1)
        m2 = await mat_service.create_material(test_db, uid, d2)

        assert m1.order_index == 0
        assert m2.order_index == 1


# ─── UPDATE ──────────────────────────────────────────────────


class TestUpdateMaterial:
    @pytest.mark.asyncio
    async def test_update_material(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        material = await mat_service.create_material(
            test_db, _uid(test_unit.id), _make_material_create()
        )
        update = MaterialUpdate(title="Updated Title", duration_minutes=90)
        result = await mat_service.update_material(test_db, _uid(material.id), update)

        assert result is not None
        assert result.title == "Updated Title"
        assert result.duration_minutes == 90

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(
        self, mat_service: MaterialsService, test_db: Session
    ):
        update = MaterialUpdate(title="Ghost")
        result = await mat_service.update_material(test_db, uuid.uuid4(), update)
        assert result is None


# ─── DELETE ──────────────────────────────────────────────────


class TestDeleteMaterial:
    @pytest.mark.asyncio
    async def test_delete_material(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        material = await mat_service.create_material(
            test_db, _uid(test_unit.id), _make_material_create()
        )
        deleted = await mat_service.delete_material(test_db, _uid(material.id))
        assert deleted is True

        result = await mat_service.get_material(test_db, _uid(material.id))
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(
        self, mat_service: MaterialsService, test_db: Session
    ):
        result = await mat_service.delete_material(test_db, uuid.uuid4())
        assert result is False


# ─── GET ─────────────────────────────────────────────────────


class TestGetMaterial:
    @pytest.mark.asyncio
    async def test_get_material(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        material = await mat_service.create_material(
            test_db, _uid(test_unit.id), _make_material_create()
        )
        result = await mat_service.get_material(test_db, _uid(material.id))
        assert result is not None
        assert result.title == "Lecture 1"

    @pytest.mark.asyncio
    async def test_get_materials_by_week(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="W1A")
        )
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="W1B")
        )
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=2, title="W2A")
        )

        results = await mat_service.get_materials_by_week(test_db, uid, 1)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_materials_by_unit(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="A")
        )
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=2, title="B")
        )

        results = await mat_service.get_materials_by_unit(test_db, uid)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_materials_with_filter(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        await mat_service.create_material(
            test_db,
            uid,
            _make_material_create(week=1, title="Lecture", mat_type="lecture"),
        )
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="Quiz", mat_type="quiz")
        )

        filt = MaterialFilter(type="quiz")
        results = await mat_service.get_materials_by_unit(test_db, uid, filt)
        assert len(results) == 1
        assert results[0].type == "quiz"

    @pytest.mark.asyncio
    async def test_get_materials_search_filter(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        await mat_service.create_material(
            test_db, uid, _make_material_create(title="Python Basics")
        )
        await mat_service.create_material(
            test_db, uid, _make_material_create(title="Java Intro")
        )

        filt = MaterialFilter(search="Python")
        results = await mat_service.get_materials_by_unit(test_db, uid, filt)
        assert len(results) == 1
        assert "Python" in results[0].title


# ─── DUPLICATE ───────────────────────────────────────────────


class TestDuplicateMaterial:
    @pytest.mark.asyncio
    async def test_duplicate_material(
        self,
        mat_service: MaterialsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        uid = _uid(test_unit.id)
        original = await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="Original")
        )

        dup_data = MaterialDuplicate(target_week=3, new_title="Copied Material")
        result = await mat_service.duplicate_material(
            test_db, _uid(original.id), dup_data
        )

        assert result.title == "Copied Material"
        assert result.week_number == 3
        assert result.status == MaterialStatus.DRAFT.value
        assert result.id != original.id

    @pytest.mark.asyncio
    async def test_duplicate_copies_local_outcomes(
        self,
        mat_service: MaterialsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        uid = _uid(test_unit.id)
        original = await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="With LLOs")
        )
        # Add a local outcome
        llo = LocalLearningOutcome(
            material_id=original.id,
            description="Students will understand X",
            order_index=0,
        )
        test_db.add(llo)
        test_db.commit()

        dup_data = MaterialDuplicate(target_week=2)
        result = await mat_service.duplicate_material(
            test_db, _uid(original.id), dup_data
        )

        # Fetch with outcomes
        fetched = await mat_service.get_material(
            test_db, _uid(result.id), include_outcomes=True
        )
        assert fetched is not None
        assert len(fetched.local_outcomes) == 1

    @pytest.mark.asyncio
    async def test_duplicate_nonexistent_raises(
        self, mat_service: MaterialsService, test_db: Session
    ):
        dup_data = MaterialDuplicate(target_week=2)
        with pytest.raises(ValueError, match="not found"):
            await mat_service.duplicate_material(test_db, uuid.uuid4(), dup_data)


# ─── REORDER ─────────────────────────────────────────────────


class TestReorderMaterials:
    @pytest.mark.asyncio
    async def test_reorder(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        m1 = await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="A")
        )
        m2 = await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="B")
        )

        reorder = MaterialReorder(material_ids=[str(m2.id), str(m1.id)])
        results = await mat_service.reorder_materials(test_db, uid, 1, reorder)

        order_map = {r.title: r.order_index for r in results}
        assert order_map["B"] < order_map["A"]

    @pytest.mark.asyncio
    async def test_reorder_invalid_id_raises(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        reorder = MaterialReorder(material_ids=["nonexistent"])
        with pytest.raises(ValueError, match="not found"):
            await mat_service.reorder_materials(test_db, uid, 1, reorder)


# ─── ULO MAPPINGS ────────────────────────────────────────────


class TestULOMappings:
    @pytest.mark.asyncio
    async def test_update_ulo_mappings(
        self,
        mat_service: MaterialsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        uid = _uid(test_unit.id)
        material = await mat_service.create_material(
            test_db, uid, _make_material_create()
        )
        ulo = _insert_ulo(test_db, test_unit.id, test_user.id)

        mapping = MaterialMapping(ulo_ids=[str(ulo.id)])
        result = await mat_service.update_ulo_mappings(
            test_db, _uid(material.id), mapping
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_ulo_mappings_clears_existing(
        self,
        mat_service: MaterialsService,
        test_db: Session,
        test_unit: Unit,
        test_user: User,
    ):
        uid = _uid(test_unit.id)
        material = await mat_service.create_material(
            test_db, uid, _make_material_create()
        )
        ulo1 = _insert_ulo(test_db, test_unit.id, test_user.id, code="U1")
        ulo2 = _insert_ulo(test_db, test_unit.id, test_user.id, code="U2")

        # Map to ulo1 first
        await mat_service.update_ulo_mappings(
            test_db, _uid(material.id), MaterialMapping(ulo_ids=[str(ulo1.id)])
        )
        # Then replace with ulo2
        await mat_service.update_ulo_mappings(
            test_db, _uid(material.id), MaterialMapping(ulo_ids=[str(ulo2.id)])
        )

        # Check only ulo2 is mapped
        rows = test_db.execute(
            material_ulo_mappings.select().where(
                material_ulo_mappings.c.material_id == material.id
            )
        ).fetchall()
        assert len(rows) == 1
        assert str(rows[0].ulo_id) == str(ulo2.id)


# ─── LOCAL OUTCOMES ──────────────────────────────────────────


class TestAddLocalOutcome:
    @pytest.mark.asyncio
    async def test_add_local_outcome(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        material = await mat_service.create_material(
            test_db, _uid(test_unit.id), _make_material_create()
        )
        llo_data = LLOCreate(description="Understand basic concepts", order_index=0)
        result = await mat_service.add_local_outcome(
            test_db, _uid(material.id), llo_data
        )

        assert result.description == "Understand basic concepts"
        assert result.material_id == material.id

    @pytest.mark.asyncio
    async def test_add_local_outcome_nonexistent_material_raises(
        self, mat_service: MaterialsService, test_db: Session
    ):
        llo_data = LLOCreate(description="Ghost", order_index=0)
        with pytest.raises(ValueError, match="not found"):
            await mat_service.add_local_outcome(test_db, uuid.uuid4(), llo_data)


# ─── WEEK SUMMARY ────────────────────────────────────────────


class TestWeekSummary:
    @pytest.mark.asyncio
    async def test_week_summary(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        uid = _uid(test_unit.id)
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="L1", duration=60)
        )
        await mat_service.create_material(
            test_db, uid, _make_material_create(week=1, title="L2", duration=30)
        )

        summary = await mat_service.get_week_summary(test_db, uid, 1)

        assert summary["week_number"] == 1
        assert summary["total_materials"] == 2
        assert summary["total_duration_minutes"] == 90
        assert summary["total_duration_hours"] == 1.5

    @pytest.mark.asyncio
    async def test_week_summary_empty(
        self, mat_service: MaterialsService, test_db: Session, test_unit: Unit
    ):
        summary = await mat_service.get_week_summary(test_db, _uid(test_unit.id), 99)
        assert summary["total_materials"] == 0
        assert summary["total_duration_minutes"] == 0
