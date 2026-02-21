"""
Tests for Learning Design service — uses real in-memory SQLite (no mocks).
"""

import pytest
from sqlalchemy.orm import Session

from app.models.learning_design import DesignStatus, LearningDesign
from app.models.unit import Unit
from app.schemas.learning_design import DesignCreate, DesignUpdate
from app.services.design_service import design_service


@pytest.mark.asyncio
async def test_create_design(test_db: Session, test_unit: Unit):
    data = DesignCreate(
        unit_id=str(test_unit.id),
        content={"topic": "Test Topic", "objectives": ["Learn testing"]},
        version="1.0",
    )
    design = await design_service.create_design(test_db, data)

    assert design.id is not None
    assert str(design.unit_id) == str(test_unit.id)
    assert design.status == DesignStatus.DRAFT.value
    assert design.content["topic"] == "Test Topic"


@pytest.mark.asyncio
async def test_get_design(test_db: Session, test_design: LearningDesign):
    result = await design_service.get_design(test_db, str(test_design.id))
    assert result is not None
    assert str(result.id) == str(test_design.id)


@pytest.mark.asyncio
async def test_get_design_not_found(test_db: Session):
    result = await design_service.get_design(
        test_db, "00000000-0000-0000-0000-000000000000"
    )
    assert result is None


@pytest.mark.asyncio
async def test_list_by_unit(
    test_db: Session, test_design: LearningDesign, test_unit: Unit
):
    results = await design_service.list_by_unit(test_db, str(test_unit.id))
    assert len(results) >= 1
    assert any(str(r.id) == str(test_design.id) for r in results)


@pytest.mark.asyncio
async def test_update_design(test_db: Session, test_design: LearningDesign):
    update_data = DesignUpdate(content={"topic": "Updated Topic"}, version="1.1")
    updated = await design_service.update_design(
        test_db, str(test_design.id), update_data
    )

    assert updated is not None
    assert updated.content["topic"] == "Updated Topic"
    assert updated.version == "1.1"


@pytest.mark.asyncio
async def test_update_design_not_found(test_db: Session):
    update_data = DesignUpdate(content={"topic": "Updated"})
    result = await design_service.update_design(
        test_db, "00000000-0000-0000-0000-000000000000", update_data
    )
    assert result is None


@pytest.mark.asyncio
async def test_delete_design(test_db: Session, test_design: LearningDesign):
    design_id = str(test_design.id)
    deleted = await design_service.delete_design(test_db, design_id)
    assert deleted is True

    # Verify it's gone
    result = await design_service.get_design(test_db, design_id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_design_not_found(test_db: Session):
    deleted = await design_service.delete_design(
        test_db, "00000000-0000-0000-0000-000000000000"
    )
    assert deleted is False


@pytest.mark.asyncio
async def test_submit_for_review(test_db: Session, test_design: LearningDesign):
    result = await design_service.submit_for_review(test_db, str(test_design.id))

    assert result is not None
    assert result.status == DesignStatus.UNDER_REVIEW.value
    assert result.approval_history is not None
    records = result.approval_history.get("records", [])
    assert len(records) == 1
    assert records[0]["action"] == "submitted_for_review"


@pytest.mark.asyncio
async def test_submit_for_review_empty_content(test_db: Session, test_unit: Unit):
    # Create learning design with empty content
    data = DesignCreate(unit_id=str(test_unit.id), content={})
    design = await design_service.create_design(test_db, data)

    with pytest.raises(ValueError, match="empty content"):
        await design_service.submit_for_review(test_db, str(design.id))


@pytest.mark.asyncio
async def test_clone_design(test_db: Session, test_design: LearningDesign):
    clone = await design_service.clone_design(test_db, str(test_design.id))

    assert clone is not None
    assert str(clone.id) != str(test_design.id)
    assert clone.version == "1.1"  # Incremented from 1.0
    assert clone.status == DesignStatus.DRAFT.value
    assert clone.content == test_design.content


@pytest.mark.asyncio
async def test_clone_design_not_found(test_db: Session):
    result = await design_service.clone_design(
        test_db, "00000000-0000-0000-0000-000000000000"
    )
    assert result is None


@pytest.mark.asyncio
async def test_generate_tasks(test_db: Session, test_design: LearningDesign):
    task_list = await design_service.generate_tasks(test_db, str(test_design.id))

    assert task_list is not None
    assert str(task_list.design_id) == str(test_design.id)
    assert str(task_list.unit_id) == str(test_design.unit_id)
    assert task_list.total_tasks > 0
    assert task_list.completed_tasks == 0

    # Should have tasks from objectives and modules
    items = task_list.tasks.get("items", [])
    assert len(items) > 0
    # 3 objectives + 2 modules = 5 tasks
    assert len(items) == 5


@pytest.mark.asyncio
async def test_generate_tasks_not_found(test_db: Session):
    result = await design_service.generate_tasks(
        test_db, "00000000-0000-0000-0000-000000000000"
    )
    assert result is None
