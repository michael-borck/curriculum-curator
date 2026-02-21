"""
Service for managing Learning Designs
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.learning_design import DesignStatus, LearningDesign
from app.models.task_list import TaskList
from app.schemas.learning_design import DesignCreate, DesignUpdate

logger = logging.getLogger(__name__)


class DesignService:
    """Service for managing Learning Designs"""

    async def create_design(
        self,
        db: Session,
        design_data: DesignCreate,
    ) -> LearningDesign:
        """Create a new learning design"""
        try:
            design = LearningDesign(
                unit_id=design_data.unit_id,
                content=design_data.content,
                version=design_data.version,
                status=DesignStatus.DRAFT.value,
            )
            db.add(design)
            db.commit()
            db.refresh(design)
            logger.info(
                f"Created learning design {design.id} for unit {design_data.unit_id}"
            )
            return design
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to create learning design")
            raise ValueError(
                "Failed to create learning design — unit may not exist"
            ) from e

    async def get_design(
        self,
        db: Session,
        design_id: str,
    ) -> LearningDesign | None:
        """Get a single learning design by ID"""
        return db.query(LearningDesign).filter(LearningDesign.id == design_id).first()

    async def list_by_unit(
        self,
        db: Session,
        unit_id: str,
    ) -> list[LearningDesign]:
        """Get all learning designs for a unit"""
        return (
            db.query(LearningDesign)
            .filter(LearningDesign.unit_id == unit_id)
            .order_by(LearningDesign.updated_at.desc())
            .all()
        )

    async def update_design(
        self,
        db: Session,
        design_id: str,
        design_data: DesignUpdate,
    ) -> LearningDesign | None:
        """Update an existing learning design"""
        design = db.query(LearningDesign).filter(LearningDesign.id == design_id).first()
        if not design:
            return None

        update_data = design_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(design, field, value)

        try:
            db.commit()
            db.refresh(design)
            logger.info(f"Updated learning design {design_id}")
            return design
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to update learning design")
            raise ValueError("Update would violate constraints") from e

    async def delete_design(
        self,
        db: Session,
        design_id: str,
    ) -> bool:
        """Delete a learning design"""
        design = db.query(LearningDesign).filter(LearningDesign.id == design_id).first()
        if not design:
            return False

        db.delete(design)
        db.commit()
        logger.info(f"Deleted learning design {design_id}")
        return True

    async def submit_for_review(
        self,
        db: Session,
        design_id: str,
    ) -> LearningDesign | None:
        """Submit a learning design for review"""
        design = db.query(LearningDesign).filter(LearningDesign.id == design_id).first()
        if not design:
            return None

        if not design.content:
            raise ValueError("Cannot submit a learning design with empty content")

        design.status = DesignStatus.UNDER_REVIEW.value

        # Append to approval history
        history: list[dict[str, Any]] = []
        if design.approval_history and isinstance(design.approval_history, dict):
            existing = design.approval_history.get("records", [])
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
        design.approval_history = {"records": history}

        db.commit()
        db.refresh(design)
        logger.info(f"Learning design {design_id} submitted for review")
        return design

    async def clone_design(
        self,
        db: Session,
        design_id: str,
    ) -> LearningDesign | None:
        """Clone a learning design with incremented version"""
        original = (
            db.query(LearningDesign).filter(LearningDesign.id == design_id).first()
        )
        if not original:
            return None

        # Increment version
        try:
            major, minor = original.version.split(".")
            new_version = f"{major}.{int(minor) + 1}"
        except (ValueError, AttributeError):
            new_version = f"{original.version}.1"

        clone = LearningDesign(
            unit_id=original.unit_id,
            content=dict(original.content) if original.content else {},
            version=new_version,
            status=DesignStatus.DRAFT.value,
        )
        db.add(clone)
        db.commit()
        db.refresh(clone)
        logger.info(f"Cloned learning design {design_id} → {clone.id} (v{new_version})")
        return clone

    async def generate_tasks(
        self,
        db: Session,
        design_id: str,
    ) -> TaskList | None:
        """Generate a TaskList from learning design content"""
        design = db.query(LearningDesign).filter(LearningDesign.id == design_id).first()
        if not design:
            return None

        # Extract tasks from learning design content
        tasks = self._extract_tasks_from_content(design.content)

        task_list = TaskList(
            design_id=design.id,
            unit_id=design.unit_id,
            tasks={"items": tasks},
            total_tasks=len(tasks),
            completed_tasks=0,
        )
        db.add(task_list)
        db.commit()
        db.refresh(task_list)
        logger.info(f"Generated {len(tasks)} tasks from learning design {design_id}")
        return task_list

    def _extract_tasks_from_content(
        self, content: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract actionable tasks from learning design content JSON"""
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
                    "title": "Review and implement learning design requirements",
                    "status": "pending",
                    "source": "general",
                }
            )

        return tasks


# Create singleton instance
design_service = DesignService()
