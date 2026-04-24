"""Business logic for UDL Audit — checkpoint self-assessment CRUD and AI suggestions."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.udl_audit import UDLAuditResponse
from app.models.unit import Unit
from app.models.user import User
from app.schemas.udl_audit import (
    UDLAuditAISuggestion,
    UDLAuditAISuggestionsResponse,
    UDLAuditBatchUpsert,
    UDLAuditResponseItem,
    UDLAuditSummary,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_guidelines() -> dict[str, Any]:
    path = _DATA_DIR / "udl-guidelines.json"
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _load_profiles() -> list[dict[str, Any]]:
    path = _DATA_DIR / "udl-profiles.json"
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _checkpoint_name(checkpoint_id: str) -> str:
    """Look up the checkpoint name from the guidelines file."""
    for principle in _load_guidelines()["principles"]:
        for guideline in principle["guidelines"]:
            for cp in guideline["checkpoints"]:
                if cp["id"] == checkpoint_id:
                    return str(cp["name"])
    return checkpoint_id


def _profile_by_id(profile_id: str) -> dict[str, Any] | None:
    for p in _load_profiles():
        if p["id"] == profile_id:
            return p  # type: ignore[no-any-return]
    return None


class UDLAuditService:
    # ── Read ─────────────────────────────────────────────────────

    def list_profiles(self) -> list[dict[str, Any]]:
        """Return all available audit profiles (id, name, description, checkpoints)."""
        return _load_profiles()

    def list_guidelines(self) -> dict[str, Any]:
        """Return full CAST UDL 3.0 guidelines structure."""
        return _load_guidelines()

    def get_responses(
        self,
        db: Session,
        unit_id: UUID,
        profile_id: str,
        assessment_id: str = "",
    ) -> list[UDLAuditResponseItem]:
        """Return all saved responses for a unit+profile+scope."""
        rows = (
            db.query(UDLAuditResponse)
            .filter(
                and_(
                    UDLAuditResponse.unit_id == str(unit_id),
                    UDLAuditResponse.profile_id == profile_id,
                    UDLAuditResponse.assessment_id == assessment_id,
                )
            )
            .all()
        )
        return [UDLAuditResponseItem.model_validate(r) for r in rows]

    def get_summary(
        self,
        db: Session,
        unit_id: UUID,
        profile_id: str,
        assessment_id: str = "",
    ) -> UDLAuditSummary:
        """Return coverage counts for a unit+profile+scope."""
        rows = (
            db.query(UDLAuditResponse)
            .filter(
                and_(
                    UDLAuditResponse.unit_id == str(unit_id),
                    UDLAuditResponse.profile_id == profile_id,
                    UDLAuditResponse.assessment_id == assessment_id,
                )
            )
            .all()
        )
        profile = _profile_by_id(profile_id)
        total = len(profile["checkpoints"]) if profile else 0
        doing_well = sum(1 for r in rows if r.response == "doing_well")
        needs_work = sum(1 for r in rows if r.response == "needs_work")
        not_applicable = sum(1 for r in rows if r.response == "not_applicable")
        skipped = total - doing_well - needs_work - not_applicable
        return UDLAuditSummary(
            unit_id=str(unit_id),
            profile_id=profile_id,
            assessment_id=assessment_id,
            total_checkpoints=total,
            doing_well=doing_well,
            needs_work=needs_work,
            not_applicable=not_applicable,
            skipped=max(skipped, 0),
        )

    # ── Write ────────────────────────────────────────────────────

    def upsert_responses(
        self,
        db: Session,
        unit_id: UUID,
        data: UDLAuditBatchUpsert,
    ) -> list[UDLAuditResponseItem]:
        """Upsert a batch of checkpoint responses for a unit+profile+scope."""
        for entry in data.responses:
            existing = (
                db.query(UDLAuditResponse)
                .filter(
                    and_(
                        UDLAuditResponse.unit_id == str(unit_id),
                        UDLAuditResponse.profile_id == data.profile_id,
                        UDLAuditResponse.checkpoint_id == entry.checkpoint_id,
                        UDLAuditResponse.assessment_id == data.assessment_id,
                    )
                )
                .first()
            )
            if existing:
                existing.response = entry.response
                existing.notes = entry.notes
            else:
                row = UDLAuditResponse(
                    unit_id=str(unit_id),
                    profile_id=data.profile_id,
                    checkpoint_id=entry.checkpoint_id,
                    assessment_id=data.assessment_id,
                    response=entry.response,
                    notes=entry.notes,
                )
                db.add(row)
        db.commit()
        return self.get_responses(db, unit_id, data.profile_id, data.assessment_id)

    # ── AI suggestions ───────────────────────────────────────────

    async def get_ai_suggestions(
        self,
        db: Session,
        unit_id: UUID,
        profile_id: str,
        assessment_id: str,
        user: User,
        db_for_llm: Session,
    ) -> UDLAuditAISuggestionsResponse:
        """Generate AI improvement suggestions for all needs_work checkpoints."""
        responses = self.get_responses(db, unit_id, profile_id, assessment_id)
        needs_work_ids = [r.checkpoint_id for r in responses if r.response == "needs_work"]

        if not needs_work_ids:
            return UDLAuditAISuggestionsResponse(
                unit_id=str(unit_id),
                profile_id=profile_id,
                assessment_id=assessment_id,
                suggestions=[],
                generated_at=datetime.now(UTC),
            )

        guidelines = _load_guidelines()
        checkpoint_names: dict[str, str] = {
            cp["id"]: cp["name"]
            for principle in guidelines["principles"]
            for guideline in principle["guidelines"]
            for cp in guideline["checkpoints"]
        }

        profile = _profile_by_id(profile_id)
        profile_checkpoints = {cp["checkpointId"]: cp for cp in (profile or {}).get("checkpoints", [])}

        unit = db.query(Unit).filter(Unit.id == str(unit_id)).first()
        unit_context = f"Unit: {unit.title}" if unit else "Unknown unit"

        checkpoint_blocks = []
        for cp_id in needs_work_ids:
            name = checkpoint_names.get(cp_id, cp_id)
            profile_cp = profile_checkpoints.get(cp_id, {})
            helpful = profile_cp.get("helpfulPractice", "")
            context_note = profile_cp.get("contextNote", "")
            block = f"Checkpoint {cp_id}: {name}"
            if context_note:
                block += f"\n  Context: {context_note}"
            if helpful:
                block += f"\n  Helpful practice example: {helpful}"
            checkpoint_blocks.append(block)

        prompt = (
            f"{unit_context}\n\n"
            "The following UDL checkpoints have been identified as needing improvement:\n\n"
            + "\n\n".join(checkpoint_blocks)
            + "\n\nFor each checkpoint, suggest one specific, practical, incremental improvement "
            "the educator could make to their unit or assessment design. Ground each suggestion "
            "in the helpful practice example provided. Be concrete and actionable.\n\n"
            "Return ONLY a JSON array. Example format:\n"
            '[{"checkpoint_id": "4.1", "checkpoint_name": "...", "suggestion": "..."}]'
        )

        try:
            result = await llm_service.generate_text(
                prompt=prompt,
                system_prompt="Return only valid JSON. No markdown, no explanation.",
                user=user,
                db=db_for_llm,
                temperature=0.3,
            )
            raw = str(result).strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            items = json.loads(raw)
            suggestions = [
                UDLAuditAISuggestion(**item)
                for item in items
                if isinstance(item, dict)
            ]
        except Exception:
            logger.exception("UDL audit AI suggestion failed")
            suggestions = []

        return UDLAuditAISuggestionsResponse(
            unit_id=str(unit_id),
            profile_id=profile_id,
            assessment_id=assessment_id,
            suggestions=suggestions,
            generated_at=datetime.now(UTC),
        )


udl_audit_service = UDLAuditService()
