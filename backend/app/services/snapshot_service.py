"""
Service for creating and comparing analytics snapshots.

Snapshots capture quality and UDL scores at a point in time,
allowing users to track unit improvement over semesters.
"""

import json
import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.assessment import Assessment, AssessmentStatus
from app.models.learning_outcome import OutcomeType, UnitLearningOutcome
from app.models.weekly_material import WeeklyMaterial
from app.services.analytics_service import analytics_service
from app.services.udl_service import udl_service

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for analytics snapshot CRUD and comparison."""

    async def create_snapshot(
        self,
        db: Session,
        unit_id: UUID,
        user_id: str | None = None,
        label: str | None = None,
        is_auto: bool = False,
    ) -> dict[str, Any]:
        """Calculate current scores and persist as a snapshot."""
        # Calculate current quality and UDL scores
        quality = await analytics_service.calculate_quality_score(
            db=db, unit_id=unit_id
        )
        udl = await udl_service.calculate_unit_udl(db=db, unit_id=unit_id)

        # Gather summary stats
        material_count = (
            db.query(func.count(WeeklyMaterial.id))
            .filter(WeeklyMaterial.unit_id == str(unit_id))
            .scalar()
            or 0
        )
        assessment_count = (
            db.query(func.count(Assessment.id))
            .filter(
                and_(
                    Assessment.unit_id == str(unit_id),
                    Assessment.status != AssessmentStatus.ARCHIVED,
                )
            )
            .scalar()
            or 0
        )
        ulo_count = (
            db.query(func.count(UnitLearningOutcome.id))
            .filter(
                and_(
                    UnitLearningOutcome.unit_id == str(unit_id),
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    UnitLearningOutcome.is_active.is_(True),
                )
            )
            .scalar()
            or 0
        )
        weeks_with_content = (
            db.query(func.count(func.distinct(WeeklyMaterial.week_number)))
            .filter(WeeklyMaterial.unit_id == str(unit_id))
            .scalar()
            or 0
        )

        snapshot = AnalyticsSnapshot(
            unit_id=str(unit_id),
            label=label,
            is_auto=is_auto,
            quality_overall=quality["overall_score"],
            quality_star_rating=quality["star_rating"],
            quality_grade=quality["grade"],
            quality_sub_scores=json.dumps(quality["sub_scores"]),
            udl_overall=udl["overall_score"],
            udl_star_rating=udl["star_rating"],
            udl_grade=udl["grade"],
            udl_sub_scores=json.dumps(udl["sub_scores"]),
            material_count=material_count,
            assessment_count=assessment_count,
            ulo_count=ulo_count,
            weeks_with_content=weeks_with_content,
            created_by_id=user_id,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return self._snapshot_to_dict(snapshot)

    async def maybe_auto_snapshot(
        self,
        db: Session,
        unit_id: UUID,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Create an auto-snapshot if none exists for today. Returns the snapshot or None."""
        today = date.today()
        existing = (
            db.query(AnalyticsSnapshot)
            .filter(
                and_(
                    AnalyticsSnapshot.unit_id == str(unit_id),
                    AnalyticsSnapshot.is_auto.is_(True),
                    func.date(AnalyticsSnapshot.created_at) == today,
                )
            )
            .first()
        )
        if existing:
            return None

        return await self.create_snapshot(
            db=db, unit_id=unit_id, user_id=user_id, is_auto=True
        )

    def list_snapshots(
        self,
        db: Session,
        unit_id: UUID,
    ) -> list[dict[str, Any]]:
        """List all snapshots for a unit, newest first."""
        snapshots = (
            db.query(AnalyticsSnapshot)
            .filter(AnalyticsSnapshot.unit_id == str(unit_id))
            .order_by(AnalyticsSnapshot.created_at.desc())
            .all()
        )
        return [self._snapshot_to_dict(s) for s in snapshots]

    def get_snapshot(
        self,
        db: Session,
        snapshot_id: UUID,
    ) -> dict[str, Any] | None:
        """Get a single snapshot by ID."""
        snapshot = (
            db.query(AnalyticsSnapshot)
            .filter(AnalyticsSnapshot.id == str(snapshot_id))
            .first()
        )
        if not snapshot:
            return None
        return self._snapshot_to_dict(snapshot)

    def delete_snapshot(
        self,
        db: Session,
        snapshot_id: UUID,
    ) -> bool:
        """Delete a snapshot. Returns True if deleted."""
        snapshot = (
            db.query(AnalyticsSnapshot)
            .filter(AnalyticsSnapshot.id == str(snapshot_id))
            .first()
        )
        if not snapshot:
            return False
        db.delete(snapshot)
        db.commit()
        return True

    async def compare_snapshots(
        self,
        db: Session,
        unit_id: UUID,
        snapshot_a_id: str,
        snapshot_b_id: str,
    ) -> dict[str, Any]:
        """Compare two snapshots (or one snapshot vs current live scores).

        If snapshot_b_id is "current", calculate live scores instead.
        """
        # Get snapshot A
        a = self.get_snapshot(db, UUID(snapshot_a_id))
        if not a:
            raise ValueError(f"Snapshot {snapshot_a_id} not found")

        # Get snapshot B or current
        if snapshot_b_id == "current":
            quality = await analytics_service.calculate_quality_score(
                db=db, unit_id=unit_id
            )
            udl = await udl_service.calculate_unit_udl(db=db, unit_id=unit_id)
            b: dict[str, Any] = {
                "id": "current",
                "label": "Current",
                "is_auto": False,
                "quality_overall": quality["overall_score"],
                "quality_star_rating": quality["star_rating"],
                "quality_grade": quality["grade"],
                "quality_sub_scores": quality["sub_scores"],
                "udl_overall": udl["overall_score"],
                "udl_star_rating": udl["star_rating"],
                "udl_grade": udl["grade"],
                "udl_sub_scores": udl["sub_scores"],
                "created_at": datetime.utcnow().isoformat(),
            }
        else:
            found = self.get_snapshot(db, UUID(snapshot_b_id))
            if not found:
                raise ValueError(f"Snapshot {snapshot_b_id} not found")
            b = found

        # Calculate deltas
        delta = self._calculate_delta(a, b)

        return {"a": a, "b": b, "delta": delta}

    def _calculate_delta(
        self,
        a: dict[str, Any],
        b: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate differences between two snapshots."""
        delta: dict[str, Any] = {
            "quality_overall": round(b["quality_overall"] - a["quality_overall"], 2),
            "udl_overall": round(b["udl_overall"] - a["udl_overall"], 2),
            "quality_sub_scores": {},
            "udl_sub_scores": {},
        }

        a_quality = a["quality_sub_scores"]
        b_quality = b["quality_sub_scores"]
        if isinstance(a_quality, str):
            a_quality = json.loads(a_quality)
        if isinstance(b_quality, str):
            b_quality = json.loads(b_quality)

        for key in a_quality:
            if key in b_quality:
                delta["quality_sub_scores"][key] = round(
                    b_quality[key] - a_quality[key], 2
                )

        a_udl = a["udl_sub_scores"]
        b_udl = b["udl_sub_scores"]
        if isinstance(a_udl, str):
            a_udl = json.loads(a_udl)
        if isinstance(b_udl, str):
            b_udl = json.loads(b_udl)

        for key in a_udl:
            if key in b_udl:
                delta["udl_sub_scores"][key] = round(b_udl[key] - a_udl[key], 2)

        return delta

    def _snapshot_to_dict(self, snapshot: AnalyticsSnapshot) -> dict[str, Any]:
        """Convert an AnalyticsSnapshot ORM object to a dictionary."""
        quality_sub = snapshot.quality_sub_scores
        udl_sub = snapshot.udl_sub_scores

        # Parse JSON strings to dicts
        if isinstance(quality_sub, str):
            quality_sub = json.loads(quality_sub)
        if isinstance(udl_sub, str):
            udl_sub = json.loads(udl_sub)

        return {
            "id": str(snapshot.id),
            "unit_id": str(snapshot.unit_id),
            "label": snapshot.label,
            "is_auto": snapshot.is_auto,
            "quality_overall": snapshot.quality_overall,
            "quality_star_rating": snapshot.quality_star_rating,
            "quality_grade": snapshot.quality_grade,
            "quality_sub_scores": quality_sub,
            "udl_overall": snapshot.udl_overall,
            "udl_star_rating": snapshot.udl_star_rating,
            "udl_grade": snapshot.udl_grade,
            "udl_sub_scores": udl_sub,
            "material_count": snapshot.material_count,
            "assessment_count": snapshot.assessment_count,
            "ulo_count": snapshot.ulo_count,
            "weeks_with_content": snapshot.weeks_with_content,
            "created_by_id": snapshot.created_by_id,
            "created_at": snapshot.created_at.isoformat()
            if isinstance(snapshot.created_at, datetime)
            else str(snapshot.created_at),
        }


snapshot_service = SnapshotService()
