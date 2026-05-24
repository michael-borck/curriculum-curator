"""
Curriculum Context Builder.

One seam for assembling the AI-generation context for a unit/week: the Learning
Design spec, the weekly topic + existing materials, and any source materials.
Replaces the per-endpoint stitching of get_design_context / week-enrichment /
source-injection that was scattered (and composed inconsistently) across ai.py.

(This is candidate #4 in docs/architecture-deepening.md, delivered as part of #2.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.models.weekly_material import WeeklyMaterial
from app.models.weekly_topic import WeeklyTopic
from app.services.design_context import get_design_context

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Cap on how many source materials get inlined into a prompt.
_MAX_SOURCE_MATERIALS = 5


@dataclass
class CurriculumContext:
    """The assembled context blocks for an AI generation request.

    Each block is either a ready-to-embed string or ``None`` when absent.
    Use :meth:`as_block` to join them in canonical order, or :meth:`prepend_to`
    to put the context ahead of a task/topic string.
    """

    design_spec: str | None = None
    week_context: str | None = None
    source_materials: str | None = None

    def as_block(self, separator: str = "\n\n") -> str:
        """Join present sections in canonical order: design → week → sources."""
        return separator.join(
            part
            for part in (self.design_spec, self.week_context, self.source_materials)
            if part
        )

    def prepend_to(self, text: str, separator: str = "\n\n") -> str:
        """Prepend the assembled context block to ``text`` (empty block = no-op)."""
        block = self.as_block(separator)
        return f"{block}{separator}{text}" if block else text


def build_week_context(db: Session, unit_id: str, week_number: int) -> str | None:
    """Build the weekly topic + existing-materials block, or None if empty."""
    weekly_topic = (
        db.query(WeeklyTopic)
        .filter(
            WeeklyTopic.unit_id == unit_id,
            WeeklyTopic.week_number == week_number,
        )
        .first()
    )
    weekly_materials = (
        db.query(WeeklyMaterial)
        .filter(
            WeeklyMaterial.unit_id == unit_id,
            WeeklyMaterial.week_number == week_number,
        )
        .all()
    )
    parts: list[str] = []
    if weekly_topic and weekly_topic.topic_title:
        parts.append(
            f"Week {week_number} Topic: <user_data>{weekly_topic.topic_title}</user_data>"
        )
    titles = [m.title for m in weekly_materials if m.title]
    if titles:
        parts.append(f"Existing materials for this week: {', '.join(titles)}")
    return "\n".join(parts) if parts else None


def build_source_materials(db: Session, material_ids: list[str]) -> str | None:
    """Build the source-materials block from material descriptions, or None."""
    source_materials = (
        db.query(WeeklyMaterial)
        .filter(WeeklyMaterial.id.in_(material_ids[:_MAX_SOURCE_MATERIALS]))
        .all()
    )
    if not source_materials:
        return None
    lines = ["=== SOURCE MATERIALS ==="]
    for mat in source_materials:
        lines.append(f"\n--- <user_data>{mat.title}</user_data> ---")
        if mat.description:
            lines.append(f"<user_data>{mat.description}</user_data>")
    lines.append("=== END SOURCE MATERIALS ===")
    return "\n".join(lines)


async def build_context(
    db: Session,
    *,
    unit_id: str | None = None,
    design_id: str | None = None,
    week_number: int | None = None,
    source_material_ids: list[str] | None = None,
) -> CurriculumContext:
    """Assemble the full curriculum context behind one call.

    Each section is fetched only when its inputs are present; an absent section
    is ``None``. Safe to call with no design/week/sources (returns an empty
    context whose ``prepend_to`` is a no-op).
    """
    design_spec: str | None = None
    if unit_id or design_id:
        design_spec = await get_design_context(db, unit_id or "", design_id)

    week_context: str | None = None
    if week_number and unit_id:
        week_context = build_week_context(db, unit_id, week_number)

    source_materials: str | None = None
    if source_material_ids:
        source_materials = build_source_materials(db, source_material_ids)

    return CurriculumContext(
        design_spec=design_spec,
        week_context=week_context,
        source_materials=source_materials,
    )
