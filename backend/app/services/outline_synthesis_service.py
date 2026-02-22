"""
Outline Synthesis Service — propose/apply pattern for AI-assisted unit construction.

Three actions:
- scaffold: Generate a full unit outline from research sources
- compare: Compare sources against an existing unit to find gaps/overlaps
- match_reading_list: Map sources to unit weeks with confidence scores

All 'propose' methods are read-only (no DB writes). 'Apply' is handled at the route layer.
"""

import logging

from sqlalchemy.orm import Session

from app.models.learning_outcome import UnitLearningOutcome
from app.models.unit import Unit
from app.models.weekly_topic import WeeklyTopic
from app.schemas.ai import ScaffoldUnitResponse
from app.schemas.research import (
    ComparisonProposal,
    ReadingListProposal,
    SourceInput,
    UnitWeekInfo,
)
from app.services.design_context import build_pedagogy_instruction, get_design_context
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class OutlineSynthesisService:
    """AI-powered outline synthesis from research sources."""

    async def propose_scaffold(
        self,
        sources: list[SourceInput],
        unit_title: str,
        unit_description: str,
        duration_weeks: int,
        pedagogy_style: str,
        unit_id: str | None,
        design_id: str | None,
        db: Session,
    ) -> ScaffoldUnitResponse | None:
        """Generate a unit scaffold informed by research sources.

        Returns ScaffoldUnitResponse (same schema as /api/ai/scaffold-unit).
        """
        # Build source context
        source_block = self._format_sources(sources)

        # Build pedagogy instruction from Learning Design or style
        design_context = ""
        if unit_id:
            ctx = await get_design_context(db, unit_id, design_id)
            if ctx:
                design_context = f"\n\n{ctx}"

        pedagogy_instruction = build_pedagogy_instruction(fallback_style=pedagogy_style)

        prompt = f"""You are an expert curriculum designer at an Australian university.

Generate a complete unit outline based on the following research sources and parameters.

=== UNIT PARAMETERS ===
Title: {unit_title}
Description: {unit_description}
Duration: {duration_weeks} weeks
{pedagogy_instruction}
{design_context}

=== RESEARCH SOURCES ===
{source_block}

=== INSTRUCTIONS ===
Create a comprehensive unit structure that:
1. Draws on the research sources for topic selection and sequencing
2. Includes {duration_weeks} weekly topics with realistic activities
3. Defines 4-6 Unit Learning Outcomes (ULOs) using Bloom's taxonomy verbs
4. Includes 3-5 assessments with appropriate weights totalling 100%
5. Follows Australian university conventions (unit = subject, not degree)
6. References specific sources in weekly topics where relevant

Return a JSON object with: title, description, ulos[], weeks[], assessments[].
Each ULO has: code, description, bloom_level.
Each week has: week_number, topic, activities[].
Each assessment has: title, category, weight, due_week."""

        result, error = await llm_service.generate_structured_content(
            prompt=prompt,
            response_model=ScaffoldUnitResponse,
            max_retries=3,
        )

        if error:
            logger.error("Scaffold generation failed: %s", error)
            return None

        return result  # type: ignore[return-value]

    async def propose_comparison(
        self,
        sources: list[SourceInput],
        unit_id: str,
        db: Session,
    ) -> ComparisonProposal | None:
        """Compare sources against an existing unit's structure.

        Identifies gaps, overlaps, and improvement suggestions.
        """
        # Load existing unit structure
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            logger.error("Unit %s not found for comparison", unit_id)
            return None

        topics = (
            db.query(WeeklyTopic)
            .filter(WeeklyTopic.unit_id == unit_id)
            .order_by(WeeklyTopic.week_number)
            .all()
        )

        ulos = (
            db.query(UnitLearningOutcome)
            .filter(UnitLearningOutcome.unit_id == unit_id)
            .order_by(UnitLearningOutcome.sequence_order)
            .all()
        )

        # Build unit context
        week_lines = "\n".join(
            f"  Week {t.week_number}: {t.topic_title}" for t in topics
        )
        ulo_lines = "\n".join(f"  {o.outcome_code}: {o.outcome_text}" for o in ulos)

        source_block = self._format_sources(sources)

        prompt = f"""You are an expert curriculum reviewer at an Australian university.

Compare the following research sources against an existing unit structure.
Identify gaps, overlaps, and suggest improvements.

=== EXISTING UNIT ===
Title: {unit.title}
Description: {unit.description or "N/A"}

Weekly Topics:
{week_lines or "  No topics defined yet"}

Learning Outcomes:
{ulo_lines or "  No ULOs defined yet"}

=== RESEARCH SOURCES ===
{source_block}

=== INSTRUCTIONS ===
For each week, assess coverage as one of: well_covered, partially_covered, not_covered.
List which sources are relevant to each week.
Identify gaps (topics in sources but missing from the unit).
Identify overlaps (topics covered by multiple sources unnecessarily).
Suggest specific improvements.

Return JSON with: unit_id, weeks[], gaps[], overlaps[], suggestions[].
Each week has: week_number, topic, coverage, matching_sources[].
Use the actual week numbers and topics from the unit above."""

        result, error = await llm_service.generate_structured_content(
            prompt=prompt,
            response_model=ComparisonProposal,
            max_retries=3,
        )

        if error:
            logger.error("Comparison generation failed: %s", error)
            return None

        # Ensure unit_id is set correctly
        if result:
            result.unit_id = str(unit_id)  # type: ignore[union-attr]

        return result  # type: ignore[return-value]

    async def propose_reading_list(
        self,
        sources: list[SourceInput],
        unit_id: str,
        db: Session,
    ) -> ReadingListProposal | None:
        """Match sources to unit weeks with confidence scores.

        Returns each source mapped to its best-fit week.
        """
        # Load unit weeks
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            logger.error("Unit %s not found for reading list", unit_id)
            return None

        topics = (
            db.query(WeeklyTopic)
            .filter(WeeklyTopic.unit_id == unit_id)
            .order_by(WeeklyTopic.week_number)
            .all()
        )

        if not topics:
            logger.warning("Unit %s has no weekly topics", unit_id)
            return None

        week_lines = "\n".join(
            f"  Week {t.week_number}: {t.topic_title}" for t in topics
        )

        source_block = self._format_sources(sources)

        prompt = f"""You are an expert curriculum designer at an Australian university.

Match each research source to the most appropriate week in the unit.

=== UNIT WEEKS ===
{week_lines}

=== RESEARCH SOURCES ===
{source_block}

=== INSTRUCTIONS ===
For each source, determine:
1. Which week it best fits (use the week numbers above)
2. A confidence score (0.0-1.0) for the match
3. Brief reasoning for the assignment

If a source doesn't fit any week well, set suggested_week to null and explain why.

Return JSON with: unit_id, matches[].
Each match has: url, title, suggested_week (int or null), confidence (float), reasoning (string)."""

        result, error = await llm_service.generate_structured_content(
            prompt=prompt,
            response_model=ReadingListProposal,
            max_retries=3,
        )

        if error:
            logger.error("Reading list generation failed: %s", error)
            return None

        if result:
            proposal: ReadingListProposal = result  # type: ignore[assignment]
            # Fill in unit_id and week info
            proposal.unit_id = str(unit_id)
            proposal.unit_weeks = [
                UnitWeekInfo(week_number=t.week_number, topic=t.topic_title)
                for t in topics
            ]

            # Calculate aggregate stats
            matched = [m for m in proposal.matches if m.suggested_week is not None]
            proposal.unmatched_count = len(proposal.matches) - len(matched)
            if matched:
                proposal.avg_confidence = sum(m.confidence for m in matched) / len(
                    matched
                )

        return result  # type: ignore[return-value]

    def _format_sources(self, sources: list[SourceInput]) -> str:
        """Format sources into a text block for LLM prompts."""
        lines: list[str] = []
        for i, src in enumerate(sources, 1):
            lines.append(f"Source {i}: {src.title}")
            lines.append(f"  URL: {src.url}")
            if src.summary:
                lines.append(f"  Summary: {src.summary}")
            if src.key_points:
                lines.extend(f"  - {kp}" for kp in src.key_points)
            lines.append("")
        return "\n".join(lines)


# Singleton
outline_synthesis_service = OutlineSynthesisService()
