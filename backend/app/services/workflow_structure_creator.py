"""
Service for creating actual database records from workflow decisions
"""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.assessments import Assessment
from app.models.learning_outcomes import UnitLearningOutcome
from app.models.unit import Unit
from app.models.unit_outline import UnitOutline
from app.models.weekly_materials import WeeklyMaterial
from app.models.workflow import WorkflowChatSession


class WorkflowStructureCreator:
    """Creates actual database records from workflow structure"""

    def __init__(self, db: Session):
        self.db = db

    def create_unit_structure(
        self,
        session: WorkflowChatSession,
        unit: Unit,
        structure_data: dict[str, Any],
        use_ai: bool = True,
    ) -> dict[str, Any]:
        """
        Create actual database records for unit structure

        Returns:
            Dictionary with created IDs and counts
        """
        # Create unit outline if it doesn't exist
        outline = (
            self.db.query(UnitOutline).filter(UnitOutline.unit_id == unit.id).first()
        )

        if not outline:
            outline = UnitOutline(
                id=str(uuid.uuid4()),
                unit_id=unit.id,
                title=f"{unit.code} - {unit.title}",
                description=unit.description or "",
                duration_weeks=unit.duration_weeks,
                delivery_mode=session.decisions_made.get("delivery_mode", {}).get(
                    "value", "Blended"
                ),
                teaching_pattern=session.decisions_made.get("weekly_structure", {}).get(
                    "value", "Lecture + Tutorial"
                ),
                is_complete=False,
                completion_percentage=0,
            )
            self.db.add(outline)

        # Create learning outcomes
        ulo_count = 0
        for idx, lo_data in enumerate(structure_data.get("learning_outcomes", [])):
            if lo_data.get("description"):  # Only create if has content
                ulo = UnitLearningOutcome(
                    id=str(uuid.uuid4()),
                    unit_id=unit.id,
                    code=f"ULO{idx + 1}",
                    description=lo_data["description"],
                    bloom_level=lo_data.get("bloom_level", "understand"),
                    order_index=idx,
                )
                self.db.add(ulo)
                ulo_count += 1

        # Create weekly materials (just placeholders for each week)
        material_count = 0
        for week_data in structure_data.get("weekly_topics", []):
            week_num = week_data.get("week", 1)

            # Create a lecture material for each week if has topic
            if week_data.get("topic"):
                material = WeeklyMaterial(
                    id=str(uuid.uuid4()),
                    unit_id=unit.id,
                    week_number=week_num,
                    title=f"Week {week_num}: {week_data['topic']}",
                    type="lecture",
                    description=week_data.get("description", ""),
                    order_index=0,
                    status="draft",
                )
                self.db.add(material)
                material_count += 1

        # Create assessments
        assessment_count = 0
        for _idx, assess_data in enumerate(structure_data.get("assessments", [])):
            if assess_data.get("name"):  # Only create if has content
                assessment = Assessment(
                    id=str(uuid.uuid4()),
                    unit_id=unit.id,
                    title=assess_data["name"],
                    type=assess_data.get("type", "summative"),
                    category="assignment",  # Default, can be refined
                    weight=float(assess_data.get("weight", 0))
                    if assess_data.get("weight")
                    else 0,
                    due_week=int(assess_data.get("due_week", 1))
                    if assess_data.get("due_week")
                    else None,
                    status="draft",
                )
                self.db.add(assessment)
                assessment_count += 1

        # Commit all changes
        self.db.commit()

        # Update outline completion percentage
        if ulo_count > 0 or material_count > 0 or assessment_count > 0:
            outline.completion_percentage = min(
                100, (ulo_count * 10) + (material_count * 2) + (assessment_count * 10)
            )
            self.db.commit()

        return {
            "outlineId": str(outline.id),
            "components": {
                "learningOutcomes": ulo_count,
                "weeklyTopics": material_count,
                "assessments": assessment_count,
            },
        }
