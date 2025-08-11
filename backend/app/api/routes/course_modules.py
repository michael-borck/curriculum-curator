"""
Course module management endpoints
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Course, CourseModule, Material, User, UserRole
from app.schemas.course_module import (
    CourseClone,
    CourseModuleCreate,
    CourseModuleListResponse,
    CourseModuleResponse,
    CourseModuleUpdate,
    CourseProgress,
    CourseStatistics,
    CourseTemplate,
    ModuleBulkOperation,
    ModuleReorder,
)

router = APIRouter()


@router.get("/courses/{course_id}/modules", response_model=CourseModuleListResponse)
async def get_course_modules(
    course_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get all modules for a course.
    User must own the course or be an admin.
    """
    # Verify access to course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if current_user.role != UserRole.ADMIN.value and course.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this course",
        )

    # Get modules ordered by number
    modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course_id)
        .order_by(CourseModule.number)
        .all()
    )

    return CourseModuleListResponse(
        modules=[
            CourseModuleResponse(
                id=str(module.id),
                course_id=str(module.course_id),
                number=module.number,
                title=module.title,
                description=module.description,
                type=module.type,
                duration_minutes=module.duration_minutes,
                is_optional=module.is_optional,
                prerequisites=module.prerequisites or [],
                is_complete=module.is_complete,
                materials_count=module.materials_count,
                pre_class_content=module.pre_class_content,
                in_class_content=module.in_class_content,
                post_class_content=module.post_class_content,
                created_at=module.created_at,
                updated_at=module.updated_at,
            )
            for module in modules
        ],
        total=len(modules),
        course_id=course_id,
    )


@router.get("/modules/{module_id}", response_model=CourseModuleResponse)
async def get_module(
    module_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a specific module by ID.
    User must own the course or be an admin.
    """
    # Get module with course ownership check
    module = (
        db.query(CourseModule)
        .join(Course, CourseModule.course_id == Course.id)
        .filter(CourseModule.id == module_id)
        .first()
    )

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    # Check access
    course = db.query(Course).filter(Course.id == module.course_id).first()
    if current_user.role != UserRole.ADMIN.value and course.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this module",
        )

    return CourseModuleResponse(
        id=str(module.id),
        course_id=str(module.course_id),
        number=module.number,
        title=module.title,
        description=module.description,
        type=module.type,
        duration_minutes=module.duration_minutes,
        is_optional=module.is_optional,
        prerequisites=module.prerequisites or [],
        is_complete=module.is_complete,
        materials_count=module.materials_count,
        pre_class_content=module.pre_class_content,
        in_class_content=module.in_class_content,
        post_class_content=module.post_class_content,
        created_at=module.created_at,
        updated_at=module.updated_at,
    )


@router.post("/courses/{course_id}/modules", response_model=CourseModuleResponse)
async def create_module(
    course_id: str,
    module_data: CourseModuleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new module in a course.
    User must own the course.
    """
    # Verify user owns the course
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    # Check if module number already exists
    existing = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course_id)
        .filter(CourseModule.number == module_data.number)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Module number {module_data.number} already exists in this course",
        )

    # Create new module
    new_module = CourseModule(
        id=uuid.uuid4(),
        course_id=course_id,
        number=module_data.number,
        title=module_data.title,
        description=module_data.description,
        type=module_data.type.value,
        duration_minutes=module_data.duration_minutes,
        is_optional=module_data.is_optional,
        prerequisites=module_data.prerequisites,
        is_complete=False,
        materials_count=0,
        pre_class_content=module_data.content.pre_class_content if module_data.content else None,
        in_class_content=module_data.content.in_class_content if module_data.content else None,
        post_class_content=module_data.content.post_class_content if module_data.content else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_module)
    db.commit()
    db.refresh(new_module)

    return CourseModuleResponse(
        id=str(new_module.id),
        course_id=str(new_module.course_id),
        number=new_module.number,
        title=new_module.title,
        description=new_module.description,
        type=new_module.type,
        duration_minutes=new_module.duration_minutes,
        is_optional=new_module.is_optional,
        prerequisites=new_module.prerequisites or [],
        is_complete=new_module.is_complete,
        materials_count=new_module.materials_count,
        pre_class_content=new_module.pre_class_content,
        in_class_content=new_module.in_class_content,
        post_class_content=new_module.post_class_content,
        created_at=new_module.created_at,
        updated_at=new_module.updated_at,
    )


@router.put("/modules/{module_id}", response_model=CourseModuleResponse)
async def update_module(
    module_id: str,
    module_data: CourseModuleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update a module.
    User must own the course.
    """
    # Get module with ownership check
    module = (
        db.query(CourseModule)
        .join(Course, CourseModule.course_id == Course.id)
        .filter(CourseModule.id == module_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found or access denied",
        )

    # Update fields if provided
    update_data = module_data.model_dump(exclude_unset=True)

    # Handle content updates specially
    if update_data.get("content"):
        content = update_data.pop("content")
        if content.get("pre_class_content"):
            module.pre_class_content = content["pre_class_content"]
        if content.get("in_class_content"):
            module.in_class_content = content["in_class_content"]
        if content.get("post_class_content"):
            module.post_class_content = content["post_class_content"]

    # Update other fields
    for field, value in update_data.items():
        if hasattr(module, field):
            setattr(module, field, value)

    module.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(module)

    return CourseModuleResponse(
        id=str(module.id),
        course_id=str(module.course_id),
        number=module.number,
        title=module.title,
        description=module.description,
        type=module.type,
        duration_minutes=module.duration_minutes,
        is_optional=module.is_optional,
        prerequisites=module.prerequisites or [],
        is_complete=module.is_complete,
        materials_count=module.materials_count,
        pre_class_content=module.pre_class_content,
        in_class_content=module.in_class_content,
        post_class_content=module.post_class_content,
        created_at=module.created_at,
        updated_at=module.updated_at,
    )


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete a module.
    User must own the course.
    """
    # Get module with ownership check
    module = (
        db.query(CourseModule)
        .join(Course, CourseModule.course_id == Course.id)
        .filter(CourseModule.id == module_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found or access denied",
        )

    # Delete associated materials
    db.query(Material).filter(Material.module_id == module_id).delete()

    # Renumber remaining modules
    remaining_modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == module.course_id)
        .filter(CourseModule.number > module.number)
        .all()
    )

    for remaining in remaining_modules:
        remaining.number -= 1

    db.delete(module)
    db.commit()

    return {"message": "Module deleted successfully", "id": str(module_id)}


@router.post("/courses/{course_id}/modules/reorder")
async def reorder_modules(
    course_id: str,
    reorder_data: ModuleReorder,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Reorder modules in a course.
    User must own the course.
    """
    # Verify user owns the course
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    # Update module positions
    for item in reorder_data.module_order:
        module_id = item.get("module_id")
        new_position = item.get("position")

        module = (
            db.query(CourseModule)
            .filter(CourseModule.id == module_id)
            .filter(CourseModule.course_id == course_id)
            .first()
        )

        if module:
            module.number = new_position
            module.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Modules reordered successfully", "course_id": course_id}


@router.post("/courses/{course_id}/modules/bulk")
async def bulk_module_operation(
    course_id: str,
    operation: ModuleBulkOperation,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Perform bulk operations on modules.
    User must own the course.
    """
    # Verify user owns the course
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    # Get modules
    modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course_id)
        .filter(CourseModule.id.in_(operation.module_ids))
        .all()
    )

    if operation.operation == "delete":
        for module in modules:
            db.delete(module)
    elif operation.operation == "mark_complete":
        for module in modules:
            module.is_complete = True
            module.updated_at = datetime.utcnow()
    elif operation.operation == "mark_incomplete":
        for module in modules:
            module.is_complete = False
            module.updated_at = datetime.utcnow()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown operation: {operation.operation}",
        )

    db.commit()

    return {
        "message": f"Bulk operation '{operation.operation}' completed",
        "affected_modules": len(modules),
    }


@router.post("/courses/{course_id}/clone", response_model=CourseModuleResponse)
async def clone_course(
    course_id: str,
    clone_data: CourseClone,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Clone a course with options for what to include.
    User must own the original course or be an admin.
    """
    # Get original course
    original_course = db.query(Course).filter(Course.id == course_id).first()

    if not original_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    # Check access
    if (
        current_user.role != UserRole.ADMIN.value
        and original_course.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to clone this course",
        )

    # Create new course
    new_course = Course(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=clone_data.new_title,
        code=clone_data.new_code,
        description=original_course.description,
        teaching_philosophy=original_course.teaching_philosophy,
        language_preference=original_course.language_preference,
        status="planning",
        semester=clone_data.semester or original_course.semester,
        credits=original_course.credits,
        learning_objectives=original_course.learning_objectives,
        prerequisites=original_course.prerequisites,
        assessment_structure=original_course.assessment_structure,
        course_metadata=original_course.course_metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_course)

    # Clone modules if requested
    if clone_data.include_modules:
        original_modules = (
            db.query(CourseModule)
            .filter(CourseModule.course_id == course_id)
            .order_by(CourseModule.number)
            .all()
        )

        for module in original_modules:
            new_module = CourseModule(
                id=uuid.uuid4(),
                course_id=new_course.id,
                number=module.number,
                title=module.title,
                description=module.description,
                type=module.type,
                duration_minutes=module.duration_minutes,
                is_optional=module.is_optional,
                prerequisites=module.prerequisites,
                is_complete=False,
                materials_count=0,
                pre_class_content=module.pre_class_content,
                in_class_content=module.in_class_content,
                post_class_content=module.post_class_content,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_module)

            # Clone materials if requested
            if clone_data.include_materials:
                original_materials = (
                    db.query(Material)
                    .filter(Material.module_id == module.id)
                    .filter(Material.is_latest.is_(True))
                    .all()
                )

                for material in original_materials:
                    new_material = Material(
                        id=uuid.uuid4(),
                        course_id=new_course.id,
                        module_id=new_module.id,
                        type=material.type,
                        title=material.title,
                        description=material.description,
                        content=material.content,
                        raw_content=material.raw_content,
                        version=1,
                        is_latest=True,
                        teaching_philosophy=material.teaching_philosophy,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(new_material)

    db.commit()
    db.refresh(new_course)

    return {
        "message": "Course cloned successfully",
        "original_id": str(course_id),
        "new_course_id": str(new_course.id),
        "new_course_title": new_course.title,
        "new_course_code": new_course.code,
    }


@router.get("/courses/{course_id}/progress", response_model=CourseProgress)
async def get_course_progress(
    course_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get progress tracking for a course.
    User must own the course.
    """
    # Verify access to course
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    # Get module statistics
    modules = db.query(CourseModule).filter(CourseModule.course_id == course_id).all()
    total_modules = len(modules)
    completed_modules = sum(1 for m in modules if m.is_complete)

    # Get material statistics
    materials = db.query(Material).filter(Material.course_id == course_id).all()
    total_materials = len(materials)
    # Note: We don't have a completed field for materials yet, so we'll estimate
    completed_materials = 0  # This would need to be tracked separately

    # Calculate overall progress
    if total_modules > 0:
        module_progress = (completed_modules / total_modules) * 100
    else:
        module_progress = 0

    # Calculate estimated hours remaining
    incomplete_modules = [m for m in modules if not m.is_complete]
    estimated_hours = sum(m.duration_minutes / 60 for m in incomplete_modules)

    # Get last activity (most recent update)
    last_activity = None
    if modules:
        last_updated_module = max(modules, key=lambda m: m.updated_at)
        last_activity = last_updated_module.updated_at

    # Create milestones
    milestones = []
    if total_modules > 0:
        milestones.append(
            {
                "name": "Course Started",
                "completed": total_modules > 0,
                "date": course.created_at.isoformat() if course.created_at else None,
            }
        )
        milestones.append(
            {
                "name": "25% Complete",
                "completed": completed_modules >= total_modules * 0.25,
                "date": None,
            }
        )
        milestones.append(
            {
                "name": "50% Complete",
                "completed": completed_modules >= total_modules * 0.5,
                "date": None,
            }
        )
        milestones.append(
            {
                "name": "75% Complete",
                "completed": completed_modules >= total_modules * 0.75,
                "date": None,
            }
        )
        milestones.append(
            {"name": "Course Complete", "completed": completed_modules == total_modules, "date": None}
        )

    return CourseProgress(
        course_id=str(course_id),
        total_modules=total_modules,
        completed_modules=completed_modules,
        total_materials=total_materials,
        completed_materials=completed_materials,
        overall_progress=module_progress,
        estimated_hours_remaining=estimated_hours,
        last_activity=last_activity,
        milestones=milestones,
    )


@router.get("/courses/{course_id}/statistics", response_model=CourseStatistics)
async def get_course_statistics(
    course_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get detailed statistics for a course.
    User must own the course or be an admin.
    """
    # Verify access to course
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if current_user.role != UserRole.ADMIN.value and course.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this course",
        )

    # Get modules with statistics
    modules = db.query(CourseModule).filter(CourseModule.course_id == course_id).all()

    module_stats = []
    total_content_hours = 0

    for module in modules:
        materials_count = (
            db.query(Material).filter(Material.module_id == module.id).count()
        )

        module_hours = module.duration_minutes / 60
        total_content_hours += module_hours

        module_stats.append(
            {
                "module_id": str(module.id),
                "module_number": module.number,
                "module_title": module.title,
                "is_complete": module.is_complete,
                "materials_count": materials_count,
                "duration_hours": module_hours,
                "type": module.type,
            }
        )

    # Calculate completion rate
    if len(modules) > 0:
        avg_completion = sum(1 for m in modules if m.is_complete) / len(modules) * 100
    else:
        avg_completion = 0

    return CourseStatistics(
        course_id=str(course_id),
        student_count=0,  # Would need enrollment tracking
        avg_completion_rate=avg_completion,
        total_content_hours=total_content_hours,
        module_statistics=module_stats,
        engagement_metrics={
            "total_modules": len(modules),
            "completed_modules": sum(1 for m in modules if m.is_complete),
            "optional_modules": sum(1 for m in modules if m.is_optional),
        },
    )


@router.get("/templates", response_model=list[CourseTemplate])
async def get_course_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get available course templates.
    Available to all authenticated users.
    """
    # Predefined templates based on teaching philosophies
    return [
        CourseTemplate(
            name="Flipped Classroom Template",
            description="Template for flipped classroom approach with pre-class videos and in-class activities",
            teaching_philosophy="flipped_classroom",
            module_structure=[
                {
                    "number": 1,
                    "title": "Introduction & Course Overview",
                    "type": "flipped",
                    "duration_minutes": 120,
                },
                {
                    "number": 2,
                    "title": "Core Concept 1",
                    "type": "flipped",
                    "duration_minutes": 120,
                },
                {
                    "number": 3,
                    "title": "Core Concept 2",
                    "type": "flipped",
                    "duration_minutes": 120,
                },
                {
                    "number": 4,
                    "title": "Practical Application",
                    "type": "flipped",
                    "duration_minutes": 180,
                },
                {
                    "number": 5,
                    "title": "Assessment & Review",
                    "type": "flipped",
                    "duration_minutes": 120,
                },
            ],
            duration_weeks=12,
            assessment_structure={"participation": 10, "assignments": 40, "midterm": 20, "final": 30},
        ),
        CourseTemplate(
            name="Project-Based Learning Template",
            description="Template for project-based courses with hands-on deliverables",
            teaching_philosophy="project_based",
            module_structure=[
                {
                    "number": 1,
                    "title": "Project Introduction & Planning",
                    "type": "project",
                    "duration_minutes": 180,
                },
                {
                    "number": 2,
                    "title": "Research & Requirements",
                    "type": "project",
                    "duration_minutes": 180,
                },
                {
                    "number": 3,
                    "title": "Design & Prototyping",
                    "type": "project",
                    "duration_minutes": 240,
                },
                {
                    "number": 4,
                    "title": "Implementation Phase 1",
                    "type": "project",
                    "duration_minutes": 240,
                },
                {
                    "number": 5,
                    "title": "Implementation Phase 2",
                    "type": "project",
                    "duration_minutes": 240,
                },
                {
                    "number": 6,
                    "title": "Testing & Refinement",
                    "type": "project",
                    "duration_minutes": 180,
                },
                {
                    "number": 7,
                    "title": "Final Presentation",
                    "type": "project",
                    "duration_minutes": 120,
                },
            ],
            duration_weeks=14,
            assessment_structure={
                "project_milestones": 40,
                "final_project": 40,
                "peer_review": 10,
                "presentation": 10,
            },
        ),
        CourseTemplate(
            name="Traditional Lecture Template",
            description="Traditional lecture-based course structure",
            teaching_philosophy="traditional_lecture",
            module_structure=[
                {
                    "number": i,
                    "title": f"Week {i} - Topic {i}",
                    "type": "traditional",
                    "duration_minutes": 150,
                }
                for i in range(1, 13)
            ],
            duration_weeks=12,
            assessment_structure={"assignments": 30, "midterm": 30, "final": 40},
        ),
    ]



@router.post("/courses/from-template")
async def create_course_from_template(
    template_name: str,
    title: str,
    code: str,
    semester: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new course from a template.
    """
    # Get template (in real app, might be from DB)
    templates = await get_course_templates(db, current_user)
    template = next((t for t in templates if t.name == template_name), None)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Create course
    new_course = Course(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=title,
        code=code,
        description=f"Course created from template: {template.name}",
        teaching_philosophy=template.teaching_philosophy,
        language_preference=current_user.language_preference or "en-AU",
        status="planning",
        semester=semester,
        credits=3,
        assessment_structure=template.assessment_structure,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_course)

    # Create modules from template
    for module_def in template.module_structure:
        module = CourseModule(
            id=uuid.uuid4(),
            course_id=new_course.id,
            number=module_def["number"],
            title=module_def["title"],
            type=module_def["type"],
            duration_minutes=module_def["duration_minutes"],
            is_complete=False,
            materials_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(module)

    db.commit()
    db.refresh(new_course)

    return {
        "message": "Course created from template successfully",
        "course_id": str(new_course.id),
        "course_title": new_course.title,
        "course_code": new_course.code,
        "template_used": template_name,
    }
