"""
API routes for course structure (outline, outcomes, topics, assessments)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models import (
    AssessmentPlan,
    UnitLearningOutcome,
    UnitOutline,
    WeeklyTopic,
)

router = APIRouter()


@router.get(
    "/units/{unit_id}/structure",
    dependencies=[Depends(deps.get_user_unit)],
)
async def get_course_structure(
    unit_id: str,
    db: Session = Depends(deps.get_db),
):
    """
    Get complete course structure including outline, outcomes, topics, and assessments
    """
    # Get course outline
    outline = db.query(UnitOutline).filter(UnitOutline.unit_id == unit_id).first()

    if not outline:
        return {
            "outline": None,
            "learning_outcomes": [],
            "weekly_topics": [],
            "assessments": [],
        }

    # Get learning outcomes
    learning_outcomes = (
        db.query(UnitLearningOutcome)
        .filter(UnitLearningOutcome.unit_id == unit_id)
        .order_by(UnitLearningOutcome.sequence_order)
        .all()
    )

    # Get weekly topics
    weekly_topics = (
        db.query(WeeklyTopic)
        .filter(WeeklyTopic.unit_id == unit_id)
        .order_by(WeeklyTopic.week_number)
        .all()
    )

    # Get assessments
    assessments = (
        db.query(AssessmentPlan)
        .filter(AssessmentPlan.unit_id == unit_id)
        .order_by(AssessmentPlan.due_week)
        .all()
    )

    return {
        "outline": {
            "id": str(outline.id),
            "title": outline.title,
            "description": outline.description,
            "duration_weeks": outline.duration_weeks,
            "delivery_mode": outline.delivery_mode,
            "teaching_pattern": outline.teaching_pattern,
            "is_complete": outline.is_complete,
            "completion_percentage": outline.completion_percentage,
        },
        "learning_outcomes": [
            {
                "id": str(lo.id),
                "outcome_code": lo.outcome_code,
                "outcome_text": lo.outcome_text,
                "outcome_type": lo.outcome_type,
                "bloom_level": lo.bloom_level,
            }
            for lo in learning_outcomes
        ],
        "weekly_topics": [
            {
                "id": str(topic.id),
                "week_number": topic.week_number,
                "week_type": topic.week_type,
                "topic_title": topic.topic_title,
                "topic_description": topic.topic_description,
                "learning_objectives": topic.learning_objectives,
                "pre_class_modules": topic.pre_class_modules,
                "in_class_activities": topic.in_class_activities,
                "post_class_tasks": topic.post_class_tasks,
                "required_readings": topic.required_readings,
            }
            for topic in weekly_topics
        ],
        "assessments": [
            {
                "id": str(assessment.id),
                "assessment_name": assessment.assessment_name,
                "assessment_type": assessment.assessment_type,
                "assessment_mode": assessment.assessment_mode,
                "weight_percentage": assessment.weight_percentage,
                "due_week": assessment.due_week,
                "description": assessment.description,
            }
            for assessment in assessments
        ],
    }


@router.delete(
    "/units/{unit_id}/structure",
    dependencies=[Depends(deps.get_user_unit)],
)
async def delete_unit_structure(
    unit_id: str,
    db: Session = Depends(deps.get_db),
):
    """
    Delete unit structure (for testing/reset purposes)
    """
    # Delete in correct order due to foreign key constraints
    db.query(AssessmentPlan).filter(AssessmentPlan.unit_id == unit_id).delete()
    db.query(WeeklyTopic).filter(WeeklyTopic.unit_id == unit_id).delete()
    db.query(UnitLearningOutcome).filter(
        UnitLearningOutcome.unit_id == unit_id
    ).delete()
    db.query(UnitOutline).filter(UnitOutline.unit_id == unit_id).delete()

    db.commit()

    return {"status": "success", "message": "Course structure deleted"}
