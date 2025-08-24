"""
Service for managing Unit Learning Outcomes (ULOs)
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.learning_outcome import OutcomeType, UnitLearningOutcome
from app.models.mappings import assessment_ulo_mappings, material_ulo_mappings
from app.schemas.learning_outcomes import (
    BulkULOCreate,
    OutcomeReorder,
    ULOCreate,
    ULOUpdate,
)

logger = logging.getLogger(__name__)


class ULOService:
    """Service for managing Unit Learning Outcomes"""

    async def create_ulo(
        self,
        db: Session,
        unit_id: UUID,
        ulo_data: ULOCreate,
        user_id: UUID,
    ) -> UnitLearningOutcome:
        """Create a new Unit Learning Outcome"""
        try:
            # Get the next order index
            max_order = (
                db.query(func.max(UnitLearningOutcome.sequence_order))
                .filter(
                    and_(
                        UnitLearningOutcome.unit_id == unit_id,
                        UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    )
                )
                .scalar()
            )
            next_order = (max_order or -1) + 1

            ulo = UnitLearningOutcome(
                unit_id=unit_id,
                outcome_type=OutcomeType.ULO,
                outcome_code=ulo_data.code,
                outcome_text=ulo_data.description,
                bloom_level=ulo_data.bloom_level,
                sequence_order=ulo_data.order_index or next_order,
                created_by_id=user_id,
                is_active=True,
                is_measurable=True,
            )

            db.add(ulo)
            db.commit()
            db.refresh(ulo)

            logger.info(f"Created ULO {ulo.outcome_code} for unit {unit_id}")
            return ulo

        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to create ULO")
            raise ValueError(f"ULO with code {ulo_data.code} already exists") from e

    async def update_ulo(
        self,
        db: Session,
        ulo_id: UUID,
        ulo_data: ULOUpdate,
    ) -> UnitLearningOutcome | None:
        """Update an existing Unit Learning Outcome"""
        ulo = (
            db.query(UnitLearningOutcome)
            .filter(
                and_(
                    UnitLearningOutcome.id == ulo_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                )
            )
            .first()
        )

        if not ulo:
            return None

        update_data = ulo_data.model_dump(exclude_unset=True)

        # Map field names
        if "code" in update_data:
            ulo.outcome_code = update_data.pop("code")
        if "description" in update_data:
            ulo.outcome_text = update_data.pop("description")
        if "order_index" in update_data:
            ulo.sequence_order = update_data.pop("order_index")

        # Apply remaining updates
        for field, value in update_data.items():
            setattr(ulo, field, value)

        try:
            db.commit()
            db.refresh(ulo)
            logger.info(f"Updated ULO {ulo_id}")
            return ulo
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to update ULO")
            raise ValueError("Update would violate constraints") from e

    async def delete_ulo(
        self,
        db: Session,
        ulo_id: UUID,
    ) -> bool:
        """Delete a Unit Learning Outcome"""
        ulo = (
            db.query(UnitLearningOutcome)
            .filter(
                and_(
                    UnitLearningOutcome.id == ulo_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                )
            )
            .first()
        )

        if not ulo:
            return False

        # Check for mappings
        material_mappings = db.execute(
            select(material_ulo_mappings).where(
                material_ulo_mappings.c.ulo_id == ulo_id
            )
        ).first()

        assessment_mappings = db.execute(
            select(assessment_ulo_mappings).where(
                assessment_ulo_mappings.c.ulo_id == ulo_id
            )
        ).first()

        if material_mappings or assessment_mappings:
            logger.warning(f"Cannot delete ULO {ulo_id}: has existing mappings")
            raise ValueError("Cannot delete ULO with existing mappings")

        db.delete(ulo)
        db.commit()
        logger.info(f"Deleted ULO {ulo_id}")
        return True

    async def get_ulo(
        self,
        db: Session,
        ulo_id: UUID,
    ) -> UnitLearningOutcome | None:
        """Get a single Unit Learning Outcome"""
        return (
            db.query(UnitLearningOutcome)
            .filter(
                and_(
                    UnitLearningOutcome.id == ulo_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                )
            )
            .first()
        )

    async def get_ulos_by_unit(
        self,
        db: Session,
        unit_id: UUID,
        include_mappings: bool = False,
    ) -> list[UnitLearningOutcome]:
        """Get all ULOs for a unit"""
        query = db.query(UnitLearningOutcome).filter(
            and_(
                UnitLearningOutcome.unit_id == unit_id,
                UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                UnitLearningOutcome.is_active.is_(True),
            )
        )

        if include_mappings:
            # Include mapping counts
            query = query.options(
                selectinload(UnitLearningOutcome.materials),
                selectinload(UnitLearningOutcome.assessments),
            )

        return query.order_by(UnitLearningOutcome.sequence_order).all()

    async def reorder_ulos(
        self,
        db: Session,
        unit_id: UUID,
        reorder_data: OutcomeReorder,
    ) -> list[UnitLearningOutcome]:
        """Reorder ULOs for a unit"""
        ulos = await self.get_ulos_by_unit(db, unit_id)

        # Create ID to ULO mapping
        ulo_map = {str(ulo.id): ulo for ulo in ulos}

        # Validate all IDs exist
        for ulo_id in reorder_data.outcome_ids:
            if ulo_id not in ulo_map:
                raise ValueError(f"ULO {ulo_id} not found in unit")

        # Update order
        for index, ulo_id in enumerate(reorder_data.outcome_ids):
            ulo = ulo_map[ulo_id]
            ulo.sequence_order = index

        db.commit()
        logger.info(f"Reordered {len(reorder_data.outcome_ids)} ULOs for unit {unit_id}")

        return await self.get_ulos_by_unit(db, unit_id)

    async def bulk_create_ulos(
        self,
        db: Session,
        unit_id: UUID,
        bulk_data: BulkULOCreate,
        user_id: UUID,
    ) -> list[UnitLearningOutcome]:
        """Create multiple ULOs at once"""
        created_ulos = []

        # Get starting order index
        max_order = (
            db.query(func.max(UnitLearningOutcome.sequence_order))
            .filter(
                and_(
                    UnitLearningOutcome.unit_id == unit_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                )
            )
            .scalar()
        )
        next_order = (max_order or -1) + 1

        for index, ulo_data in enumerate(bulk_data.outcomes):
            ulo = UnitLearningOutcome(
                unit_id=unit_id,
                outcome_type=OutcomeType.ULO,
                outcome_code=ulo_data.code,
                outcome_text=ulo_data.description,
                bloom_level=ulo_data.bloom_level,
                sequence_order=ulo_data.order_index or (next_order + index),
                created_by_id=user_id,
                is_active=True,
                is_measurable=True,
            )
            db.add(ulo)
            created_ulos.append(ulo)

        try:
            db.commit()
            for ulo in created_ulos:
                db.refresh(ulo)
            logger.info(f"Created {len(created_ulos)} ULOs for unit {unit_id}")
            return created_ulos
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to bulk create ULOs")
            raise ValueError("One or more ULO codes already exist") from e

    async def get_ulo_coverage(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Get coverage statistics for ULOs in a unit"""
        ulos = await self.get_ulos_by_unit(db, unit_id, include_mappings=True)

        total_ulos = len(ulos)
        covered_by_materials = 0
        covered_by_assessments = 0
        fully_covered = 0

        for ulo in ulos:
            has_materials = len(getattr(ulo, "materials", [])) > 0
            has_assessments = len(getattr(ulo, "assessments", [])) > 0

            if has_materials:
                covered_by_materials += 1
            if has_assessments:
                covered_by_assessments += 1
            if has_materials and has_assessments:
                fully_covered += 1

        return {
            "total_ulos": total_ulos,
            "covered_by_materials": covered_by_materials,
            "covered_by_assessments": covered_by_assessments,
            "fully_covered": fully_covered,
            "material_coverage_percentage": (
                (covered_by_materials / total_ulos * 100) if total_ulos > 0 else 0
            ),
            "assessment_coverage_percentage": (
                (covered_by_assessments / total_ulos * 100) if total_ulos > 0 else 0
            ),
            "full_coverage_percentage": (
                (fully_covered / total_ulos * 100) if total_ulos > 0 else 0
            ),
        }


# Create singleton instance
ulo_service = ULOService()
