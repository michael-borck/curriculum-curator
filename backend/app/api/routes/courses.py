"""
Course management routes with user workspace isolation
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Unit, UnitStatus, User, UserRole
from app.schemas.course import (
    CourseCreate,
    CourseListResponse,
    CourseResponse,
    CourseUpdate,
)

router = APIRouter()


@router.get("/", response_model=CourseListResponse)
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    user_id: str | None = None,  # Admin can filter by user
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get all courses for the current user.
    Admins can see all courses or filter by user_id.
    Regular users only see their own courses.
    """
    # Admin can see all or filter by user
    if current_user.role == UserRole.ADMIN.value:
        if user_id:
            query = db.query(Unit).filter(Unit.owner_id == user_id)
        else:
            query = db.query(Unit)
    else:
        # Regular users only see their own
        query = db.query(Unit).filter(Unit.owner_id == current_user.id)

    # Apply filters
    if status:
        query = query.filter(Unit.status == status)
    if search:
        query = query.filter(Unit.title.contains(search) | Unit.code.contains(search))

    # Get total count
    total = query.count()

    # Apply pagination
    courses = query.offset(skip).limit(limit).all()

    return CourseListResponse(
        courses=[
            CourseResponse(
                id=str(course.id),
                title=course.title,
                code=course.code,
                description=course.description or "",
                year=course.year,
                semester=course.semester,
                status=course.status,
                pedagogy_type=course.pedagogy_type,
                difficulty_level=course.difficulty_level,
                duration_weeks=course.duration_weeks,
                credit_points=course.credit_points,
                created_at=course.created_at.isoformat(),
                updated_at=course.updated_at.isoformat(),
            )
            for course in courses
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a specific course by ID.
    Regular users can only see their own courses.
    Admins can see any course.
    """
    # Build query based on user role
    if current_user.role == UserRole.ADMIN.value:
        # Admin can see any course
        course = db.query(Unit).filter(Unit.id == course_id).first()
    else:
        # Regular user can only see their own
        course = (
            db.query(Unit)
            .filter(Unit.id == course_id)
            .filter(Unit.owner_id == current_user.id)
            .first()
        )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    return CourseResponse(
        id=str(course.id),
        title=course.title,
        code=course.code,
        description=course.description or "",
        year=course.year,
        semester=course.semester,
        status=course.status,
        pedagogy_type=course.pedagogy_type,
        difficulty_level=course.difficulty_level,
        duration_weeks=course.duration_weeks,
        credit_points=course.credit_points,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat(),
    )


@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new course.
    The course will be owned by the authenticated user.
    """
    # Create new unit with current user as owner
    new_course = Unit(
        id=uuid.uuid4(),
        title=course_data.title,
        code=course_data.code,
        description=course_data.description,
        year=course_data.year,
        semester=course_data.semester,
        status=course_data.status or UnitStatus.DRAFT.value,
        pedagogy_type=course_data.pedagogy_type,
        difficulty_level=course_data.difficulty_level,
        duration_weeks=course_data.duration_weeks,
        credit_points=course_data.credit_points,
        owner_id=current_user.id,
        created_by_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    return CourseResponse(
        id=str(new_course.id),
        title=new_course.title,
        code=new_course.code,
        description=new_course.description or "",
        year=new_course.year,
        semester=new_course.semester,
        status=new_course.status,
        pedagogy_type=new_course.pedagogy_type,
        difficulty_level=new_course.difficulty_level,
        duration_weeks=new_course.duration_weeks,
        credit_points=new_course.credit_points,
        created_at=new_course.created_at.isoformat(),
        updated_at=new_course.updated_at.isoformat(),
    )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update a course.
    Only the owner can update their course.
    """
    course = (
        db.query(Unit)
        .filter(Unit.id == course_id)
        .filter(Unit.owner_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    # Update fields if provided
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)

    course.updated_by_id = current_user.id
    course.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(course)

    return CourseResponse(
        id=str(course.id),
        title=course.title,
        code=course.code,
        description=course.description or "",
        year=course.year,
        semester=course.semester,
        status=course.status,
        pedagogy_type=course.pedagogy_type,
        difficulty_level=course.difficulty_level,
        duration_weeks=course.duration_weeks,
        credit_points=course.credit_points,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat(),
    )


@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete a course.
    Only the owner can delete their course.
    """
    course = (
        db.query(Unit)
        .filter(Unit.id == course_id)
        .filter(Unit.owner_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    db.delete(course)
    db.commit()

    return {"message": "Course deleted successfully"}
