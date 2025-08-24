"""
Service for managing Assessments
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import Assessment, AssessmentType
from app.models.learning_outcomes import AssessmentLearningOutcome
from app.models.mappings import assessment_material_links, assessment_ulo_mappings
from app.schemas.assessments import (
    AssessmentCreate,
    AssessmentFilter,
    AssessmentMapping,
    AssessmentMaterialLink,
    AssessmentUpdate,
    GradeDistribution,
)
from app.schemas.learning_outcomes import ALOCreate

logger = logging.getLogger(__name__)


class AssessmentsService:
    """Service for managing Assessments"""

    async def create_assessment(
        self,
        db: Session,
        unit_id: UUID,
        assessment_data: AssessmentCreate,
    ) -> Assessment:
        """Create a new Assessment"""
        try:
            assessment_dict = assessment_data.model_dump(exclude={"rubric"})

            # Convert rubric to dict if present
            if assessment_data.rubric:
                assessment_dict["rubric"] = assessment_data.rubric.model_dump()

            assessment = Assessment(
                unit_id=unit_id,
                **assessment_dict
            )

            db.add(assessment)
            db.commit()
            db.refresh(assessment)

            logger.info(f"Created assessment '{assessment.title}' for unit {unit_id}")
            return assessment

        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to create assessment")
            raise ValueError("Failed to create assessment") from e

    async def update_assessment(
        self,
        db: Session,
        assessment_id: UUID,
        assessment_data: AssessmentUpdate,
    ) -> Assessment | None:
        """Update an existing Assessment"""
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()

        if not assessment:
            return None

        update_data = assessment_data.model_dump(exclude_unset=True, exclude={"rubric"})

        # Handle rubric separately
        if assessment_data.rubric is not None:
            update_data["rubric"] = assessment_data.rubric.model_dump()

        for field, value in update_data.items():
            setattr(assessment, field, value)

        try:
            db.commit()
            db.refresh(assessment)
            logger.info(f"Updated assessment {assessment_id}")
            return assessment
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to update assessment")
            raise ValueError("Update would violate constraints") from e

    async def delete_assessment(
        self,
        db: Session,
        assessment_id: UUID,
    ) -> bool:
        """Delete an Assessment"""
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()

        if not assessment:
            return False

        db.delete(assessment)
        db.commit()
        logger.info(f"Deleted assessment {assessment_id}")
        return True

    async def get_assessment(
        self,
        db: Session,
        assessment_id: UUID,
        include_outcomes: bool = False,
    ) -> Assessment | None:
        """Get a single Assessment"""
        query = db.query(Assessment).filter(
            Assessment.id == assessment_id
        )

        if include_outcomes:
            query = query.options(
                selectinload(Assessment.assessment_outcomes),
                selectinload(Assessment.learning_outcomes),
                selectinload(Assessment.linked_materials),
            )

        return query.first()

    async def get_assessments_by_unit(
        self,
        db: Session,
        unit_id: UUID,
        filter_params: AssessmentFilter | None = None,
    ) -> list[Assessment]:
        """Get all assessments for a unit with optional filtering"""
        query = db.query(Assessment).filter(
            Assessment.unit_id == unit_id
        )

        if filter_params:
            if filter_params.type:
                query = query.filter(Assessment.type == filter_params.type)
            if filter_params.category:
                query = query.filter(Assessment.category == filter_params.category)
            if filter_params.status:
                query = query.filter(Assessment.status == filter_params.status)
            if filter_params.release_week is not None:
                query = query.filter(Assessment.release_week == filter_params.release_week)
            if filter_params.due_week is not None:
                query = query.filter(Assessment.due_week == filter_params.due_week)
            if filter_params.search:
                search_term = f"%{filter_params.search}%"
                query = query.filter(
                    (Assessment.title.ilike(search_term)) |
                    (Assessment.description.ilike(search_term))
                )

        return query.order_by(
            Assessment.due_week,
            Assessment.weight.desc()
        ).all()

    async def calculate_grade_distribution(
        self,
        db: Session,
        unit_id: UUID,
    ) -> GradeDistribution:
        """Calculate grade distribution for a unit"""
        assessments = await self.get_assessments_by_unit(db, unit_id)

        total_weight = sum(a.weight for a in assessments)
        formative_weight = sum(
            a.weight for a in assessments
            if a.type == AssessmentType.FORMATIVE
        )
        summative_weight = sum(
            a.weight for a in assessments
            if a.type == AssessmentType.SUMMATIVE
        )

        # Group by category
        by_category = {}
        by_type = {"formative": 0, "summative": 0}

        for assessment in assessments:
            # Sum weights by category
            by_category[assessment.category] = (
                by_category.get(assessment.category, 0) + assessment.weight
            )
            # Count by type
            by_type[assessment.type] = by_type.get(assessment.type, 0) + 1

        return GradeDistribution(
            total_weight=total_weight,
            formative_weight=formative_weight,
            summative_weight=summative_weight,
            is_valid=abs(total_weight - 100.0) < 0.01,  # Allow small floating point errors
            assessments_by_category=by_category,
            assessments_by_type=by_type,
        )

    async def validate_weights(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Validate assessment weights for a unit"""
        distribution = await self.calculate_grade_distribution(db, unit_id)

        errors = []
        warnings = []

        if distribution.total_weight < 100:
            errors.append(f"Total weight is {distribution.total_weight}%, should be 100%")
        elif distribution.total_weight > 100:
            errors.append(f"Total weight is {distribution.total_weight}%, exceeds 100%")

        if distribution.formative_weight > 40:
            warnings.append("Formative assessments exceed 40% of total grade")

        if distribution.summative_weight < 50:
            warnings.append("Summative assessments are less than 50% of total grade")

        # Check for assessment variety
        if len(distribution.assessments_by_category) < 3:
            warnings.append("Consider using more varied assessment types")

        return {
            "is_valid": len(errors) == 0,
            "total_weight": distribution.total_weight,
            "errors": errors,
            "warnings": warnings,
            "distribution": distribution.model_dump(),
        }

    async def update_ulo_mappings(
        self,
        db: Session,
        assessment_id: UUID,
        mapping_data: AssessmentMapping,
    ) -> Assessment:
        """Update ULO mappings for an assessment"""
        assessment = await self.get_assessment(db, assessment_id)

        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Clear existing mappings
        db.execute(
            assessment_ulo_mappings.delete().where(
                assessment_ulo_mappings.c.assessment_id == assessment_id
            )
        )

        # Add new mappings
        for ulo_id in mapping_data.ulo_ids:
            db.execute(
                assessment_ulo_mappings.insert().values(
                    assessment_id=assessment_id,
                    ulo_id=ulo_id,
                )
            )

        db.commit()
        logger.info(f"Updated ULO mappings for assessment {assessment_id}")

        return await self.get_assessment(db, assessment_id, include_outcomes=True)

    async def update_material_links(
        self,
        db: Session,
        assessment_id: UUID,
        link_data: AssessmentMaterialLink,
    ) -> Assessment:
        """Update material links for an assessment"""
        assessment = await self.get_assessment(db, assessment_id)

        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Clear existing links
        db.execute(
            assessment_material_links.delete().where(
                assessment_material_links.c.assessment_id == assessment_id
            )
        )

        # Add new links
        for material_id in link_data.material_ids:
            db.execute(
                assessment_material_links.insert().values(
                    assessment_id=assessment_id,
                    material_id=material_id,
                )
            )

        db.commit()
        logger.info(f"Updated material links for assessment {assessment_id}")

        return await self.get_assessment(db, assessment_id, include_outcomes=True)

    async def add_assessment_outcome(
        self,
        db: Session,
        assessment_id: UUID,
        outcome_data: ALOCreate,
    ) -> AssessmentLearningOutcome:
        """Add an assessment-specific learning outcome"""
        assessment = await self.get_assessment(db, assessment_id)

        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Get the next order index
        max_order = (
            db.query(func.max(AssessmentLearningOutcome.order_index))
            .filter(AssessmentLearningOutcome.assessment_id == assessment_id)
            .scalar()
        )
        next_order = (max_order or -1) + 1

        alo = AssessmentLearningOutcome(
            assessment_id=assessment_id,
            description=outcome_data.description,
            order_index=outcome_data.order_index or next_order,
        )

        db.add(alo)
        db.commit()
        db.refresh(alo)

        logger.info(f"Added outcome to assessment {assessment_id}")
        return alo

    async def get_assessment_timeline(
        self,
        db: Session,
        unit_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get assessment timeline for a unit"""
        assessments = await self.get_assessments_by_unit(db, unit_id)

        # Group by week
        timeline = {}

        for assessment in assessments:
            if assessment.due_week:
                week = assessment.due_week
                if week not in timeline:
                    timeline[week] = {
                        "week_number": week,
                        "assessments": [],
                        "total_weight": 0,
                    }

                timeline[week]["assessments"].append({
                    "id": str(assessment.id),
                    "title": assessment.title,
                    "type": assessment.type,
                    "category": assessment.category,
                    "weight": assessment.weight,
                    "due_date": assessment.due_date.isoformat() if assessment.due_date else None,
                })
                timeline[week]["total_weight"] += assessment.weight

        # Convert to sorted list
        return sorted(timeline.values(), key=lambda x: x["week_number"])

    async def get_assessment_workload(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Analyze assessment workload distribution"""
        timeline = await self.get_assessment_timeline(db, unit_id)

        # Find weeks with heavy workload
        heavy_weeks = []
        light_weeks = []

        for week_data in timeline:
            if week_data["total_weight"] > 20:
                heavy_weeks.append(week_data["week_number"])
            elif week_data["total_weight"] < 5 and week_data["total_weight"] > 0:
                light_weeks.append(week_data["week_number"])

        # Calculate statistics
        weights_by_week = [w["total_weight"] for w in timeline]
        avg_weight = sum(weights_by_week) / len(weights_by_week) if weights_by_week else 0
        max_weight = max(weights_by_week) if weights_by_week else 0

        return {
            "timeline": timeline,
            "heavy_weeks": heavy_weeks,
            "light_weeks": light_weeks,
            "average_weight_per_week": round(avg_weight, 2),
            "max_weight_in_week": max_weight,
            "recommendations": self._generate_workload_recommendations(
                heavy_weeks, light_weeks, max_weight
            ),
        }

    def _generate_workload_recommendations(
        self,
        heavy_weeks: list[int],
        light_weeks: list[int],
        max_weight: float,
    ) -> list[str]:
        """Generate recommendations for assessment workload"""
        recommendations = []

        if max_weight > 30:
            recommendations.append(
                f"Consider redistributing assessments - week has {max_weight}% of grade"
            )

        if len(heavy_weeks) > 2:
            recommendations.append(
                f"Multiple weeks have heavy assessment loads: {heavy_weeks}"
            )

        if len(heavy_weeks) > 0 and len(light_weeks) > 0:
            recommendations.append(
                f"Consider moving some assessments from weeks {heavy_weeks} to weeks {light_weeks}"
            )

        return recommendations


# Create singleton instance
assessments_service = AssessmentsService()
