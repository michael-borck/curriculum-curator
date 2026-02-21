"""
Tests for LRD service — uses real in-memory SQLite (no mocks).
"""

import pytest
from sqlalchemy.orm import Session

from app.models.lrd import LRD, LRDStatus
from app.models.unit import Unit
from app.schemas.lrd import LRDCreate, LRDUpdate
from app.services.lrd_service import lrd_service


@pytest.mark.asyncio
async def test_create_lrd(test_db: Session, test_unit: Unit):
    data = LRDCreate(
        unit_id=str(test_unit.id),
        content={"topic": "Test Topic", "objectives": ["Learn testing"]},
        version="1.0",
    )
    lrd = await lrd_service.create_lrd(test_db, data)

    assert lrd.id is not None
    assert str(lrd.unit_id) == str(test_unit.id)
    assert lrd.status == LRDStatus.DRAFT.value
    assert lrd.content["topic"] == "Test Topic"


@pytest.mark.asyncio
async def test_get_lrd(test_db: Session, test_lrd: LRD):
    result = await lrd_service.get_lrd(test_db, str(test_lrd.id))
    assert result is not None
    assert str(result.id) == str(test_lrd.id)


@pytest.mark.asyncio
async def test_get_lrd_not_found(test_db: Session):
    result = await lrd_service.get_lrd(test_db, "00000000-0000-0000-0000-000000000000")
    assert result is None


@pytest.mark.asyncio
async def test_list_by_unit(test_db: Session, test_lrd: LRD, test_unit: Unit):
    results = await lrd_service.list_by_unit(test_db, str(test_unit.id))
    assert len(results) >= 1
    assert any(str(r.id) == str(test_lrd.id) for r in results)


@pytest.mark.asyncio
async def test_update_lrd(test_db: Session, test_lrd: LRD):
    update_data = LRDUpdate(content={"topic": "Updated Topic"}, version="1.1")
    updated = await lrd_service.update_lrd(test_db, str(test_lrd.id), update_data)

    assert updated is not None
    assert updated.content["topic"] == "Updated Topic"
    assert updated.version == "1.1"


@pytest.mark.asyncio
async def test_update_lrd_not_found(test_db: Session):
    update_data = LRDUpdate(content={"topic": "Updated"})
    result = await lrd_service.update_lrd(test_db, "00000000-0000-0000-0000-000000000000", update_data)
    assert result is None


@pytest.mark.asyncio
async def test_delete_lrd(test_db: Session, test_lrd: LRD):
    lrd_id = str(test_lrd.id)
    deleted = await lrd_service.delete_lrd(test_db, lrd_id)
    assert deleted is True

    # Verify it's gone
    result = await lrd_service.get_lrd(test_db, lrd_id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_lrd_not_found(test_db: Session):
    deleted = await lrd_service.delete_lrd(test_db, "00000000-0000-0000-0000-000000000000")
    assert deleted is False


@pytest.mark.asyncio
async def test_submit_for_review(test_db: Session, test_lrd: LRD):
    result = await lrd_service.submit_for_review(test_db, str(test_lrd.id))

    assert result is not None
    assert result.status == LRDStatus.UNDER_REVIEW.value
    assert result.approval_history is not None
    records = result.approval_history.get("records", [])
    assert len(records) == 1
    assert records[0]["action"] == "submitted_for_review"


@pytest.mark.asyncio
async def test_submit_for_review_empty_content(test_db: Session, test_unit: Unit):
    # Create LRD with empty content
    data = LRDCreate(unit_id=str(test_unit.id), content={})
    lrd = await lrd_service.create_lrd(test_db, data)

    with pytest.raises(ValueError, match="empty content"):
        await lrd_service.submit_for_review(test_db, str(lrd.id))


@pytest.mark.asyncio
async def test_clone_lrd(test_db: Session, test_lrd: LRD):
    clone = await lrd_service.clone_lrd(test_db, str(test_lrd.id))

    assert clone is not None
    assert str(clone.id) != str(test_lrd.id)
    assert clone.version == "1.1"  # Incremented from 1.0
    assert clone.status == LRDStatus.DRAFT.value
    assert clone.content == test_lrd.content


@pytest.mark.asyncio
async def test_clone_lrd_not_found(test_db: Session):
    result = await lrd_service.clone_lrd(test_db, "00000000-0000-0000-0000-000000000000")
    assert result is None


@pytest.mark.asyncio
async def test_generate_tasks(test_db: Session, test_lrd: LRD):
    task_list = await lrd_service.generate_tasks(test_db, str(test_lrd.id))

    assert task_list is not None
    assert str(task_list.lrd_id) == str(test_lrd.id)
    assert str(task_list.unit_id) == str(test_lrd.unit_id)
    assert task_list.total_tasks > 0
    assert task_list.completed_tasks == 0

    # Should have tasks from objectives and modules
    items = task_list.tasks.get("items", [])
    assert len(items) > 0
    # 3 objectives + 2 modules = 5 tasks
    assert len(items) == 5


@pytest.mark.asyncio
async def test_generate_tasks_not_found(test_db: Session):
    result = await lrd_service.generate_tasks(test_db, "00000000-0000-0000-0000-000000000000")
    assert result is None
