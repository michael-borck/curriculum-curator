"""
Design Context Service

Converts Learning Design content into compact context blocks
that are prepended to AI generation prompts. This is the bridge
between the structured Learning Design and all AI generation paths.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import desc

from app.models.learning_design import DesignStatus, LearningDesign

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


async def get_design_context(
    db: Session,
    unit_id: str,
    design_id: str | None = None,
) -> str | None:
    """Fetch the best available Learning Design and return formatted context.

    Resolution order:
    1. If ``design_id`` is provided, use that specific design.
    2. Otherwise, pick the unit's most recent **approved** design.
    3. Fallback to the most recent **draft** if no approved design exists.
    4. Return ``None`` when no design is found (graceful degradation).
    """
    design: LearningDesign | None = None

    if design_id:
        design = db.query(LearningDesign).filter(LearningDesign.id == design_id).first()
    else:
        # Try approved first
        design = (
            db.query(LearningDesign)
            .filter(
                LearningDesign.unit_id == unit_id,
                LearningDesign.status == DesignStatus.APPROVED.value,
            )
            .order_by(desc(LearningDesign.updated_at))
            .first()
        )
        # Fallback to draft
        if not design:
            design = (
                db.query(LearningDesign)
                .filter(
                    LearningDesign.unit_id == unit_id,
                    LearningDesign.status == DesignStatus.DRAFT.value,
                )
                .order_by(desc(LearningDesign.updated_at))
                .first()
            )

    if not design or not design.content:
        return None

    return format_design_context(design.content)


def _format_list_section(label: str, items: list[str]) -> str | None:
    """Format a list of items as a labelled section, skipping empty entries."""
    filtered = "\n".join(f"  - {item}" for item in items if item)
    return f"{label}:\n{filtered}" if filtered else None


def _format_assessment(assessment: dict[str, Any]) -> str | None:
    """Format the assessment block from design content."""
    if not assessment or not any(
        assessment.get(k) for k in ("type", "weight", "description")
    ):
        return None
    parts: list[str] = []
    if atype := assessment.get("type"):
        parts.append(f"Type: {atype}")
    if weight := assessment.get("weight"):
        parts.append(f"Weight: {weight}")
    if adesc := assessment.get("description"):
        parts.append(f"Description: {adesc}")
    criteria: list[str] = assessment.get("criteria", [])
    crit_items = ", ".join(c for c in criteria if c)
    if crit_items:
        parts.append(f"Criteria: {crit_items}")
    return "Assessment:\n  " + "\n  ".join(parts)


def _format_structure(structure: dict[str, Any]) -> str | None:
    """Format the class structure block from design content."""
    if not structure:
        return None
    struct_parts: list[str] = []
    for phase, label in [
        ("preClass", "Pre-Class"),
        ("inClass", "In-Class"),
        ("postClass", "Post-Class"),
    ]:
        phase_data: dict[str, Any] = structure.get(phase, {})
        activities = [a for a in phase_data.get("activities", []) if a]
        if activities:
            struct_parts.append(f"  {label}: {', '.join(activities)}")
    return "Class Structure:\n" + "\n".join(struct_parts) if struct_parts else None


def format_design_context(
    content: dict[str, Any],
    pedagogy_fallback: str | None = None,
) -> str:
    """Convert a Learning Design content JSON blob into a compact plaintext block.

    The output is delimited with ``=== LEARNING DESIGN SPEC ===`` so LLMs
    treat it as a distinct context block. Empty/None sections are skipped to
    keep the prompt compact for small local models.
    """
    sections: list[str] = []

    if topic := content.get("topic"):
        sections.append(f"Topic: {topic}")
    if duration := content.get("duration"):
        sections.append(f"Duration: {duration}")

    philosophy = content.get("teachingPhilosophy") or pedagogy_fallback
    if philosophy:
        sections.append(f"Teaching Philosophy: {philosophy}")

    for label, key in [
        ("Objectives", "objectives"),
        ("Learning Outcomes", "learningOutcomes"),
        ("Prerequisites", "prerequisites"),
    ]:
        if section := _format_list_section(label, content.get(key, [])):
            sections.append(section)

    if notes := content.get("pedagogyNotes"):
        sections.append(f"Pedagogy Notes: {notes}")
    if diff := content.get("differentiation"):
        sections.append(f"Differentiation: {diff}")

    if asmt := _format_assessment(content.get("assessment", {})):
        sections.append(asmt)
    if struct := _format_structure(content.get("structure", {})):
        sections.append(struct)

    if not sections:
        return ""

    body = "\n".join(sections)
    return f"=== LEARNING DESIGN SPEC ===\n{body}\n=== END SPEC ==="


# Style map — mirrors llm_service._build_pedagogy_prompt() styles
_PEDAGOGY_STYLES: dict[str, str] = {
    "traditional": "Focus on direct instruction, clear explanations, and structured practice.",
    "inquiry-based": "Encourage questioning, exploration, and discovery learning.",
    "project-based": "Emphasise real-world applications and hands-on projects.",
    "collaborative": "Promote group work, peer learning, and discussion.",
    "game-based": "Incorporate game elements, challenges, and rewards.",
    "flipped": "Design for self-paced learning with active classroom application.",
    "differentiated": "Provide multiple paths and options for different learners.",
    "constructivist": "Build on prior knowledge and encourage meaning-making.",
    "experiential": "Focus on learning through experience and reflection.",
}


def build_pedagogy_instruction(
    design_content: dict[str, Any] | None = None,
    fallback_style: str = "inquiry-based",
) -> str:
    """Build a rich pedagogy instruction string from design content.

    When a Learning Design is available, combines ``teachingPhilosophy``,
    ``pedagogyNotes``, and ``differentiation`` into a multi-sentence
    instruction. Otherwise falls back to the one-liner style map.
    """
    if design_content:
        parts: list[str] = []
        philosophy = design_content.get("teachingPhilosophy")
        if philosophy:
            # Normalise to lookup key
            key = philosophy.lower().replace("_", "-").replace(" ", "-")
            style_desc = _PEDAGOGY_STYLES.get(key, "")
            parts.append(f"Use a {philosophy} teaching approach.")
            if style_desc:
                parts.append(style_desc)

        if notes := design_content.get("pedagogyNotes"):
            parts.append(f"Pedagogy guidance: {notes}")

        if diff := design_content.get("differentiation"):
            parts.append(f"Differentiation strategy: {diff}")

        if parts:
            return " ".join(parts)

    # Fallback to simple style map
    key = fallback_style.lower().replace("_", "-").replace(" ", "-")
    style_desc = _PEDAGOGY_STYLES.get(key, "")
    if style_desc:
        return f"Use a {fallback_style} teaching approach. {style_desc}"
    return f"Use a {fallback_style} teaching approach."
