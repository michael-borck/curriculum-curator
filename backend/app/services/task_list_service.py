"""
Service for managing TaskLists
"""

import copy
import logging

from sqlalchemy.orm import Session

from app.models.task_list import TaskList

logger = logging.getLogger(__name__)


class TaskListService:
    """Service for managing TaskLists"""

    async def get_task_lists(
        self,
        db: Session,
        unit_id: str | None = None,
        design_id: str | None = None,
    ) -> list[TaskList]:
        """Get task lists with optional filtering"""
        query = db.query(TaskList)
        if unit_id:
            query = query.filter(TaskList.unit_id == unit_id)
        if design_id:
            query = query.filter(TaskList.design_id == design_id)
        return query.order_by(TaskList.created_at.desc()).all()

    async def get_task_list(
        self,
        db: Session,
        task_list_id: str,
    ) -> TaskList | None:
        """Get a single TaskList by ID"""
        return db.query(TaskList).filter(TaskList.id == task_list_id).first()

    async def update_task_status(
        self,
        db: Session,
        task_list_id: str,
        task_index: int,
        new_status: str,
    ) -> TaskList | None:
        """Update a single task's status within a TaskList"""
        task_list = db.query(TaskList).filter(TaskList.id == task_list_id).first()
        if not task_list:
            return None

        tasks = copy.deepcopy(task_list.tasks or {})
        items: list[dict[str, object]] = tasks.get("items", [])

        if task_index < 0 or task_index >= len(items):
            raise ValueError(f"Task index {task_index} out of range (0-{len(items) - 1})")

        items[task_index]["status"] = new_status

        # Recalculate counts
        completed = sum(1 for item in items if item.get("status") == "complete")

        # Assign new dict so SQLAlchemy detects the change
        task_list.tasks = {"items": items}
        task_list.total_tasks = len(items)
        task_list.completed_tasks = completed

        db.commit()
        db.refresh(task_list)
        logger.info(f"Updated task {task_index} in TaskList {task_list_id} to '{new_status}'")
        return task_list


# Create singleton instance
task_list_service = TaskListService()
