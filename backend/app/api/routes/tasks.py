"""
Task management API endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.models import TaskList, User
from app.models.task_list import TaskStatus
from app.schemas.task import (
    TaskListCreate,
    TaskListResponse,
    TaskListUpdate,
    TaskUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[TaskListResponse])
async def get_task_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    course_id: UUID | None = None,
    lrd_id: UUID | None = None,
    status: TaskStatus | None = None,
) -> list[TaskListResponse]:
    """Get all task lists for the current user with optional filters"""
    query = db.query(TaskList)

    # Filter by course
    if course_id:
        query = query.filter(TaskList.course_id == course_id)

    # Filter by LRD
    if lrd_id:
        query = query.filter(TaskList.lrd_id == lrd_id)

    # Filter by status
    if status:
        query = query.filter(TaskList.status == status.value)

    task_lists = query.all()

    return [
        TaskListResponse.model_validate(task_list)
        for task_list in task_lists
    ]


@router.get("/{task_list_id}", response_model=TaskListResponse)
async def get_task_list(
    task_list_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> TaskListResponse:
    """Get a specific task list by ID"""
    task_list = db.query(TaskList).filter(TaskList.id == task_list_id).first()

    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task list not found"
        )

    return TaskListResponse.model_validate(task_list)


@router.post("/", response_model=TaskListResponse, status_code=status.HTTP_201_CREATED)
async def create_task_list(
    task_list_data: TaskListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> TaskListResponse:
    """Create a new task list"""
    task_list = TaskList(
        course_id=task_list_data.course_id,
        lrd_id=task_list_data.lrd_id,
        tasks=task_list_data.tasks,
        status=TaskStatus.PENDING.value,
        total_tasks=len(task_list_data.tasks),
        completed_tasks=0,
        progress={},
    )

    db.add(task_list)
    db.commit()
    db.refresh(task_list)

    return TaskListResponse.model_validate(task_list)


@router.put("/{task_list_id}", response_model=TaskListResponse)
async def update_task_list(
    task_list_id: UUID,
    update_data: TaskListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> TaskListResponse:
    """Update a task list"""
    task_list = db.query(TaskList).filter(TaskList.id == task_list_id).first()

    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task list not found"
        )

    # Update fields
    if update_data.status is not None:
        task_list.status = update_data.status

    if update_data.tasks is not None:
        task_list.tasks = update_data.tasks
        task_list.total_tasks = len(update_data.tasks)
        # Recalculate completed tasks
        completed = sum(1 for task in update_data.tasks if task.get("status") == "complete")
        task_list.completed_tasks = completed

    if update_data.progress is not None:
        task_list.progress = update_data.progress

    db.commit()
    db.refresh(task_list)

    return TaskListResponse.model_validate(task_list)


@router.patch("/{task_list_id}/tasks/{task_index}", response_model=TaskListResponse)
async def update_task(
    task_list_id: UUID,
    task_index: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> TaskListResponse:
    """Update a specific task within a task list"""
    task_list = db.query(TaskList).filter(TaskList.id == task_list_id).first()

    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task list not found"
        )

    # Ensure tasks is a list (cast to list for type checker)
    tasks = list(task_list.tasks) if task_list.tasks else []

    if task_index < 0 or task_index >= len(tasks):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task index"
        )

    # Update the specific task
    if task_update.status is not None:
        tasks[task_index]["status"] = task_update.status

    if task_update.title is not None:
        tasks[task_index]["title"] = task_update.title

    if task_update.description is not None:
        tasks[task_index]["description"] = task_update.description

    if task_update.assignee is not None:
        tasks[task_index]["assignee"] = task_update.assignee

    if task_update.priority is not None:
        tasks[task_index]["priority"] = task_update.priority

    if task_update.due_date is not None:
        tasks[task_index]["due_date"] = task_update.due_date.isoformat() if task_update.due_date else None

    if task_update.metadata is not None:
        tasks[task_index]["metadata"] = task_update.metadata

    # Update task list
    task_list.tasks = tasks

    # Recalculate completed tasks
    completed = sum(1 for task in tasks if task.get("status") == "complete")
    task_list.completed_tasks = completed

    # Update overall status if all tasks are complete
    if completed == task_list.total_tasks and task_list.total_tasks > 0:
        task_list.status = TaskStatus.COMPLETE.value
    elif completed > 0:
        task_list.status = TaskStatus.IN_PROGRESS.value

    db.commit()
    db.refresh(task_list)

    return TaskListResponse.model_validate(task_list)


@router.delete("/{task_list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_list(
    task_list_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete a task list"""
    task_list = db.query(TaskList).filter(TaskList.id == task_list_id).first()

    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task list not found"
        )

    db.delete(task_list)
    db.commit()
