"""
LRD (Learning Requirements Document) API routes
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import LRD, Course, TaskList, TaskStatus, User, UserRole
from app.models.lrd import LRDStatus
from app.schemas.lrd import (
    ApprovalRecord,
    GeneratedTasks,
    LRDApproval,
    LRDCreate,
    LRDListResponse,
    LRDResponse,
    LRDUpdate,
    TaskGeneration,
)

router = APIRouter()


@router.get("/", response_model=LRDListResponse)
async def get_lrds(
    course_id: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get all LRDs accessible to the current user.
    Regular users see only their course LRDs, admins see all.
    """
    # Base query - join with courses to check ownership
    query = db.query(LRD).join(Course, LRD.course_id == Course.id)

    # Apply access control
    if current_user.role != UserRole.ADMIN.value:
        query = query.filter(Course.user_id == current_user.id)

    # Apply filters
    if course_id:
        query = query.filter(LRD.course_id == course_id)
    if status:
        query = query.filter(LRD.status == status)

    # Get total count
    total = query.count()

    # Apply pagination
    lrds = query.offset(skip).limit(limit).all()

    return LRDListResponse(
        lrds=[
            LRDResponse(
                id=str(lrd.id),
                course_id=str(lrd.course_id),
                version=lrd.version,
                status=lrd.status,
                content=lrd.content,
                created_at=lrd.created_at,
                updated_at=lrd.updated_at,
                approval_history=lrd.approval_history or [],
                task_lists=[],  # Will be populated when we implement task lists
            )
            for lrd in lrds
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{lrd_id}", response_model=LRDResponse)
async def get_lrd(
    lrd_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a specific LRD by ID.
    User must own the associated course or be an admin.
    """
    # Get LRD with ownership check
    query = db.query(LRD).join(Course, LRD.course_id == Course.id).filter(LRD.id == lrd_id)

    if current_user.role != UserRole.ADMIN.value:
        query = query.filter(Course.user_id == current_user.id)

    lrd = query.first()

    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found or access denied",
        )

    # Get associated task lists
    task_lists = db.query(TaskList).filter(TaskList.lrd_id == lrd.id).all()

    return LRDResponse(
        id=str(lrd.id),
        course_id=str(lrd.course_id),
        version=lrd.version,
        status=lrd.status,
        content=lrd.content,
        created_at=lrd.created_at,
        updated_at=lrd.updated_at,
        approval_history=lrd.approval_history or [],
        task_lists=[{"id": str(tl.id), "status": tl.status} for tl in task_lists],
    )


@router.post("/", response_model=LRDResponse)
async def create_lrd(
    lrd_data: LRDCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new LRD for a course.
    User must own the course.
    """
    # Verify user owns the course
    course = (
        db.query(Course)
        .filter(Course.id == lrd_data.course_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    # Check if course already has an active LRD
    existing_lrd = (
        db.query(LRD)
        .filter(LRD.course_id == lrd_data.course_id)
        .filter(LRD.status.in_([LRDStatus.DRAFT.value, LRDStatus.APPROVED.value]))
        .first()
    )

    if existing_lrd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course already has an active LRD. Archive it first to create a new one.",
        )

    # Create new LRD
    new_lrd = LRD(
        id=uuid.uuid4(),
        course_id=lrd_data.course_id,
        version=lrd_data.version,
        status=lrd_data.status.value,
        content=lrd_data.content.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        approval_history=[],
    )

    db.add(new_lrd)
    db.commit()
    db.refresh(new_lrd)

    return LRDResponse(
        id=str(new_lrd.id),
        course_id=str(new_lrd.course_id),
        version=new_lrd.version,
        status=new_lrd.status,
        content=new_lrd.content,
        created_at=new_lrd.created_at,
        updated_at=new_lrd.updated_at,
        approval_history=[],
        task_lists=[],
    )


@router.put("/{lrd_id}", response_model=LRDResponse)
async def update_lrd(
    lrd_id: str,
    lrd_data: LRDUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update an LRD.
    Only draft LRDs can be updated. User must own the course.
    """
    # Get LRD with ownership check
    lrd = (
        db.query(LRD)
        .join(Course, LRD.course_id == Course.id)
        .filter(LRD.id == lrd_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found or access denied",
        )

    # Only draft LRDs can be updated
    if lrd.status != LRDStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft LRDs can be updated",
        )

    # Update fields if provided
    if lrd_data.content:
        lrd.content = lrd_data.content.model_dump()
    if lrd_data.status:
        lrd.status = lrd_data.status.value

    lrd.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(lrd)

    return LRDResponse(
        id=str(lrd.id),
        course_id=str(lrd.course_id),
        version=lrd.version,
        status=lrd.status,
        content=lrd.content,
        created_at=lrd.created_at,
        updated_at=lrd.updated_at,
        approval_history=lrd.approval_history or [],
        task_lists=[],
    )


@router.post("/{lrd_id}/approve", response_model=LRDResponse)
async def approve_lrd(
    lrd_id: str,
    approval: LRDApproval,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Approve or reject an LRD.
    User must own the course or be an admin.
    """
    # Get LRD
    lrd = db.query(LRD).filter(LRD.id == lrd_id).first()

    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found",
        )

    # Check permissions
    course = db.query(Course).filter(Course.id == lrd.course_id).first()
    if current_user.role != UserRole.ADMIN.value and course.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to approve this LRD",
        )

    # Validate status transition
    valid_transitions = {
        LRDStatus.DRAFT.value: [LRDStatus.PENDING_REVIEW.value],
        LRDStatus.PENDING_REVIEW.value: [LRDStatus.APPROVED.value, LRDStatus.REJECTED.value],
        LRDStatus.REJECTED.value: [LRDStatus.DRAFT.value],
    }

    if approval.status.value not in valid_transitions.get(lrd.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {lrd.status} to {approval.status.value}",
        )

    # Create approval record
    approval_record = ApprovalRecord(
        date=datetime.utcnow(),
        approver_id=str(current_user.id),
        approver_name=current_user.name,
        status=approval.status.value,
        comments=approval.comments,
    )

    # Update LRD
    lrd.status = approval.status.value
    if not lrd.approval_history:
        lrd.approval_history = []
    lrd.approval_history.append(approval_record.model_dump())
    lrd.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(lrd)

    return LRDResponse(
        id=str(lrd.id),
        course_id=str(lrd.course_id),
        version=lrd.version,
        status=lrd.status,
        content=lrd.content,
        created_at=lrd.created_at,
        updated_at=lrd.updated_at,
        approval_history=lrd.approval_history,
        task_lists=[],
    )


@router.post("/{lrd_id}/generate-tasks", response_model=GeneratedTasks)
async def generate_tasks_from_lrd(
    lrd_id: str,
    options: TaskGeneration,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Generate a task list from an approved LRD.
    Creates tasks based on LRD content and teaching philosophy.
    """
    # Get LRD with ownership check
    lrd = (
        db.query(LRD)
        .join(Course, LRD.course_id == Course.id)
        .filter(LRD.id == lrd_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found or access denied",
        )

    # Only approved LRDs can generate tasks
    if lrd.status != LRDStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved LRDs can generate tasks",
        )

    # Generate tasks based on LRD content
    parent_tasks = []
    task_id = 1

    # Core content creation tasks
    for module in lrd.content.get("modules", []):
        module_tasks = {
            "id": str(task_id),
            "title": f"Create content for: {module.get('title', 'Module')}",
            "status": "pending",
            "subtasks": [],
        }

        # Add subtasks based on teaching philosophy
        if lrd.content.get("teaching_philosophy") == "flipped_classroom":
            module_tasks["subtasks"].extend(
                [
                    {
                        "id": f"{task_id}.1",
                        "title": "Create pre-class video content",
                        "completed": False,
                    },
                    {
                        "id": f"{task_id}.2",
                        "title": "Prepare reading materials",
                        "completed": False,
                    },
                    {
                        "id": f"{task_id}.3",
                        "title": "Design in-class activities",
                        "completed": False,
                    },
                    {
                        "id": f"{task_id}.4",
                        "title": "Create post-class assignments",
                        "completed": False,
                    },
                ]
            )
        else:
            module_tasks["subtasks"].extend(
                [
                    {"id": f"{task_id}.1", "title": "Create lecture content", "completed": False},
                    {"id": f"{task_id}.2", "title": "Prepare examples", "completed": False},
                    {"id": f"{task_id}.3", "title": "Design exercises", "completed": False},
                ]
            )

        parent_tasks.append(module_tasks)
        task_id += 1

    # Assessment tasks
    assessment_tasks = {
        "id": str(task_id),
        "title": "Develop assessments",
        "status": "pending",
        "subtasks": [],
    }

    for assessment_type, items in lrd.content.get("assessment", {}).items():
        if isinstance(items, list):
            for item in items:
                assessment_tasks["subtasks"].append(
                    {
                        "id": f"{task_id}.{len(assessment_tasks['subtasks']) + 1}",
                        "title": f"Create {assessment_type}: {item.get('name', 'Assessment')}",
                        "completed": False,
                    }
                )

    if assessment_tasks["subtasks"]:
        parent_tasks.append(assessment_tasks)
        task_id += 1

    # Optional tasks
    if options.include_optional:
        optional_tasks = {
            "id": str(task_id),
            "title": "Additional resources",
            "status": "pending",
            "subtasks": [
                {"id": f"{task_id}.1", "title": "Create supplementary materials", "completed": False},
                {"id": f"{task_id}.2", "title": "Develop practice problems", "completed": False},
                {"id": f"{task_id}.3", "title": "Record tutorial videos", "completed": False},
            ],
        }
        parent_tasks.append(optional_tasks)

    # Calculate estimated hours
    total_subtasks = sum(len(task.get("subtasks", [])) for task in parent_tasks)
    estimated_hours = total_subtasks * 2.5  # Rough estimate: 2.5 hours per subtask

    # Create task list in database
    task_list = TaskList(
        id=uuid.uuid4(),
        lrd_id=lrd.id,
        course_id=lrd.course_id,
        tasks={"parent_tasks": parent_tasks},
        status=TaskStatus.PENDING.value,
        total_tasks=total_subtasks,
        completed_tasks=0,
        progress={
            "last_updated": datetime.utcnow().isoformat(),
            "completion_percentage": 0,
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(task_list)
    db.commit()

    return GeneratedTasks(
        lrd_id=str(lrd.id),
        total_tasks=total_subtasks,
        parent_tasks=parent_tasks,
        estimated_hours=estimated_hours,
        suggested_timeline={
            "weeks": max(4, len(parent_tasks) * 2),
            "hours_per_week": estimated_hours / max(4, len(parent_tasks) * 2),
        },
    )


@router.delete("/{lrd_id}")
async def archive_lrd(
    lrd_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Archive an LRD (soft delete).
    User must own the course.
    """
    # Get LRD with ownership check
    lrd = (
        db.query(LRD)
        .join(Course, LRD.course_id == Course.id)
        .filter(LRD.id == lrd_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found or access denied",
        )

    # Archive the LRD
    lrd.status = LRDStatus.ARCHIVED.value
    lrd.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "LRD archived successfully", "id": str(lrd.id)}
