"""
API routes for course structure (outline, outcomes, topics, assessments)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import (
    AssessmentPlan,
    # Course,  # Removed - using Unit model
    CourseOutline,
    Unit,
    UnitLearningOutcome,
    User,
    WeeklyTopic,
)

router = APIRouter()


@router.get("/courses/{course_id}/structure")
async def get_course_structure(
    course_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get complete course structure including outline, outcomes, topics, and assessments
    """
    # For now, we'll treat course_id as unit_id since that's what our models use
    # In the future, we should properly link courses and units

    # Check if user has access to this course/unit
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        # Try to find as a unit
        unit = db.query(Unit).filter(
            Unit.id == course_id,
            Unit.owner_id == current_user.id
        ).first()

        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or access denied"
            )
        unit_id = unit.id
    else:
        # For now, use course_id as unit_id
        unit_id = course_id

    # Get course outline
    outline = db.query(CourseOutline).filter(
        CourseOutline.unit_id == unit_id
    ).first()

    if not outline:
        return {
            "outline": None,
            "learning_outcomes": [],
            "weekly_topics": [],
            "assessments": []
        }

    # Get learning outcomes
    learning_outcomes = db.query(UnitLearningOutcome).filter(
        UnitLearningOutcome.unit_id == unit_id
    ).order_by(UnitLearningOutcome.sequence_order).all()

    # Get weekly topics
    weekly_topics = db.query(WeeklyTopic).filter(
        WeeklyTopic.unit_id == unit_id
    ).order_by(WeeklyTopic.week_number).all()

    # Get assessments
    assessments = db.query(AssessmentPlan).filter(
        AssessmentPlan.unit_id == unit_id
    ).order_by(AssessmentPlan.due_week).all()

    return {
        "outline": {
            "id": str(outline.id),
            "title": outline.title,
            "description": outline.description,
            "duration_weeks": outline.duration_weeks,
            "delivery_mode": outline.delivery_mode,
            "teaching_pattern": outline.teaching_pattern,
            "is_complete": outline.is_complete,
            "completion_percentage": outline.completion_percentage
        },
        "learning_outcomes": [
            {
                "id": str(lo.id),
                "outcome_code": lo.outcome_code,
                "outcome_text": lo.outcome_text,
                "outcome_type": lo.outcome_type,
                "bloom_level": lo.bloom_level
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
                "required_readings": topic.required_readings
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
                "description": assessment.description
            }
            for assessment in assessments
        ]
    }


@router.delete("/courses/{course_id}/structure")
async def delete_course_structure(
    course_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete course structure (for testing/reset purposes)
    """
    # Check access
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        unit = db.query(Unit).filter(
            Unit.id == course_id,
            Unit.owner_id == current_user.id
        ).first()

        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or access denied"
            )
        unit_id = unit.id
    else:
        unit_id = course_id

    # Delete in correct order due to foreign key constraints
    db.query(AssessmentPlan).filter(AssessmentPlan.unit_id == unit_id).delete()
    db.query(WeeklyTopic).filter(WeeklyTopic.unit_id == unit_id).delete()
    db.query(UnitLearningOutcome).filter(UnitLearningOutcome.unit_id == unit_id).delete()
    db.query(CourseOutline).filter(CourseOutline.unit_id == unit_id).delete()

    db.commit()

    return {"status": "success", "message": "Course structure deleted"}
