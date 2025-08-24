"""
Service for analytics and reporting
"""

import logging
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
            "by_status": {status.value: count for status, count in material_counts},
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
            "by_status": {status.value: count for status, count in assessment_counts},
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
        materials = db.query(WeeklyMaterial).filter(
            WeeklyMaterial.unit_id == unit_id
        ).all()

        assessments = db.query(Assessment).filter(
            Assessment.unit_id == unit_id
        ).all()

        material_progress = {
            "total": len(materials),
            "published": sum(1 for m in materials if m.status == MaterialStatus.PUBLISHED),
            "draft": sum(1 for m in materials if m.status == MaterialStatus.DRAFT),
            "completion_percentage": (
                (sum(1 for m in materials if m.status == MaterialStatus.PUBLISHED) / len(materials) * 100)
                if materials else 0
            ),
        }

        assessment_progress = {
            "total": len(assessments),
            "published": sum(1 for a in assessments if a.status == AssessmentStatus.PUBLISHED),
            "draft": sum(1 for a in assessments if a.status == AssessmentStatus.DRAFT),
            "completion_percentage": (
                (sum(1 for a in assessments if a.status == AssessmentStatus.PUBLISHED) / len(assessments) * 100)
                if assessments else 0
            ),
        }

        progress = {
            "unit_id": str(unit_id),
            "materials": material_progress,
            "assessments": assessment_progress,
            "overall_completion": (
                (material_progress["completion_percentage"] + assessment_progress["completion_percentage"]) / 2
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
                (sum(1 for u in ulo_completion if u["is_complete"]) / len(ulo_completion) * 100)
                if ulo_completion else 0
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
        aligned_ulos = sum(1 for a in alignment_data if int(a["material_count"]) > 0 and int(a["assessment_count"]) > 0)
        materials_only = sum(1 for a in alignment_data if int(a["material_count"]) > 0 and int(a["assessment_count"]) == 0)
        assessments_only = sum(1 for a in alignment_data if int(a["material_count"]) == 0 and int(a["assessment_count"]) > 0)
        unaligned = sum(1 for a in alignment_data if int(a["material_count"]) == 0 and int(a["assessment_count"]) == 0)

        return {
            "unit_id": str(unit_id),
            "alignment_details": alignment_data,
            "summary": {
                "total_ulos": total_ulos,
                "fully_aligned": aligned_ulos,
                "materials_only": materials_only,
                "assessments_only": assessments_only,
                "unaligned": unaligned,
                "alignment_percentage": (aligned_ulos / total_ulos * 100) if total_ulos > 0 else 0,
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
                assessment_duration = sum(a.duration or 0 for a in assessments)

                workload.append({
                    "week_number": week,
                    "material_count": len(materials),
                    "material_duration_minutes": total_duration,
                    "assessment_count": len(assessments),
                    "assessment_duration_minutes": assessment_duration,
                    "total_duration_minutes": total_duration + assessment_duration,
                    "workload_hours": (total_duration + assessment_duration) / 60,
                    "materials": [
                        {"id": str(m.id), "title": m.title, "duration": m.duration_minutes}
                        for m in materials
                    ],
                    "assessments": [
                        {"id": str(a.id), "title": a.title, "weight": a.weight}
                        for a in assessments
                    ],
                })

        return workload

    async def get_recommendations(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Get AI-generated recommendations for unit improvement"""
        # Gather data for analysis
        overview = await self.get_unit_overview(db, unit_id)
        alignment = await self.get_alignment_report(db, unit_id)
        workload = await self.get_weekly_workload(db, unit_id)

        recommendations = []

        # Check for unaligned ULOs
        if alignment["summary"]["unaligned"] > 0:
            recommendations.append({
                "category": "alignment",
                "priority": "high",
                "issue": f"{alignment['summary']['unaligned']} ULOs have no materials or assessments",
                "suggestion": "Create materials and assessments for uncovered learning outcomes",
            })

        # Check for uneven workload distribution
        workload_variance = self._calculate_workload_variance(workload)
        if workload_variance > 0.3:  # High variance threshold
            recommendations.append({
                "category": "workload",
                "priority": "medium",
                "issue": "Uneven workload distribution across weeks",
                "suggestion": "Redistribute materials and assessments for more consistent weekly workload",
            })

        # Check assessment weight total
        if overview["total_assessment_weight"] != 100.0:
            recommendations.append({
                "category": "assessment",
                "priority": "high",
                "issue": f"Assessment weights sum to {overview['total_assessment_weight']}%, not 100%",
                "suggestion": "Adjust assessment weights to total exactly 100%",
            })

        # Check for draft content
        draft_materials = overview["materials"]["by_status"].get("draft", 0)
        if draft_materials > 0:
            recommendations.append({
                "category": "content",
                "priority": "medium",
                "issue": f"{draft_materials} materials are still in draft status",
                "suggestion": "Review and publish draft materials",
            })

        return {
            "unit_id": str(unit_id),
            "recommendations": recommendations,
            "generated_at": datetime.utcnow(),
        }

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
            export_data["notice"] = "PDF generation would be handled by a separate service"

        return export_data

    async def calculate_quality_score(
        self,
        db: Session,
        unit_id: UUID,
    ) -> dict[str, Any]:
        """Calculate quality score for a unit"""
        # Get various metrics
        overview = await self.get_unit_overview(db, unit_id)
        alignment = await self.get_alignment_report(db, unit_id)
        completion = await self.get_completion_report(db, unit_id)

        # Calculate sub-scores
        alignment_score = alignment["summary"]["alignment_percentage"]
        completion_score = completion["completion_percentage"]
        weight_score = 100.0 if overview["total_assessment_weight"] == 100.0 else 0.0

        # Calculate overall quality score (weighted average)
        quality_score = (
            alignment_score * 0.4 +  # 40% weight for alignment
            completion_score * 0.3 +  # 30% weight for completion
            weight_score * 0.3  # 30% weight for proper assessment weights
        )

        return {
            "unit_id": str(unit_id),
            "overall_score": round(quality_score, 2),
            "sub_scores": {
                "alignment": round(alignment_score, 2),
                "completion": round(completion_score, 2),
                "assessment_weights": round(weight_score, 2),
            },
            "grade": self._score_to_grade(quality_score),
            "calculated_at": datetime.utcnow(),
        }

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
            warnings.append(f"{alignment['summary']['unaligned']} ULOs have no coverage")

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
        materials = db.query(WeeklyMaterial).filter(
            WeeklyMaterial.unit_id == unit_id
        ).all()

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
            "total_duration_hours": sum(m.duration_minutes or 0 for m in materials) / 60,
            "average_duration_minutes": (
                sum(m.duration_minutes or 0 for m in materials) / len(materials)
                if materials else 0
            ),
        }

        # Assessment statistics
        assessments = db.query(Assessment).filter(
            Assessment.unit_id == unit_id
        ).all()

        # Count assessments by type and category
        assessment_by_type: dict[str, int] = {}
        assessment_by_category: dict[str, int] = {}

        for assessment in assessments:
            type_key = str(assessment.type)
            assessment_by_type[type_key] = assessment_by_type.get(type_key, 0) + 1
            category_key = str(assessment.category)
            assessment_by_category[category_key] = assessment_by_category.get(category_key, 0) + 1

        assessment_stats = {
            "total": len(assessments),
            "by_type": assessment_by_type,
            "by_category": assessment_by_category,
            "total_weight": sum(a.weight for a in assessments),
            "average_weight": sum(a.weight for a in assessments) / len(assessments) if assessments else 0,
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
            bloom_distribution[ulo.bloom_level] = bloom_distribution.get(ulo.bloom_level, 0) + 1

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

    def _generate_alignment_recommendations(self, alignment_data: list[dict]) -> list[str]:
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
        return variance / (mean ** 2) if mean > 0 else 0.0

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


# Create singleton instance
analytics_service = AnalyticsService()
