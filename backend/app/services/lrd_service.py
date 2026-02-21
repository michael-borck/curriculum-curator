"""
Service for managing Learning Requirements Documents (LRDs)
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.lrd import LRD, LRDStatus
from app.models.task_list import TaskList
from app.schemas.lrd import LRDCreate, LRDUpdate

logger = logging.getLogger(__name__)


class LRDService:
    """Service for managing LRDs"""

    async def create_lrd(
        self,
        db: Session,
        lrd_data: LRDCreate,
    ) -> LRD:
        """Create a new LRD"""
        try:
            lrd = LRD(
                unit_id=lrd_data.unit_id,
                content=lrd_data.content,
                version=lrd_data.version,
                status=LRDStatus.DRAFT.value,
            )
            db.add(lrd)
            db.commit()
            db.refresh(lrd)
            logger.info(f"Created LRD {lrd.id} for unit {lrd_data.unit_id}")
            return lrd
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to create LRD")
            raise ValueError("Failed to create LRD — unit may not exist") from e

    async def get_lrd(
        self,
        db: Session,
        lrd_id: str,
    ) -> LRD | None:
        """Get a single LRD by ID"""
        return db.query(LRD).filter(LRD.id == lrd_id).first()

    async def list_by_unit(
        self,
        db: Session,
        unit_id: str,
    ) -> list[LRD]:
        """Get all LRDs for a unit"""
        return (
            db.query(LRD)
            .filter(LRD.unit_id == unit_id)
            .order_by(LRD.updated_at.desc())
            .all()
        )

    async def update_lrd(
        self,
        db: Session,
        lrd_id: str,
        lrd_data: LRDUpdate,
    ) -> LRD | None:
        """Update an existing LRD"""
        lrd = db.query(LRD).filter(LRD.id == lrd_id).first()
        if not lrd:
            return None

        update_data = lrd_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lrd, field, value)

        try:
            db.commit()
            db.refresh(lrd)
            logger.info(f"Updated LRD {lrd_id}")
            return lrd
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to update LRD")
            raise ValueError("Update would violate constraints") from e

    async def delete_lrd(
        self,
        db: Session,
        lrd_id: str,
    ) -> bool:
        """Delete an LRD"""
        lrd = db.query(LRD).filter(LRD.id == lrd_id).first()
        if not lrd:
            return False

        db.delete(lrd)
        db.commit()
        logger.info(f"Deleted LRD {lrd_id}")
        return True

    async def submit_for_review(
        self,
        db: Session,
        lrd_id: str,
    ) -> LRD | None:
        """Submit an LRD for review"""
        lrd = db.query(LRD).filter(LRD.id == lrd_id).first()
        if not lrd:
            return None

        if not lrd.content:
            raise ValueError("Cannot submit an LRD with empty content")

        lrd.status = LRDStatus.UNDER_REVIEW.value

        # Append to approval history
        history: list[dict[str, Any]] = []
        if lrd.approval_history and isinstance(lrd.approval_history, dict):
            existing = lrd.approval_history.get("records", [])
            if isinstance(existing, list):
                history = [item for item in existing if isinstance(item, dict)]

        history.append(
            {
                "action": "submitted_for_review",
                "timestamp": datetime.now(UTC).isoformat(),
                "from_status": "draft",
                "to_status": "under_review",
            }
        )
        lrd.approval_history = {"records": history}

        db.commit()
        db.refresh(lrd)
        logger.info(f"LRD {lrd_id} submitted for review")
        return lrd

    async def clone_lrd(
        self,
        db: Session,
        lrd_id: str,
    ) -> LRD | None:
        """Clone an LRD with incremented version"""
        original = db.query(LRD).filter(LRD.id == lrd_id).first()
        if not original:
            return None

        # Increment version
        try:
            major, minor = original.version.split(".")
            new_version = f"{major}.{int(minor) + 1}"
        except (ValueError, AttributeError):
            new_version = f"{original.version}.1"

        clone = LRD(
            unit_id=original.unit_id,
            content=dict(original.content) if original.content else {},
            version=new_version,
            status=LRDStatus.DRAFT.value,
        )
        db.add(clone)
        db.commit()
        db.refresh(clone)
        logger.info(f"Cloned LRD {lrd_id} → {clone.id} (v{new_version})")
        return clone

    async def generate_tasks(
        self,
        db: Session,
        lrd_id: str,
    ) -> TaskList | None:
        """Generate a TaskList from LRD content"""
        lrd = db.query(LRD).filter(LRD.id == lrd_id).first()
        if not lrd:
            return None

        # Extract tasks from LRD content
        tasks = self._extract_tasks_from_content(lrd.content)

        task_list = TaskList(
            lrd_id=lrd.id,
            unit_id=lrd.unit_id,
            tasks={"items": tasks},
            total_tasks=len(tasks),
            completed_tasks=0,
        )
        db.add(task_list)
        db.commit()
        db.refresh(task_list)
        logger.info(f"Generated {len(tasks)} tasks from LRD {lrd_id}")
        return task_list

    def _extract_tasks_from_content(
        self, content: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract actionable tasks from LRD content JSON"""
        tasks: list[dict[str, Any]] = []
        idx = 0

        # Extract from objectives
        objectives = content.get("objectives", [])
        if isinstance(objectives, list):
            for obj in objectives:
                if isinstance(obj, str) and obj.strip():
                    tasks.append(
                        {
                            "index": idx,
                            "title": f"Implement: {obj}",
                            "status": "pending",
                            "source": "objective",
                        }
                    )
                    idx += 1

        # Extract from modules
        modules = content.get("modules", [])
        if isinstance(modules, list):
            for mod in modules:
                if isinstance(mod, dict):
                    title = mod.get("title") or mod.get("name", "Untitled module")
                    tasks.append(
                        {
                            "index": idx,
                            "title": f"Develop module: {title}",
                            "status": "pending",
                            "source": "module",
                        }
                    )
                    idx += 1

        # If no structured tasks found, create a generic one
        if not tasks:
            tasks.append(
                {
                    "index": 0,
                    "title": "Review and implement LRD requirements",
                    "status": "pending",
                    "source": "general",
                }
            )

        return tasks


# Create singleton instance
lrd_service = LRDService()
