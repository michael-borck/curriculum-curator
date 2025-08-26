"""
Service for managing Weekly Materials
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.learning_outcomes import LocalLearningOutcome
from app.models.mappings import material_ulo_mappings
from app.models.weekly_material import MaterialStatus, WeeklyMaterial
from app.schemas.learning_outcomes import LLOCreate
from app.schemas.materials import (
    MaterialCreate,
    MaterialDuplicate,
    MaterialFilter,
    MaterialMapping,
    MaterialReorder,
    MaterialUpdate,
)

logger = logging.getLogger(__name__)


class MaterialsService:
    """Service for managing Weekly Materials"""

    async def create_material(
        self,
        db: Session,
        unit_id: UUID,
        material_data: MaterialCreate,
    ) -> WeeklyMaterial:
        """Create a new Weekly Material"""
        try:
            # Get the next order index for the week
            max_order = (
                db.query(func.max(WeeklyMaterial.order_index))
                .filter(
                    and_(
                        WeeklyMaterial.unit_id == unit_id,
                        WeeklyMaterial.week_number == material_data.week_number,
                    )
                )
                .scalar()
            )
            next_order = (max_order or -1) + 1

            material = WeeklyMaterial(
                unit_id=unit_id,
                week_number=material_data.week_number,
                title=material_data.title,
                type=material_data.type,
                description=material_data.description,
                duration_minutes=material_data.duration_minutes,
                file_path=material_data.file_path,
                material_metadata=material_data.material_metadata,
                order_index=material_data.order_index or next_order,
                status=material_data.status,
            )

            db.add(material)
            db.commit()
            db.refresh(material)

            logger.info(
                f"Created material '{material.title}' for week {material.week_number}"
            )
            return material

        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to create material")
            raise ValueError("Failed to create material") from e

    async def update_material(
        self,
        db: Session,
        material_id: UUID,
        material_data: MaterialUpdate,
    ) -> WeeklyMaterial | None:
        """Update an existing Weekly Material"""
        material = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id).first()
        )

        if not material:
            return None

        update_data = material_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(material, field, value)

        try:
            db.commit()
            db.refresh(material)
            logger.info(f"Updated material {material_id}")
            return material
        except IntegrityError as e:
            db.rollback()
            logger.exception("Failed to update material")
            raise ValueError("Update would violate constraints") from e

    async def delete_material(
        self,
        db: Session,
        material_id: UUID,
    ) -> bool:
        """Delete a Weekly Material"""
        material = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id).first()
        )

        if not material:
            return False

        db.delete(material)
        db.commit()
        logger.info(f"Deleted material {material_id}")
        return True

    async def get_material(
        self,
        db: Session,
        material_id: UUID,
        include_outcomes: bool = False,
    ) -> WeeklyMaterial | None:
        """Get a single Weekly Material"""
        query = db.query(WeeklyMaterial).filter(WeeklyMaterial.id == material_id)

        if include_outcomes:
            query = query.options(
                selectinload(WeeklyMaterial.local_outcomes),
                selectinload(WeeklyMaterial.learning_outcomes),
            )

        return query.first()

    async def get_materials_by_week(
        self,
        db: Session,
        unit_id: UUID,
        week_number: int,
    ) -> list[WeeklyMaterial]:
        """Get all materials for a specific week"""
        return (
            db.query(WeeklyMaterial)
            .filter(
                and_(
                    WeeklyMaterial.unit_id == unit_id,
                    WeeklyMaterial.week_number == week_number,
                )
            )
            .order_by(WeeklyMaterial.order_index)
            .all()
        )

    async def get_materials_by_unit(
        self,
        db: Session,
        unit_id: UUID,
        filter_params: MaterialFilter | None = None,
    ) -> list[WeeklyMaterial]:
        """Get all materials for a unit with optional filtering"""
        query = db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id)

        if filter_params:
            if filter_params.week_number is not None:
                query = query.filter(
                    WeeklyMaterial.week_number == filter_params.week_number
                )
            if filter_params.type:
                query = query.filter(WeeklyMaterial.type == filter_params.type)
            if filter_params.status:
                query = query.filter(WeeklyMaterial.status == filter_params.status)
            if filter_params.search:
                search_term = f"%{filter_params.search}%"
                query = query.filter(
                    (WeeklyMaterial.title.ilike(search_term))
                    | (WeeklyMaterial.description.ilike(search_term))
                )

        return query.order_by(
            WeeklyMaterial.week_number, WeeklyMaterial.order_index
        ).all()

    async def duplicate_material(
        self,
        db: Session,
        material_id: UUID,
        duplicate_data: MaterialDuplicate,
    ) -> WeeklyMaterial:
        """Duplicate a material to another week"""
        source_material = await self.get_material(
            db, material_id, include_outcomes=True
        )

        if not source_material:
            raise ValueError(f"Material {material_id} not found")

        # Create new material
        new_material = WeeklyMaterial(
            unit_id=source_material.unit_id,
            week_number=duplicate_data.target_week,
            title=duplicate_data.new_title or f"{source_material.title} (Copy)",
            type=source_material.type,
            description=source_material.description,
            duration_minutes=source_material.duration_minutes,
            file_path=source_material.file_path,
            material_metadata=source_material.material_metadata,
            order_index=0,  # Will be at the beginning of the week
            status=MaterialStatus.DRAFT,
        )

        db.add(new_material)
        db.flush()  # Get the ID without committing

        # Duplicate local learning outcomes
        for llo in source_material.local_outcomes:
            new_llo = LocalLearningOutcome(
                material_id=new_material.id,
                description=llo.description,
                order_index=llo.order_index,
            )
            db.add(new_llo)

        # Duplicate ULO mappings
        if hasattr(source_material, "learning_outcomes"):
            for ulo in source_material.learning_outcomes:
                db.execute(
                    material_ulo_mappings.insert().values(
                        material_id=new_material.id,
                        ulo_id=ulo.id,
                    )
                )

        db.commit()
        db.refresh(new_material)

        logger.info(
            f"Duplicated material {material_id} to week {duplicate_data.target_week}"
        )
        return new_material

    async def reorder_materials(
        self,
        db: Session,
        unit_id: UUID,
        week_number: int,
        reorder_data: MaterialReorder,
    ) -> list[WeeklyMaterial]:
        """Reorder materials within a week"""
        materials = await self.get_materials_by_week(db, unit_id, week_number)

        # Create ID to material mapping
        material_map = {str(m.id): m for m in materials}

        # Validate all IDs exist
        for material_id in reorder_data.material_ids:
            if material_id not in material_map:
                raise ValueError(
                    f"Material {material_id} not found in week {week_number}"
                )

        # Update order
        for index, material_id in enumerate(reorder_data.material_ids):
            material = material_map[material_id]
            material.order_index = index

        db.commit()
        logger.info(
            f"Reordered {len(reorder_data.material_ids)} materials in week {week_number}"
        )

        return await self.get_materials_by_week(db, unit_id, week_number)

    async def update_ulo_mappings(
        self,
        db: Session,
        material_id: UUID,
        mapping_data: MaterialMapping,
    ) -> WeeklyMaterial:
        """Update ULO mappings for a material"""
        material = await self.get_material(db, material_id)

        if not material:
            raise ValueError(f"Material {material_id} not found")

        # Clear existing mappings
        db.execute(
            material_ulo_mappings.delete().where(
                material_ulo_mappings.c.material_id == material_id
            )
        )

        # Add new mappings
        for ulo_id in mapping_data.ulo_ids:
            db.execute(
                material_ulo_mappings.insert().values(
                    material_id=material_id,
                    ulo_id=ulo_id,
                )
            )

        db.commit()
        logger.info(f"Updated ULO mappings for material {material_id}")

        return await self.get_material(db, material_id, include_outcomes=True)

    async def add_local_outcome(
        self,
        db: Session,
        material_id: UUID,
        outcome_data: LLOCreate,
    ) -> LocalLearningOutcome:
        """Add a local learning outcome to a material"""
        material = await self.get_material(db, material_id)

        if not material:
            raise ValueError(f"Material {material_id} not found")

        # Get the next order index
        max_order = (
            db.query(func.max(LocalLearningOutcome.order_index))
            .filter(LocalLearningOutcome.material_id == material_id)
            .scalar()
        )
        next_order = (max_order or -1) + 1

        llo = LocalLearningOutcome(
            material_id=material_id,
            description=outcome_data.description,
            order_index=outcome_data.order_index or next_order,
        )

        db.add(llo)
        db.commit()
        db.refresh(llo)

        logger.info(f"Added local outcome to material {material_id}")
        return llo

    async def get_week_summary(
        self,
        db: Session,
        unit_id: UUID,
        week_number: int,
    ) -> dict[str, Any]:
        """Get summary statistics for a week"""
        materials = await self.get_materials_by_week(db, unit_id, week_number)

        total_duration = sum(m.duration_minutes or 0 for m in materials)

        by_type = {}
        by_status = {}

        for material in materials:
            # Count by type
            by_type[material.type] = by_type.get(material.type, 0) + 1
            # Count by status
            by_status[material.status] = by_status.get(material.status, 0) + 1

        return {
            "week_number": week_number,
            "total_materials": len(materials),
            "total_duration_minutes": total_duration,
            "total_duration_hours": round(total_duration / 60, 1),
            "by_type": by_type,
            "by_status": by_status,
            "is_complete": by_status.get(MaterialStatus.DRAFT, 0) == 0,
        }


# Create singleton instance
materials_service = MaterialsService()
