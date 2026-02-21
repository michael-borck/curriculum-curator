"""
Tests for TaskList service — uses real in-memory SQLite (no mocks).
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.lrd import LRD
from app.models.task_list import TaskList
from app.models.unit import Unit
from app.services.task_list_service import task_list_service


def _create_task_list(
    db: Session,
    unit: Unit,
    lrd: LRD | None = None,
) -> TaskList:
    """Helper to create a TaskList in the test DB."""
    tl = TaskList(
        id=str(uuid.uuid4()),
        unit_id=unit.id,
        lrd_id=lrd.id if lrd else None,
        tasks={
            "items": [
                {"index": 0, "title": "Task A", "status": "pending"},
                {"index": 1, "title": "Task B", "status": "pending"},
                {"index": 2, "title": "Task C", "status": "complete"},
            ]
        },
        total_tasks=3,
        completed_tasks=1,
        status="pending",
    )
    db.add(tl)
    db.commit()
    db.refresh(tl)
    return tl


@pytest.mark.asyncio
async def test_get_task_lists_all(test_db: Session, test_unit: Unit):
    tl = _create_task_list(test_db, test_unit)

    results = await task_list_service.get_task_lists(test_db)
    assert len(results) >= 1
    assert any(str(r.id) == str(tl.id) for r in results)


@pytest.mark.asyncio
async def test_get_task_lists_by_unit(test_db: Session, test_unit: Unit):
    _create_task_list(test_db, test_unit)

    results = await task_list_service.get_task_lists(test_db, unit_id=str(test_unit.id))
    assert len(results) >= 1
    assert all(str(r.unit_id) == str(test_unit.id) for r in results)


@pytest.mark.asyncio
async def test_get_task_lists_by_lrd(test_db: Session, test_unit: Unit, test_lrd: LRD):
    _create_task_list(test_db, test_unit, lrd=test_lrd)

    results = await task_list_service.get_task_lists(
        test_db, lrd_id=str(test_lrd.id)
    )
    assert len(results) >= 1
    assert all(str(r.lrd_id) == str(test_lrd.id) for r in results)


@pytest.mark.asyncio
async def test_get_task_list(test_db: Session, test_unit: Unit):
    tl = _create_task_list(test_db, test_unit)

    result = await task_list_service.get_task_list(test_db, str(tl.id))
    assert result is not None
    assert str(result.id) == str(tl.id)
    assert result.total_tasks == 3
    assert result.completed_tasks == 1


@pytest.mark.asyncio
async def test_get_task_list_not_found(test_db: Session):
    result = await task_list_service.get_task_list(test_db, "00000000-0000-0000-0000-000000000000")
    assert result is None


@pytest.mark.asyncio
async def test_update_task_status(test_db: Session, test_unit: Unit):
    tl = _create_task_list(test_db, test_unit)

    # Mark Task A (index 0) as complete
    updated = await task_list_service.update_task_status(
        test_db, str(tl.id), task_index=0, new_status="complete"
    )

    assert updated is not None
    items = updated.tasks["items"]
    assert items[0]["status"] == "complete"
    # Now 2 complete (Task A + Task C)
    assert updated.completed_tasks == 2
    assert updated.total_tasks == 3


@pytest.mark.asyncio
async def test_update_task_status_not_found(test_db: Session):
    result = await task_list_service.update_task_status(
        test_db, "00000000-0000-0000-0000-000000000000", task_index=0, new_status="complete"
    )
    assert result is None


@pytest.mark.asyncio
async def test_update_task_status_invalid_index(test_db: Session, test_unit: Unit):
    tl = _create_task_list(test_db, test_unit)

    with pytest.raises(ValueError, match="out of range"):
        await task_list_service.update_task_status(
            test_db, str(tl.id), task_index=99, new_status="complete"
        )


@pytest.mark.asyncio
async def test_progress_percentage(test_db: Session, test_unit: Unit):
    tl = _create_task_list(test_db, test_unit)

    # 1 of 3 complete = 33.33%
    assert abs(tl.progress_percentage - 33.33) < 1.0

    # Complete another task
    updated = await task_list_service.update_task_status(
        test_db, str(tl.id), task_index=0, new_status="complete"
    )
    assert updated is not None
    # 2 of 3 complete = 66.67%
    assert abs(updated.progress_percentage - 66.67) < 1.0
