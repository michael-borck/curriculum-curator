"""
API routes for guided content creation workflow
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import User, WorkflowChatSession, WorkflowStage
from app.schemas.course_structure import ChatSessionResponse, ChatWorkflowStatus
from app.services.content_workflow_service import ContentWorkflowService

router = APIRouter()


@router.post("/workflow/sessions/create/{unit_id}")
async def create_workflow_session(
    unit_id: str,
    session_name: str | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new guided content creation workflow session

    This starts an interactive workflow that guides users through:
    1. Initial planning (unit type, student level, delivery mode)
    2. Learning design (pedagogy, outcomes, Bloom's levels)
    3. Content structuring (organization, weekly patterns)
    4. Assessment planning (strategy, types, formative/summative)
    5. Material generation (automated creation based on decisions)
    """
    try:
        workflow_service = ContentWorkflowService(db)
        session = await workflow_service.create_workflow_session(
            unit_id=unit_id,
            user_id=str(current_user.id),
            session_name=session_name,
        )

        # Get first question
        first_question = await workflow_service.get_next_question(
            session_id=str(session.id),
            user_id=str(current_user.id),
        )

        return {
            "status": "created",
            "session": {
                "id": str(session.id),
                "name": session.session_name,
                "unit_id": unit_id,
                "status": session.status,
                "current_stage": session.current_stage,
                "progress": session.progress_percentage,
            },
            "next_question": first_question,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating workflow session: {str(e)}",
        )


@router.get("/workflow/sessions/{session_id}/status")
async def get_workflow_status(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get current status and progress of a workflow session"""
    try:
        workflow_service = ContentWorkflowService(db)
        status_data = await workflow_service.get_workflow_status(
            session_id=session_id,
            user_id=str(current_user.id),
        )

        return status_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/workflow/sessions/{session_id}/next-question")
async def get_next_question(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get the next question in the workflow"""
    try:
        workflow_service = ContentWorkflowService(db)
        question = await workflow_service.get_next_question(
            session_id=session_id,
            user_id=str(current_user.id),
        )

        if question:
            return {"status": "question_available", "question": question}
        else:
            # Check if workflow is complete or stage needs advancement
            status_data = await workflow_service.get_workflow_status(
                session_id=session_id,
                user_id=str(current_user.id),
            )

            return {
                "status": "no_questions",
                "workflow_status": status_data["status"],
                "current_stage": status_data["current_stage"],
                "can_generate": status_data["can_generate_structure"],
            }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/workflow/sessions/{session_id}/answer")
async def submit_workflow_answer(
    session_id: str,
    question_key: str,
    answer: Any,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Submit an answer to a workflow question

    The workflow will:
    1. Record the decision
    2. Update progress
    3. Advance to next question or stage
    4. Generate summaries when stages complete
    """
    try:
        workflow_service = ContentWorkflowService(db)
        result = await workflow_service.submit_answer(
            session_id=session_id,
            user_id=str(current_user.id),
            question_key=question_key,
            answer=answer,
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/workflow/sessions/{session_id}/generate-structure")
async def generate_course_structure(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Generate course structure based on workflow decisions

    This creates:
    - Course outline with description
    - Learning outcomes based on pedagogy choices
    - Weekly topics following the selected pattern
    - Assessment plan matching the chosen strategy
    """
    try:
        workflow_service = ContentWorkflowService(db)
        result = await workflow_service.generate_course_structure(
            session_id=session_id,
            user_id=str(current_user.id),
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating course structure: {str(e)}",
        )


@router.get("/workflow/stages")
async def get_workflow_stages(
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get all workflow stages and their descriptions"""
    stages = [
        {
            "stage": WorkflowStage.INITIAL_PLANNING,
            "name": "Initial Planning",
            "description": "Define unit type, student level, and delivery mode",
            "order": 1,
        },
        {
            "stage": WorkflowStage.LEARNING_DESIGN,
            "name": "Learning Design",
            "description": "Set pedagogical approach and learning outcomes",
            "order": 2,
        },
        {
            "stage": WorkflowStage.CONTENT_STRUCTURING,
            "name": "Content Structuring",
            "description": "Organize content and weekly patterns",
            "order": 3,
        },
        {
            "stage": WorkflowStage.ASSESSMENT_PLANNING,
            "name": "Assessment Planning",
            "description": "Design assessment strategy and tasks",
            "order": 4,
        },
        {
            "stage": WorkflowStage.MATERIAL_GENERATION,
            "name": "Material Generation",
            "description": "Generate course materials based on decisions",
            "order": 5,
        },
    ]

    return {"stages": stages}


@router.get("/workflow/stages/{stage}/questions")
async def get_stage_questions(
    stage: WorkflowStage,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get all questions for a specific workflow stage"""
    try:
        workflow_service = ContentWorkflowService(db)
        questions = await workflow_service.get_stage_questions(stage)

        return {
            "stage": stage,
            "questions": questions,
            "question_count": len(questions),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stage questions: {str(e)}",
        )


@router.get("/workflow/sessions")
async def list_workflow_sessions(
    skip: int = 0,
    limit: int = 20,
    include_completed: bool = True,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all workflow sessions for the current user"""
    query = db.query(WorkflowChatSession).filter(
        WorkflowChatSession.user_id == current_user.id
    )

    if not include_completed:
        query = query.filter(WorkflowChatSession.status != "completed")

    total = query.count()
    sessions = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "sessions": [
            {
                "id": str(session.id),
                "name": session.session_name,
                "unit_id": str(session.unit_id) if session.unit_id else None,
                "status": session.status,
                "current_stage": session.current_stage,
                "progress": session.progress_percentage,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": session.message_count,
            }
            for session in sessions
        ],
    }


@router.delete("/workflow/sessions/{session_id}")
async def delete_workflow_session(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Delete a workflow session"""
    session = (
        db.query(WorkflowChatSession)
        .filter(
            WorkflowChatSession.id == session_id,
            WorkflowChatSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    db.delete(session)
    db.commit()

    return {"status": "deleted", "message": "Workflow session deleted successfully"}


@router.post("/workflow/sessions/{session_id}/reset")
async def reset_workflow_session(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Reset a workflow session to start over"""
    session = (
        db.query(WorkflowChatSession)
        .filter(
            WorkflowChatSession.id == session_id,
            WorkflowChatSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Reset session
    session.status = "active"
    session.current_stage = WorkflowStage.INITIAL_PLANNING
    session.progress_percentage = 0.0
    session.decisions_made = {}
    session.chat_history = []
    session.message_count = 0
    session.workflow_data = {
        "reset_at": session.updated_at.isoformat(),
        "unit_id": str(session.unit_id) if session.unit_id else None,
    }

    db.commit()

    # Get first question
    workflow_service = ContentWorkflowService(db)
    first_question = await workflow_service.get_next_question(
        session_id=str(session.id),
        user_id=str(current_user.id),
    )

    return {
        "status": "reset",
        "message": "Workflow session reset successfully",
        "next_question": first_question,
    }