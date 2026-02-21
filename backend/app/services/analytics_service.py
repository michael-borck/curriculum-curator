"""
Service for analytics and reporting
"""

import logging
import math
from collections import Counter
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import Assessment, AssessmentStatus
from app.models.learning_outcome import (
    OutcomeType,
    UnitLearningOutcome,
)
from app.models.weekly_material import MaterialStatus, WeeklyMaterial

logger = logging.getLogger(__name__)

# Default weights for quality dimensions
DEFAULT_QUALITY_WEIGHTS: dict[str, float] = {
    "completeness": 0.20,
    "contentQuality": 0.15,
    "uloAlignment": 0.25,
    "workloadBalance": 0.10,
    "materialDiversity": 0.10,
    "assessmentDistribution": 0.20,
}


class AnalyticsService:
    """Service for generating analytics and reports"""

    async def get_unit_overview(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Get comprehensive overview of a unit"""
        # Count ULOs
        ulo_count = (
            db.query(func.count(UnitLearningOutcome.id))
            .filter(
                and_(
                    UnitLearningOutcome.unit_id == unit_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    UnitLearningOutcome.is_active.is_(True),
                )
            )
            .scalar()
        )

        # Count materials by status
        material_counts = (
            db.query(
                WeeklyMaterial.status,
                func.count(WeeklyMaterial.id),
            )
            .filter(WeeklyMaterial.unit_id == unit_id)
            .group_by(WeeklyMaterial.status)
            .all()
        )

        material_stats = {
            "total": sum(count for _, count in material_counts),
            "by_status": {
                (status.value if hasattr(status, "value") else status): count
                for status, count in material_counts
            },
        }

        # Count assessments by status
        assessment_counts = (
            db.query(
                Assessment.status,
                func.count(Assessment.id),
            )
            .filter(Assessment.unit_id == unit_id)
            .group_by(Assessment.status)
            .all()
        )

        assessment_stats = {
            "total": sum(count for _, count in assessment_counts),
            "by_status": {
                (status.value if hasattr(status, "value") else status): count
                for status, count in assessment_counts
            },
        }

        # Calculate total weight of assessments
        total_weight = (
            db.query(func.sum(Assessment.weight))
            .filter(
                and_(
                    Assessment.unit_id == unit_id,
                    Assessment.status != AssessmentStatus.ARCHIVED,
                )
            )
            .scalar()
        ) or 0.0

        # Count weeks with content
        weeks_with_content = (
            db.query(func.count(func.distinct(WeeklyMaterial.week_number)))
            .filter(WeeklyMaterial.unit_id == unit_id)
            .scalar()
        )

        return {
            "unit_id": str(unit_id),
            "ulo_count": ulo_count,
            "materials": material_stats,
            "assessments": assessment_stats,
            "total_assessment_weight": total_weight,
            "weeks_with_content": weeks_with_content,
            "last_updated": datetime.utcnow(),
        }

    async def get_unit_progress(
        self,
        db: Session,
        unit_id: UUID,
        include_details: bool = False,
    ) -> dict[str, Any]:
        """Get progress report for a unit"""
        # Count completed vs total items
        materials = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
        )

        assessments = db.query(Assessment).filter(Assessment.unit_id == unit_id).all()

        material_progress = {
            "total": len(materials),
            "published": sum(
                1 for m in materials if m.status == MaterialStatus.PUBLISHED
            ),
            "draft": sum(1 for m in materials if m.status == MaterialStatus.DRAFT),
            "completion_percentage": (
                (
                    sum(1 for m in materials if m.status == MaterialStatus.PUBLISHED)
                    / len(materials)
                    * 100
                )
                if materials
                else 0
            ),
        }

        assessment_progress = {
            "total": len(assessments),
            "published": sum(
                1 for a in assessments if a.status == AssessmentStatus.PUBLISHED
            ),
            "draft": sum(1 for a in assessments if a.status == AssessmentStatus.DRAFT),
            "completion_percentage": (
                (
                    sum(
                        1 for a in assessments if a.status == AssessmentStatus.PUBLISHED
                    )
                    / len(assessments)
                    * 100
                )
                if assessments
                else 0
            ),
        }

        progress = {
            "unit_id": str(unit_id),
            "materials": material_progress,
            "assessments": assessment_progress,
            "overall_completion": (
                (
                    material_progress["completion_percentage"]
                    + assessment_progress["completion_percentage"]
                )
                / 2
            ),
        }

        if include_details:
            progress["incomplete_items"] = {
                "materials": [
                    {"id": str(m.id), "title": m.title, "week": m.week_number}
                    for m in materials
                    if m.status != MaterialStatus.PUBLISHED
                ],
                "assessments": [
                    {"id": str(a.id), "title": a.title, "type": a.type}
                    for a in assessments
                    if a.status != AssessmentStatus.PUBLISHED
                ],
            }

        return progress

    async def get_completion_report(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Get completion status for all unit components"""
        # Check ULOs
        ulos = (
            db.query(UnitLearningOutcome)
            .filter(
                and_(
                    UnitLearningOutcome.unit_id == unit_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    UnitLearningOutcome.is_active.is_(True),
                )
            )
            .options(
                selectinload(UnitLearningOutcome.materials),
                selectinload(UnitLearningOutcome.assessments),
            )
            .all()
        )

        ulo_completion = [
            {
                "id": str(ulo.id),
                "code": ulo.outcome_code,
                "has_materials": len(ulo.materials) > 0,
                "has_assessments": len(ulo.assessments) > 0,
                "is_complete": len(ulo.materials) > 0 and len(ulo.assessments) > 0,
            }
            for ulo in ulos
        ]

        # Check weekly coverage
        weeks_with_materials = (
            db.query(WeeklyMaterial.week_number)
            .filter(WeeklyMaterial.unit_id == unit_id)
            .distinct()
            .all()
        )

        weeks_with_assessments = (
            db.query(Assessment.due_week)
            .filter(
                and_(
                    Assessment.unit_id == unit_id,
                    Assessment.due_week.isnot(None),
                )
            )
            .distinct()
            .all()
        )

        return {
            "unit_id": str(unit_id),
            "ulo_completion": ulo_completion,
            "ulos_fully_covered": sum(1 for u in ulo_completion if u["is_complete"]),
            "ulos_total": len(ulo_completion),
            "weeks_with_materials": sorted([w[0] for w in weeks_with_materials]),
            "weeks_with_assessments": sorted([w[0] for w in weeks_with_assessments]),
            "completion_percentage": (
                (
                    sum(1 for u in ulo_completion if u["is_complete"])
                    / len(ulo_completion)
                    * 100
                )
                if ulo_completion
                else 0
            ),
        }

    async def get_alignment_report(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Get learning outcome alignment report"""
        # Get all ULOs with their mappings
        ulos = (
            db.query(UnitLearningOutcome)
            .filter(
                and_(
                    UnitLearningOutcome.unit_id == unit_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    UnitLearningOutcome.is_active.is_(True),
                )
            )
            .options(
                selectinload(UnitLearningOutcome.materials),
                selectinload(UnitLearningOutcome.assessments),
            )
            .all()
        )

        alignment_data = [
            {
                "ulo_id": str(ulo.id),
                "ulo_code": ulo.outcome_code,
                "ulo_description": ulo.outcome_text,
                "bloom_level": ulo.bloom_level,
                "material_count": len(ulo.materials),
                "assessment_count": len(ulo.assessments),
                "material_ids": [str(m.id) for m in ulo.materials],
                "assessment_ids": [str(a.id) for a in ulo.assessments],
                "alignment_score": self._calculate_alignment_score(ulo),
            }
            for ulo in ulos
        ]

        # Calculate overall alignment metrics
        total_ulos = len(ulos)
        aligned_ulos = sum(
            1
            for a in alignment_data
            if int(a["material_count"]) > 0 and int(a["assessment_count"]) > 0
        )
        materials_only = sum(
            1
            for a in alignment_data
            if int(a["material_count"]) > 0 and int(a["assessment_count"]) == 0
        )
        assessments_only = sum(
            1
            for a in alignment_data
            if int(a["material_count"]) == 0 and int(a["assessment_count"]) > 0
        )
        unaligned = sum(
            1
            for a in alignment_data
            if int(a["material_count"]) == 0 and int(a["assessment_count"]) == 0
        )

        return {
            "unit_id": str(unit_id),
            "alignment_details": alignment_data,
            "summary": {
                "total_ulos": total_ulos,
                "fully_aligned": aligned_ulos,
                "materials_only": materials_only,
                "assessments_only": assessments_only,
                "unaligned": unaligned,
                "alignment_percentage": (aligned_ulos / total_ulos * 100)
                if total_ulos > 0
                else 0,
            },
            "recommendations": self._generate_alignment_recommendations(alignment_data),
        }

    async def get_weekly_workload(
        self,
        db: Session,
        unit_id: UUID,
        start_week: int = 1,
        end_week: int = 52,
    ) -> list[dict[str, Any]]:
        """Get weekly workload analysis"""
        workload = []

        for week in range(start_week, end_week + 1):
            # Get materials for the week
            materials = (
                db.query(WeeklyMaterial)
                .filter(
                    and_(
                        WeeklyMaterial.unit_id == unit_id,
                        WeeklyMaterial.week_number == week,
                    )
                )
                .all()
            )

            # Get assessments due this week
            assessments = (
                db.query(Assessment)
                .filter(
                    and_(
                        Assessment.unit_id == unit_id,
                        Assessment.due_week == week,
                    )
                )
                .all()
            )

            if materials or assessments:
                total_duration = sum(m.duration_minutes or 0 for m in materials)
                assessment_duration = sum(
                    int(a.duration) if a.duration and a.duration.isdigit() else 0
                    for a in assessments
                )

                workload.append(
                    {
                        "week_number": week,
                        "material_count": len(materials),
                        "material_duration_minutes": total_duration,
                        "assessment_count": len(assessments),
                        "assessment_duration_minutes": assessment_duration,
                        "total_duration_minutes": total_duration + assessment_duration,
                        "workload_hours": (total_duration + assessment_duration) / 60,
                        "materials": [
                            {
                                "id": str(m.id),
                                "title": m.title,
                                "duration": m.duration_minutes,
                            }
                            for m in materials
                        ],
                        "assessments": [
                            {"id": str(a.id), "title": a.title, "weight": a.weight}
                            for a in assessments
                        ],
                    }
                )

        return workload

    async def get_recommendations(
        self,
        db: Session,
        unit_id: UUID,
        source: str = "rules",
    ) -> dict[str, Any]:
        """Get recommendations for unit improvement"""
        # Gather data for analysis
        overview = await self.get_unit_overview(db, unit_id)
        alignment = await self.get_alignment_report(db, unit_id)
        workload = await self.get_weekly_workload(db, unit_id)

        recommendations = []

        # Check for unaligned ULOs
        if alignment["summary"]["unaligned"] > 0:
            recommendations.append(
                {
                    "category": "alignment",
                    "priority": "high",
                    "issue": f"{alignment['summary']['unaligned']} ULOs have no materials or assessments",
                    "suggestion": "Create materials and assessments for uncovered learning outcomes",
                }
            )

        # Check for uneven workload distribution
        workload_variance = self._calculate_workload_variance(workload)
        if workload_variance > 0.3:  # High variance threshold
            recommendations.append(
                {
                    "category": "workload",
                    "priority": "medium",
                    "issue": "Uneven workload distribution across weeks",
                    "suggestion": "Redistribute materials and assessments for more consistent weekly workload",
                }
            )

        # Check assessment weight total
        if overview["total_assessment_weight"] != 100.0:
            recommendations.append(
                {
                    "category": "assessment",
                    "priority": "high",
                    "issue": f"Assessment weights sum to {overview['total_assessment_weight']}%, not 100%",
                    "suggestion": "Adjust assessment weights to total exactly 100%",
                }
            )

        # Check for draft content
        draft_materials = overview["materials"]["by_status"].get("draft", 0)
        if draft_materials > 0:
            recommendations.append(
                {
                    "category": "content",
                    "priority": "medium",
                    "issue": f"{draft_materials} materials are still in draft status",
                    "suggestion": "Review and publish draft materials",
                }
            )

        result: dict[str, Any] = {
            "unit_id": str(unit_id),
            "recommendations": recommendations,
            "source": source,
            "generated_at": datetime.utcnow(),
        }

        if source == "llm":
            try:
                from app.services.llm_service import llm_service  # noqa: PLC0415

                metrics_summary = (
                    f"Unit has {overview['materials']['total']} materials, "
                    f"{overview['assessments']['total']} assessments, "
                    f"{alignment['summary']['total_ulos']} ULOs. "
                    f"Alignment: {alignment['summary']['alignment_percentage']:.0f}%. "
                    f"Unaligned ULOs: {alignment['summary']['unaligned']}. "
                    f"Assessment weight total: {overview['total_assessment_weight']}%. "
                    f"Weeks with content: {overview['weeks_with_content']}."
                )

                prompt = (
                    "You are an expert in university curriculum design. "
                    "Based on the following unit metrics, provide 3-5 specific, "
                    "actionable recommendations for improving quality.\n\n"
                    f"Metrics: {metrics_summary}\n\n"
                    "Return each recommendation as a single sentence. "
                    "Focus on pedagogical quality and constructive alignment."
                )

                llm_response = await llm_service.generate_text(
                    prompt, stream=False
                )
                assert isinstance(llm_response, str)
                llm_recs = [
                    line.strip().lstrip("0123456789.-) ")
                    for line in llm_response.split("\n")
                    if line.strip() and len(line.strip()) > 10
                ][:5]

                result["llm_recommendations"] = llm_recs
                result["model_name"] = "AI-generated"
            except Exception as e:
                logger.warning("LLM recommendations failed: %s", e)
                result["llm_recommendations"] = []
                result["llm_error"] = str(e)

        return result

    async def export_unit_data(
        self,
        db: Session,
        unit_id: UUID,
        export_format: str = "json",
    ) -> dict[str, Any]:
        """Export unit data in various formats"""
        # Gather all unit data
        overview = await self.get_unit_overview(db, unit_id)
        progress = await self.get_unit_progress(db, unit_id, include_details=True)
        alignment = await self.get_alignment_report(db, unit_id)
        workload = await self.get_weekly_workload(db, unit_id)

        export_data = {
            "unit_id": str(unit_id),
            "export_date": datetime.utcnow().isoformat(),
            "format": export_format,
            "data": {
                "overview": overview,
                "progress": progress,
                "alignment": alignment,
                "workload": workload,
            },
        }

        if export_format == "csv":
            # Format for CSV export (simplified structure)
            export_data["csv_ready"] = True
            export_data["notice"] = "CSV export would be handled by a separate service"
        elif export_format == "pdf":
            # Format for PDF export
            export_data["pdf_ready"] = True
            export_data["notice"] = (
                "PDF generation would be handled by a separate service"
            )

        return export_data

    async def calculate_quality_score(
        self,
        db: Session,
        unit_id: UUID,
        rating_method: str = "weighted_average",
        rating_config: dict[str, Any] | None = None,
        total_weeks: int = 12,
    ) -> dict[str, Any]:
        """Calculate quality score for a unit with 6 dimensions"""
        materials = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
        )
        alignment = await self.get_alignment_report(db, unit_id)
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

        # 1. Completeness: weeks with content + materials with descriptions
        weeks_with_content = len({m.week_number for m in materials})
        week_pct = (weeks_with_content / total_weeks * 100) if total_weeks > 0 else 0
        materials_with_desc = sum(1 for m in materials if m.description)
        desc_pct = (
            (materials_with_desc / len(materials) * 100) if materials else 0
        )
        completeness = week_pct * 0.5 + desc_pct * 0.5

        # 2. Content Quality: avg plugin quality_score across materials
        scored: list[int] = [
            int(qs)
            for m in materials
            if (qs := getattr(m, "quality_score", None)) is not None
        ]
        content_quality = sum(scored) / len(scored) if scored else 50.0

        # 3. ULO Alignment: from alignment report
        ulo_alignment = alignment["summary"]["alignment_percentage"]

        # 4. Workload Balance: 100 - CV*100
        weekly_durations: list[float] = []
        for week in range(1, total_weeks + 1):
            dur = sum(
                m.duration_minutes or 0
                for m in materials
                if m.week_number == week
            )
            weekly_durations.append(float(dur))
        workload_balance = self._calculate_balance_score(weekly_durations)

        # 5. Material Diversity: Shannon index on type distribution
        material_diversity = self._calculate_shannon_diversity(
            [str(m.type) for m in materials]
        )

        # 6. Assessment Distribution: spread of due_week across semester
        due_weeks = [a.due_week for a in assessments if a.due_week is not None]
        assessment_distribution = self._calculate_spread_score(
            due_weeks, total_weeks
        )

        sub_scores = {
            "completeness": round(completeness, 2),
            "contentQuality": round(content_quality, 2),
            "uloAlignment": round(ulo_alignment, 2),
            "workloadBalance": round(workload_balance, 2),
            "materialDiversity": round(material_diversity, 2),
            "assessmentDistribution": round(assessment_distribution, 2),
        }

        # Calculate overall score based on rating method
        weights = DEFAULT_QUALITY_WEIGHTS
        overall_score = sum(
            sub_scores[dim] * weights[dim] for dim in weights
        )
        star_rating = self._score_to_stars(overall_score)

        if rating_method == "lowest_dimension":
            min_score = min(sub_scores.values()) if sub_scores else 0
            star_rating = self._score_to_stars(min_score)
            overall_score = min_score
        elif rating_method == "threshold_based" and rating_config:
            thresholds = rating_config.get("thresholds", [20, 40, 60, 80, 90])
            star_rating = 0.0
            for threshold in sorted(thresholds):
                if all(v >= threshold for v in sub_scores.values()):
                    star_rating += 1.0
                else:
                    break

        return {
            "unit_id": str(unit_id),
            "overall_score": round(overall_score, 2),
            "star_rating": star_rating,
            "rating_method": rating_method,
            "sub_scores": sub_scores,
            "grade": self._score_to_grade(overall_score),
            "calculated_at": datetime.utcnow(),
        }

    async def calculate_weekly_quality(
        self,
        db: Session,
        unit_id: UUID,
        total_weeks: int = 12,
    ) -> list[dict[str, Any]]:
        """Calculate per-week quality scores"""
        materials = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
        )

        # Group materials by week
        by_week: dict[int, list[Any]] = {}
        for m in materials:
            by_week.setdefault(m.week_number, []).append(m)

        results = []
        for week in range(1, total_weeks + 1):
            week_materials = by_week.get(week, [])
            has_content = len(week_materials) > 0

            if not has_content:
                results.append(
                    {
                        "week_number": week,
                        "star_rating": 0.0,
                        "has_content": False,
                        "material_count": 0,
                        "type_diversity_score": 0.0,
                        "avg_quality_score": 0.0,
                        "total_duration_minutes": 0,
                    }
                )
                continue

            material_count = len(week_materials)
            type_diversity = self._calculate_shannon_diversity(
                [str(m.type) for m in week_materials]
            )
            scored: list[int] = [
                int(qs)
                for m in week_materials
                if (qs := getattr(m, "quality_score", None)) is not None
            ]
            avg_quality = sum(scored) / len(scored) if scored else 50.0
            total_duration = sum(m.duration_minutes or 0 for m in week_materials)

            # Simple week score: content exists + count + diversity + quality
            week_score = min(
                (min(material_count, 5) / 5 * 30)
                + (type_diversity * 0.3)
                + (avg_quality * 0.4),
                100.0,
            )

            results.append(
                {
                    "week_number": week,
                    "star_rating": self._score_to_stars(week_score),
                    "has_content": True,
                    "material_count": material_count,
                    "type_diversity_score": round(type_diversity, 2),
                    "avg_quality_score": round(avg_quality, 2),
                    "total_duration_minutes": total_duration,
                }
            )

        return results

    async def calculate_batch_quality_scores(
        self,
        db: Session,
        unit_ids: list[UUID],
    ) -> dict[str, float]:
        """Calculate star ratings for multiple units (lightweight)"""
        result: dict[str, float] = {}
        for uid in unit_ids:
            try:
                quality = await self.calculate_quality_score(db, uid)
                result[str(uid)] = quality["star_rating"]
            except Exception:
                logger.warning("Failed to calculate quality for unit %s", uid)
                result[str(uid)] = 0.0
        return result

    async def validate_unit(
        self,
        db: Session,
        unit_id: UUID,
        strict_mode: bool = False,
    ) -> dict[str, Any]:
        """Validate unit structure and content"""
        errors = []
        warnings = []

        # Check for ULOs
        ulo_count = (
            db.query(func.count(UnitLearningOutcome.id))
            .filter(
                and_(
                    UnitLearningOutcome.unit_id == unit_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    UnitLearningOutcome.is_active.is_(True),
                )
            )
            .scalar()
        )

        if ulo_count == 0:
            errors.append("No Unit Learning Outcomes defined")
        elif ulo_count < 3 and strict_mode:
            warnings.append(f"Only {ulo_count} ULOs defined (recommended: 3-8)")

        # Check assessment weights
        total_weight = (
            db.query(func.sum(Assessment.weight))
            .filter(Assessment.unit_id == unit_id)
            .scalar()
        ) or 0.0

        if total_weight != 100.0:
            errors.append(f"Assessment weights sum to {total_weight}%, not 100%")

        # Check for materials
        material_count = (
            db.query(func.count(WeeklyMaterial.id))
            .filter(WeeklyMaterial.unit_id == unit_id)
            .scalar()
        )

        if material_count == 0:
            errors.append("No weekly materials defined")

        # Check for assessments
        assessment_count = (
            db.query(func.count(Assessment.id))
            .filter(Assessment.unit_id == unit_id)
            .scalar()
        )

        if assessment_count == 0:
            errors.append("No assessments defined")

        # Check for orphaned outcomes
        alignment = await self.get_alignment_report(db, unit_id)
        if alignment["summary"]["unaligned"] > 0:
            warnings.append(
                f"{alignment['summary']['unaligned']} ULOs have no coverage"
            )

        return {
            "unit_id": str(unit_id),
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "strict_mode": strict_mode,
            "validated_at": datetime.utcnow(),
        }

    async def get_unit_statistics(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Get detailed statistics for a unit"""
        # Material statistics
        materials = (
            db.query(WeeklyMaterial).filter(WeeklyMaterial.unit_id == unit_id).all()
        )

        # Count by type and week
        by_type: dict[str, int] = {}
        by_week: dict[str, int] = {}

        for material in materials:
            type_key = str(material.type)
            by_type[type_key] = by_type.get(type_key, 0) + 1
            week_key = f"week_{material.week_number}"
            by_week[week_key] = by_week.get(week_key, 0) + 1

        material_stats = {
            "total": len(materials),
            "by_type": by_type,
            "by_week": by_week,
            "total_duration_hours": sum(m.duration_minutes or 0 for m in materials)
            / 60,
            "average_duration_minutes": (
                sum(m.duration_minutes or 0 for m in materials) / len(materials)
                if materials
                else 0
            ),
        }

        # Assessment statistics
        assessments = db.query(Assessment).filter(Assessment.unit_id == unit_id).all()

        # Count assessments by type and category
        assessment_by_type: dict[str, int] = {}
        assessment_by_category: dict[str, int] = {}

        for assessment in assessments:
            type_key = str(assessment.type)
            assessment_by_type[type_key] = assessment_by_type.get(type_key, 0) + 1
            category_key = str(assessment.category)
            assessment_by_category[category_key] = (
                assessment_by_category.get(category_key, 0) + 1
            )

        assessment_stats = {
            "total": len(assessments),
            "by_type": assessment_by_type,
            "by_category": assessment_by_category,
            "total_weight": sum(a.weight for a in assessments),
            "average_weight": sum(a.weight for a in assessments) / len(assessments)
            if assessments
            else 0,
        }

        # ULO statistics
        ulos = (
            db.query(UnitLearningOutcome)
            .filter(
                and_(
                    UnitLearningOutcome.unit_id == unit_id,
                    UnitLearningOutcome.outcome_type == OutcomeType.ULO,
                    UnitLearningOutcome.is_active.is_(True),
                )
            )
            .all()
        )

        bloom_distribution = {}
        for ulo in ulos:
            bloom_distribution[ulo.bloom_level] = (
                bloom_distribution.get(ulo.bloom_level, 0) + 1
            )

        return {
            "unit_id": str(unit_id),
            "materials": material_stats,
            "assessments": assessment_stats,
            "learning_outcomes": {
                "total_ulos": len(ulos),
                "bloom_distribution": bloom_distribution,
            },
            "generated_at": datetime.utcnow(),
        }

    def _calculate_alignment_score(self, ulo: UnitLearningOutcome) -> float:
        """Calculate alignment score for a single ULO"""
        material_score = min(len(ulo.materials) / 3, 1.0) * 50  # Up to 50 points
        assessment_score = min(len(ulo.assessments) / 2, 1.0) * 50  # Up to 50 points
        return material_score + assessment_score

    def _generate_alignment_recommendations(
        self, alignment_data: list[dict]
    ) -> list[str]:
        """Generate recommendations based on alignment data"""
        recommendations = []

        for item in alignment_data:
            if item["material_count"] == 0:
                recommendations.append(
                    f"ULO {item['ulo_code']}: Add materials to cover this outcome"
                )
            if item["assessment_count"] == 0:
                recommendations.append(
                    f"ULO {item['ulo_code']}: Add assessments to evaluate this outcome"
                )

        return recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_workload_variance(self, workload: list[dict]) -> float:
        """Calculate variance in weekly workload"""
        if not workload:
            return 0.0

        durations = [w["total_duration_minutes"] for w in workload]
        if not durations:
            return 0.0

        mean = sum(durations) / len(durations)
        variance = sum((x - mean) ** 2 for x in durations) / len(durations)
        return variance / (mean**2) if mean > 0 else 0.0

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    @staticmethod
    def _score_to_stars(score: float) -> float:
        """Convert 0-100 score to 0-5 star rating"""
        thresholds = [
            (95, 5.0),
            (90, 4.5),
            (85, 4.0),
            (80, 3.5),
            (70, 3.0),
            (55, 2.5),
            (40, 2.0),
            (20, 1.0),
        ]
        for threshold, stars in thresholds:
            if score >= threshold:
                return stars
        return 0.0

    @staticmethod
    def _calculate_balance_score(values: list[float]) -> float:
        """Calculate balance score (100 = perfectly even, 0 = maximally uneven)"""
        non_zero = [v for v in values if v > 0]
        if len(non_zero) < 2:
            return 50.0  # Not enough data
        mean = sum(non_zero) / len(non_zero)
        if mean == 0:
            return 50.0
        std_dev = math.sqrt(sum((x - mean) ** 2 for x in non_zero) / len(non_zero))
        cv = std_dev / mean
        return max(0.0, min(100.0, 100.0 - cv * 100.0))

    @staticmethod
    def _calculate_shannon_diversity(items: list[str]) -> float:
        """Shannon diversity index normalized to 0-100"""
        if not items:
            return 0.0
        counts = Counter(items)
        total = len(items)
        num_types = len(counts)
        if num_types <= 1:
            return 0.0 if total <= 1 else 20.0  # Single type gets baseline

        entropy = -sum(
            (c / total) * math.log(c / total) for c in counts.values() if c > 0
        )
        max_entropy = math.log(num_types)
        evenness = entropy / max_entropy if max_entropy > 0 else 0
        return round(evenness * 100.0, 2)

    @staticmethod
    def _calculate_spread_score(
        values: list[int], total_slots: int
    ) -> float:
        """Score how evenly values are spread across slots (0-100)"""
        if not values:
            return 0.0
        if len(values) == 1:
            return 50.0  # Single item can't be "spread"

        unique = sorted(set(values))
        if len(unique) == 1:
            return 0.0  # All in same slot

        # Calculate gaps between consecutive items
        gaps = [unique[i + 1] - unique[i] for i in range(len(unique) - 1)]
        ideal_gap = total_slots / (len(unique) + 1)
        if ideal_gap == 0:
            return 50.0

        mean_gap = sum(gaps) / len(gaps)
        deviation = abs(mean_gap - ideal_gap) / ideal_gap
        # Also reward using more of the semester range
        range_coverage = (unique[-1] - unique[0]) / total_slots
        return max(0.0, min(100.0, (1.0 - deviation * 0.5) * 50 + range_coverage * 50))


# Create singleton instance
analytics_service = AnalyticsService()
