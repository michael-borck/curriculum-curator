"""
UDL (Universal Design for Learning) scoring service.

Measures pedagogical inclusivity across 4 dimensions:
1. Representation Diversity (UDL Principle 1)
2. Engagement Variety (UDL Principle 2)
3. Action & Expression Options (UDL Principle 3)
4. Content Accessibility
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, AssessmentStatus
from app.models.weekly_material import WeeklyMaterial
from app.plugins.accessibility_validator import AccessibilityValidator
from app.plugins.readability_validator import ReadabilityValidator
from app.services.scoring_utils import score_to_grade, score_to_stars, shannon_diversity

logger = logging.getLogger(__name__)

# Interactive session formats score higher for engagement
_INTERACTIVE_FORMATS = {"workshop", "lab", "seminar", "tutorial"}
_PASSIVE_FORMATS = {"lecture", "independent"}


class UDLService:
    """Service for calculating UDL inclusivity scores and suggestions."""

    def __init__(self) -> None:
        self._readability = ReadabilityValidator()
        self._accessibility = AccessibilityValidator()

    # ------------------------------------------------------------------
    # Per-week scoring
    # ------------------------------------------------------------------

    def _week_representation_score(
        self,
        materials: list[WeeklyMaterial],
    ) -> float:
        """Representation Diversity — Shannon on material category + description length bonus."""
        if not materials:
            return 0.0

        categories = [str(m.category) for m in materials]
        diversity = shannon_diversity(categories)

        # Bonus for varying description lengths (short + long = richer representation)
        desc_lengths = [len(m.description) for m in materials if m.description]
        length_bonus = 0.0
        if len(desc_lengths) >= 2:
            has_short = any(ln < 200 for ln in desc_lengths)
            has_long = any(ln >= 200 for ln in desc_lengths)
            if has_short and has_long:
                length_bonus = 15.0

        return min(100.0, diversity + length_bonus)

    def _week_engagement_score(
        self,
        materials: list[WeeklyMaterial],
    ) -> float:
        """Engagement Variety — weighted by interactive vs passive formats."""
        if not materials:
            return 0.0

        types = [str(m.type) for m in materials]
        unique_types = set(types)

        # Base: diversity of session formats
        diversity = shannon_diversity(types)

        # Bonus for interactive types
        interactive_count = sum(1 for t in unique_types if t in _INTERACTIVE_FORMATS)
        passive_count = sum(1 for t in unique_types if t in _PASSIVE_FORMATS)
        total_unique = len(unique_types)

        if total_unique == 0:
            return 0.0

        interactivity_ratio = interactive_count / total_unique
        # A week with only lectures = low; lecture + tutorial + lab = high
        interactivity_bonus = interactivity_ratio * 30.0

        # Penalise weeks that are purely passive
        if interactive_count == 0 and passive_count > 0:
            return max(0.0, diversity * 0.5)

        return min(100.0, diversity * 0.7 + interactivity_bonus)

    def _week_expression_score(
        self,
        assessments: list[Assessment],
    ) -> float:
        """Action & Expression — assessment diversity linked to the week."""
        if not assessments:
            return 50.0  # Neutral — not penalised

        categories = [str(a.category) for a in assessments]
        diversity = shannon_diversity(categories)

        # Bonus for group work mix
        has_group = any(a.group_work for a in assessments)
        has_individual = any(not a.group_work for a in assessments)
        group_bonus = 15.0 if (has_group and has_individual) else 0.0

        # Bonus for submission type variety
        submission_types = {
            str(a.submission_type) for a in assessments if a.submission_type
        }
        sub_bonus = min(10.0, len(submission_types) * 5.0)

        return min(100.0, diversity + group_bonus + sub_bonus)

    async def _week_accessibility_score(
        self,
        materials: list[WeeklyMaterial],
        target_level: str,
    ) -> float:
        """Content Accessibility — readability + WCAG checks on text content."""
        texts = [
            m.description
            for m in materials
            if m.description and len(m.description) >= 100
        ]
        if not texts:
            return 50.0  # Neutral when no text content

        scores: list[float] = []
        for text in texts:
            readability_result = await self._readability.validate(
                text, {"config": {"target_level": target_level}}
            )
            accessibility_result = await self._accessibility.validate(text, {})

            r_score = 50.0
            if readability_result.data and not readability_result.data.get("skipped"):
                # Convert Flesch Reading Ease to a 0-100 quality score
                flesch = readability_result.data.get("flesch_reading_ease", 50.0)
                # For university level, 30-60 Flesch is ideal; penalise extremes
                if target_level == "university":
                    if 30 <= flesch <= 60:
                        r_score = 90.0
                    elif 20 <= flesch < 30 or 60 < flesch <= 70:
                        r_score = 70.0
                    else:
                        r_score = max(30.0, 100.0 - abs(flesch - 45.0))
                else:
                    r_score = min(100.0, flesch)

            a_score = 50.0
            if accessibility_result.data:
                a_score = float(accessibility_result.data.get("score", 50))

            scores.append(r_score * 0.5 + a_score * 0.5)

        return round(sum(scores) / len(scores), 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def calculate_weekly_udl(
        self,
        db: Session,
        unit_id: UUID,
        total_weeks: int = 12,
        target_level: str = "university",
    ) -> list[dict[str, Any]]:
        """Calculate per-week UDL scores."""
        materials = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
        )
        assessments = (
            db.query(Assessment)
            .filter(
                and_(
                    Assessment.unit_id == unit_id,
                    Assessment.status != AssessmentStatus.ARCHIVED,
                )
            )
            .all()
        )

        # Group by week
        mat_by_week: dict[int, list[WeeklyMaterial]] = {}
        for m in materials:
            mat_by_week.setdefault(m.week_number, []).append(m)

        # Map assessments to weeks via release_week / due_week
        assess_by_week: dict[int, list[Assessment]] = {}
        for a in assessments:
            weeks: set[int] = set()
            if a.release_week is not None:
                weeks.add(a.release_week)
            if a.due_week is not None:
                weeks.add(a.due_week)
            for w in weeks:
                assess_by_week.setdefault(w, []).append(a)

        results: list[dict[str, Any]] = []
        for week in range(1, total_weeks + 1):
            week_mats = mat_by_week.get(week, [])
            week_assess = assess_by_week.get(week, [])
            has_content = len(week_mats) > 0 or len(week_assess) > 0

            if not has_content:
                results.append(
                    {
                        "week_number": week,
                        "has_content": False,
                        "sub_scores": {
                            "representation": 0.0,
                            "engagement": 0.0,
                            "expression": 50.0,
                            "accessibility": 50.0,
                        },
                        "star_rating": 0.0,
                    }
                )
                continue

            rep = self._week_representation_score(week_mats)
            eng = self._week_engagement_score(week_mats)
            expr = self._week_expression_score(week_assess)
            acc = await self._week_accessibility_score(week_mats, target_level)

            avg = (rep + eng + expr + acc) / 4.0
            results.append(
                {
                    "week_number": week,
                    "has_content": True,
                    "sub_scores": {
                        "representation": round(rep, 2),
                        "engagement": round(eng, 2),
                        "expression": round(expr, 2),
                        "accessibility": round(acc, 2),
                    },
                    "star_rating": score_to_stars(avg),
                }
            )

        return results

    async def calculate_unit_udl(
        self,
        db: Session,
        unit_id: UUID,
        total_weeks: int = 12,
        target_level: str = "university",
    ) -> dict[str, Any]:
        """Calculate unit-level UDL score with sub-dimensions."""
        weekly = await self.calculate_weekly_udl(db, unit_id, total_weeks, target_level)

        # Weighted average of weeks with content
        content_weeks = [w for w in weekly if w["has_content"]]
        if not content_weeks:
            sub = {
                "representation": 0.0,
                "engagement": 0.0,
                "expression": 50.0,
                "accessibility": 50.0,
            }
            return {
                "unit_id": str(unit_id),
                "overall_score": 0.0,
                "star_rating": 0.0,
                "sub_scores": sub,
                "assessment_format_diversity": 0.0,
                "grade": "F",
                "calculated_at": datetime.utcnow(),
            }

        dims = ["representation", "engagement", "expression", "accessibility"]
        avg_sub = {
            d: round(
                sum(w["sub_scores"][d] for w in content_weeks) / len(content_weeks), 2
            )
            for d in dims
        }

        # Unit-level assessment format diversity
        assessments = (
            db.query(Assessment)
            .filter(
                and_(
                    Assessment.unit_id == unit_id,
                    Assessment.status != AssessmentStatus.ARCHIVED,
                )
            )
            .all()
        )
        assess_categories = [str(a.category) for a in assessments]
        assess_diversity = shannon_diversity(assess_categories)

        overall = sum(avg_sub.values()) / len(dims)

        return {
            "unit_id": str(unit_id),
            "overall_score": round(overall, 2),
            "star_rating": score_to_stars(overall),
            "sub_scores": avg_sub,
            "assessment_format_diversity": round(assess_diversity, 2),
            "grade": score_to_grade(overall),
            "calculated_at": datetime.utcnow(),
        }

    def _suggest_representation(
        self,
        mat_by_week: dict[int, list[WeeklyMaterial]],
        total_weeks: int,
    ) -> list[dict[str, str]]:
        """Representation suggestions — category diversity per week."""
        suggestions: list[dict[str, str]] = []
        for week_num in range(1, total_weeks + 1):
            week_mats = mat_by_week.get(week_num, [])
            if not week_mats:
                continue
            cats = {str(m.category) for m in week_mats}
            if len(cats) <= 1:
                suggestions.append(
                    {
                        "dimension": "representation",
                        "priority": "medium",
                        "issue": f"Week {week_num} has materials in only one category",
                        "suggestion": (
                            "Add pre-class readings or post-class review materials. "
                            "Providing content in multiple formats (e.g., lecture slides AND "
                            "a reading AND a short video summary) helps diverse learners."
                        ),
                    }
                )
        return suggestions

    def _suggest_engagement(
        self,
        mat_by_week: dict[int, list[WeeklyMaterial]],
        total_weeks: int,
    ) -> list[dict[str, str]]:
        """Engagement suggestions — interactive vs passive formats per week."""
        suggestions: list[dict[str, str]] = []
        for week_num in range(1, total_weeks + 1):
            week_mats = mat_by_week.get(week_num, [])
            if not week_mats:
                continue
            types = {str(m.type) for m in week_mats}
            if not any(t in _INTERACTIVE_FORMATS for t in types):
                suggestions.append(
                    {
                        "dimension": "engagement",
                        "priority": "medium",
                        "issue": f"Week {week_num} relies solely on passive formats",
                        "suggestion": (
                            "Add an interactive activity \u2014 a tutorial discussion, "
                            "a Mentimeter poll, an H5P quiz, or a small group exercise "
                            "increases student engagement."
                        ),
                    }
                )
        return suggestions

    @staticmethod
    def _suggest_expression(assessments: list[Assessment]) -> list[dict[str, str]]:
        """Expression suggestions — assessment diversity."""
        suggestions: list[dict[str, str]] = []
        if not assessments:
            return suggestions

        categories = {str(a.category) for a in assessments}
        if len(categories) <= 1:
            suggestions.append(
                {
                    "dimension": "expression",
                    "priority": "medium",
                    "issue": "All assessments use the same format",
                    "suggestion": (
                        "Consider mixing assessment types \u2014 adding a presentation, "
                        "portfolio, or group project alongside written assignments "
                        "gives students multiple ways to demonstrate learning."
                    ),
                }
            )

        has_group = any(a.group_work for a in assessments)
        has_individual = any(not a.group_work for a in assessments)
        if not has_group and len(assessments) >= 2:
            suggestions.append(
                {
                    "dimension": "expression",
                    "priority": "low",
                    "issue": "No group assessments",
                    "suggestion": (
                        "Consider adding a collaborative assessment. Group projects "
                        "or peer reviews develop teamwork skills and provide "
                        "alternative ways for students to express understanding."
                    ),
                }
            )
        elif has_group and not has_individual:
            suggestions.append(
                {
                    "dimension": "expression",
                    "priority": "low",
                    "issue": "All assessments are group-based",
                    "suggestion": (
                        "Add an individual assessment so students can also demonstrate "
                        "learning independently."
                    ),
                }
            )

        sub_types = {str(a.submission_type) for a in assessments if a.submission_type}
        if len(sub_types) <= 1 and len(assessments) >= 3:
            suggestions.append(
                {
                    "dimension": "expression",
                    "priority": "low",
                    "issue": "All assessments use the same submission mode",
                    "suggestion": (
                        "Varying submission types (online, in-person, or both) "
                        "accommodates different learner needs and reduces barriers."
                    ),
                }
            )

        return suggestions

    async def _suggest_accessibility(
        self,
        mat_by_week: dict[int, list[WeeklyMaterial]],
        total_weeks: int,
        target_level: str,
    ) -> list[dict[str, str]]:
        """Accessibility suggestions — readability checks on material content."""
        target_grades = {
            "elementary": 5,
            "middle_school": 8,
            "high_school": 12,
            "university": 16,
            "postgraduate": 18,
        }
        target_g = target_grades.get(target_level, 14)
        suggestions: list[dict[str, str]] = []

        for week_num in range(1, total_weeks + 1):
            for mat in mat_by_week.get(week_num, []):
                if not mat.description or len(mat.description) < 100:
                    continue
                result = await self._readability.validate(
                    mat.description, {"config": {"target_level": target_level}}
                )
                if result.data and not result.data.get("skipped"):
                    grade = result.data.get("flesch_kincaid_grade", 0)
                    if grade > target_g + 3:
                        suggestions.append(
                            {
                                "dimension": "accessibility",
                                "priority": "high",
                                "issue": (
                                    f"Material '{mat.title}' reads at grade {grade:.0f} level "
                                    f"(target: {target_level})"
                                ),
                                "suggestion": (
                                    "Simplify sentence structure and vocabulary. "
                                    "Aim for shorter sentences (15\u201320 words) and "
                                    "replace jargon with plain language where possible."
                                ),
                            }
                        )
        return suggestions

    async def get_udl_suggestions(
        self,
        db: Session,
        unit_id: UUID,
        total_weeks: int = 12,
        target_level: str = "university",
    ) -> dict[str, Any]:
        """Generate rule-based UDL improvement suggestions."""
        materials = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
        )
        assessments = (
            db.query(Assessment)
            .filter(
                and_(
                    Assessment.unit_id == unit_id,
                    Assessment.status != AssessmentStatus.ARCHIVED,
                )
            )
            .all()
        )

        mat_by_week: dict[int, list[WeeklyMaterial]] = {}
        for m in materials:
            mat_by_week.setdefault(m.week_number, []).append(m)

        suggestions: list[dict[str, str]] = []
        suggestions.extend(self._suggest_representation(mat_by_week, total_weeks))
        suggestions.extend(self._suggest_engagement(mat_by_week, total_weeks))
        suggestions.extend(self._suggest_expression(assessments))
        suggestions.extend(
            await self._suggest_accessibility(mat_by_week, total_weeks, target_level)
        )

        return {
            "unit_id": str(unit_id),
            "suggestions": suggestions,
            "generated_at": datetime.utcnow(),
        }


# Singleton
udl_service = UDLService()
