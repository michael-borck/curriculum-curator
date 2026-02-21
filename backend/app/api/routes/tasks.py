"""
API endpoints for managing TaskLists
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.task_list import TaskList
from app.schemas.task_list import TaskListResponse, TaskStatusUpdate
from app.schemas.user import UserResponse
from app.services.task_list_service import task_list_service

router = APIRouter()


def _task_list_to_response(tl: TaskList) -> TaskListResponse:
    """Convert a TaskList model to a response schema"""
    return TaskListResponse(
        id=str(tl.id),
        lrd_id=str(tl.lrd_id) if tl.lrd_id else None,
        unit_id=str(tl.unit_id),
        tasks=tl.tasks,
        status=tl.status,
        total_tasks=tl.total_tasks,
        completed_tasks=tl.completed_tasks,
        progress=tl.progress,
        progress_percentage=tl.progress_percentage,
        created_at=tl.created_at,
        updated_at=tl.updated_at,
        completed_at=tl.completed_at,
    )


@router.get("/tasks", response_model=list[TaskListResponse])
async def list_task_lists(
    unit_id: str | None = Query(None, alias="unitId"),
    lrd_id: str | None = Query(None, alias="lrdId"),
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> list[TaskListResponse]:
    """List task lists with optional filtering"""
    task_lists = await task_list_service.get_task_lists(db, unit_id, lrd_id)
    return [_task_list_to_response(tl) for tl in task_lists]


@router.get("/tasks/{task_list_id}", response_model=TaskListResponse)
async def get_task_list(
    task_list_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> TaskListResponse:
    """Get a single TaskList"""
    tl = await task_list_service.get_task_list(db, task_list_id)
    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TaskList not found",
        )
    return _task_list_to_response(tl)


@router.patch("/tasks/{task_list_id}", response_model=TaskListResponse)
async def update_task_status(
    task_list_id: str,
    update_data: TaskStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> TaskListResponse:
    """Update a task's status within a TaskList"""
    try:
        tl = await task_list_service.update_task_status(
            db, task_list_id, update_data.task_index, update_data.status
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TaskList not found",
        )
    return _task_list_to_response(tl)
