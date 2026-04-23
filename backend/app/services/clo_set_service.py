"""Business logic for CLO Sets."""

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.clo_set import CLOItem, CLOSet, ULOCLOItemMapping, UnitCLOSetAssignment
from app.models.learning_outcome import OutcomeType, UnitLearningOutcome
from app.models.user import User
from app.schemas.clo_sets import (
    CLOItemCreate,
    CLOItemUpdate,
    CLOSetCreate,
    CLOSetUpdate,
    CLOSuggestionPair,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class CLOSetService:

    # ── CLO Sets ──────────────────────────────────────────────

    def create_clo_set(self, db: Session, user_id: UUID, data: CLOSetCreate) -> CLOSet:
        clo_set = CLOSet(
            user_id=str(user_id),
            name=data.name,
            description=data.description,
            program_code=data.program_code,
        )
        db.add(clo_set)
        db.commit()
        db.refresh(clo_set)
        return clo_set

    def list_clo_sets(self, db: Session, user_id: UUID) -> list[CLOSet]:
        return list(
            db.execute(
                select(CLOSet)
                .where(CLOSet.user_id == str(user_id))
                .options(selectinload(CLOSet.items))
                .order_by(CLOSet.created_at)
            ).scalars()
        )

    def get_clo_set(self, db: Session, set_id: UUID, user_id: UUID) -> CLOSet | None:
        return db.execute(
            select(CLOSet)
            .where(CLOSet.id == str(set_id), CLOSet.user_id == str(user_id))
            .options(selectinload(CLOSet.items))
        ).scalar_one_or_none()

    def update_clo_set(
        self, db: Session, set_id: UUID, user_id: UUID, data: CLOSetUpdate
    ) -> CLOSet | None:
        clo_set = self.get_clo_set(db, set_id, user_id)
        if not clo_set:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(clo_set, field, value)
        db.commit()
        db.refresh(clo_set)
        return clo_set

    def delete_clo_set(self, db: Session, set_id: UUID, user_id: UUID) -> bool:
        clo_set = self.get_clo_set(db, set_id, user_id)
        if not clo_set:
            return False
        db.delete(clo_set)
        db.commit()
        return True

    # ── CLO Items ─────────────────────────────────────────────

    def add_clo_item(
        self, db: Session, set_id: UUID, user_id: UUID, data: CLOItemCreate
    ) -> CLOItem | None:
        clo_set = self.get_clo_set(db, set_id, user_id)
        if not clo_set:
            return None
        item = CLOItem(
            clo_set_id=str(set_id),
            code=data.code,
            description=data.description,
            order_index=data.order_index,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def _get_item(self, db: Session, item_id: UUID) -> CLOItem | None:
        return db.execute(
            select(CLOItem).where(CLOItem.id == str(item_id))
        ).scalar_one_or_none()

    def update_clo_item(
        self, db: Session, item_id: UUID, data: CLOItemUpdate
    ) -> CLOItem | None:
        item = self._get_item(db, item_id)
        if not item:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item

    def delete_clo_item(self, db: Session, item_id: UUID) -> bool:
        item = self._get_item(db, item_id)
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    def reorder_clo_items(
        self, db: Session, set_id: UUID, user_id: UUID, item_ids: list[str]
    ) -> list[CLOItem]:
        clo_set = self.get_clo_set(db, set_id, user_id)
        if not clo_set:
            return []
        id_to_item = {item.id: item for item in clo_set.items}
        for idx, item_id in enumerate(item_ids):
            if item_id in id_to_item:
                id_to_item[item_id].order_index = idx
        db.commit()
        return sorted(id_to_item.values(), key=lambda i: i.order_index)

    # ── Unit assignments ──────────────────────────────────────

    def assign_clo_set(
        self, db: Session, unit_id: UUID, set_id: UUID
    ) -> UnitCLOSetAssignment | None:
        existing = db.execute(
            select(UnitCLOSetAssignment).where(
                UnitCLOSetAssignment.unit_id == str(unit_id),
                UnitCLOSetAssignment.clo_set_id == str(set_id),
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        assignment = UnitCLOSetAssignment(
            unit_id=str(unit_id), clo_set_id=str(set_id)
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def unassign_clo_set(self, db: Session, unit_id: UUID, set_id: UUID) -> bool:
        assignment = db.execute(
            select(UnitCLOSetAssignment).where(
                UnitCLOSetAssignment.unit_id == str(unit_id),
                UnitCLOSetAssignment.clo_set_id == str(set_id),
            )
        ).scalar_one_or_none()
        if not assignment:
            return False
        db.delete(assignment)
        db.commit()
        return True

    def get_unit_clo_sets(self, db: Session, unit_id: UUID) -> list[CLOSet]:
        assignments = list(
            db.execute(
                select(UnitCLOSetAssignment)
                .where(UnitCLOSetAssignment.unit_id == str(unit_id))
                .options(
                    selectinload(UnitCLOSetAssignment.clo_set).selectinload(
                        CLOSet.items
                    )
                )
            ).scalars()
        )
        return [a.clo_set for a in assignments]

    # ── ULO → CLO mappings ────────────────────────────────────

    def get_ulo_clo_mappings(
        self, db: Session, ulo_id: UUID
    ) -> list[ULOCLOItemMapping]:
        return list(
            db.execute(
                select(ULOCLOItemMapping).where(
                    ULOCLOItemMapping.ulo_id == str(ulo_id)
                )
            ).scalars()
        )

    def set_ulo_clo_mappings(
        self,
        db: Session,
        ulo_id: UUID,
        clo_item_ids: list[str],
        is_ai_suggested: bool = False,
    ) -> list[ULOCLOItemMapping]:
        """Replace all CLO mappings for a ULO."""
        db.execute(
            ULOCLOItemMapping.__table__.delete().where(
                ULOCLOItemMapping.ulo_id == str(ulo_id)
            )
        )
        mappings = []
        for clo_item_id in clo_item_ids:
            mapping = ULOCLOItemMapping(
                ulo_id=str(ulo_id),
                clo_item_id=clo_item_id,
                is_ai_suggested=is_ai_suggested,
            )
            db.add(mapping)
            mappings.append(mapping)
        db.commit()
        for m in mappings:
            db.refresh(m)
        return mappings

    # ── AI suggestions ────────────────────────────────────────

    async def suggest_clo_mappings(
        self, db: Session, unit_id: UUID, user: User, db_for_llm: Session
    ) -> list[CLOSuggestionPair]:
        """Ask the LLM to match ULOs to CLO items for this unit."""
        ulos = list(
            db.execute(
                select(UnitLearningOutcome).where(
                    UnitLearningOutcome.unit_id == str(unit_id),
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    UnitLearningOutcome.is_active.is_(True),
                )
            ).scalars()
        )
        clo_sets = self.get_unit_clo_sets(db, unit_id)
        clo_items = [item for s in clo_sets for item in s.items]

        if not ulos or not clo_items:
            return []

        ulo_block = "\n".join(
            f'- id:{u.id} {u.outcome_code or "ULO"}: {u.outcome_text}'
            for u in ulos
        )
        clo_block = "\n".join(
            f"- id:{i.id} {i.code}: {i.description}" for i in clo_items
        )
        prompt = (
            "You are an educational alignment assistant. Match each ULO to the CLO(s) "
            "it aligns with. Only include mappings with genuine alignment.\n\n"
            f"ULOs:\n{ulo_block}\n\nCLOs:\n{clo_block}\n\n"
            "Return ONLY a JSON array, no other text. Example:\n"
            '[{"ulo_id": "abc", "clo_item_id": "xyz"}]'
        )

        try:
            result = await llm_service.generate_text(
                prompt=prompt,
                system_prompt="Return only valid JSON. No markdown, no explanation.",
                user=user,
                db=db_for_llm,
                temperature=0.2,
            )
            raw = str(result).strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            pairs = json.loads(raw)
            return [CLOSuggestionPair(**p) for p in pairs if isinstance(p, dict)]
        except Exception:
            logger.exception("CLO suggestion failed")
            return []


clo_set_service = CLOSetService()
