"""
Material management endpoints with versioning and quality tracking
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Course, CourseModule, Material, User, UserRole
from app.schemas.material import (
    ContentValidation,
    MaterialAnalytics,
    MaterialBulkOperation,
    MaterialClone,
    MaterialCreate,
    MaterialListResponse,
    MaterialResponse,
    MaterialTemplate,
    MaterialType,
    MaterialUpdate,
    MaterialVersionHistory,
    QualityMetrics,
)

router = APIRouter()


def _calculate_completeness_score(material: Material) -> float:
    """Calculate completeness score based on filled fields"""
    score = 0
    if material.title:
        score += 20
    if material.description:
        score += 20
    if material.content:
        score += 30
    if material.raw_content and len(material.raw_content) > 100:
        score += 30
    return score


def _calculate_clarity_score(material: Material) -> float:
    """Calculate clarity score based on content structure"""
    score = 80  # Default decent clarity
    if not material.raw_content:
        return score

    # Check for structure indicators
    has_headers = "##" in material.raw_content or "###" in material.raw_content
    has_paragraphs = len(material.raw_content.split("\n\n")) > 3

    if has_headers:
        score += 10
    if has_paragraphs:
        score += 10

    return min(score, 100)


def _calculate_engagement_score(material: Material) -> float:
    """Calculate engagement score based on interactive elements"""
    score = 50  # Base score

    if not material.content or not isinstance(material.content, dict):
        return score

    # Add points for different interactive elements
    engagement_elements = {"exercises": 25, "code_snippets": 15, "media_urls": 10}

    for element, points in engagement_elements.items():
        if material.content.get(element):
            score += points

    return min(score, 100)


def _calculate_alignment_score(material: Material) -> float:
    """Calculate alignment score based on learning objectives"""
    if (
        material.content
        and isinstance(material.content, dict)
        and material.content.get("learning_objectives")
    ):
        return 90
    return 70  # Default alignment


def _calculate_accessibility_score(material: Material) -> float:
    """Calculate accessibility score based on content features"""
    score = 80  # Default good accessibility

    # Check for images without alt text
    if (
        material.raw_content
        and "![" in material.raw_content
        and "alt=" not in material.raw_content.lower()
    ):
        score -= 20

    return max(score, 0)


def calculate_quality_score(material: Material) -> tuple[float, QualityMetrics]:
    """Calculate quality score for a material"""
    metrics = QualityMetrics()

    # Calculate individual metric scores
    metrics.completeness = _calculate_completeness_score(material)
    metrics.clarity = _calculate_clarity_score(material)
    metrics.engagement = _calculate_engagement_score(material)
    metrics.alignment = _calculate_alignment_score(material)
    metrics.accessibility = _calculate_accessibility_score(material)

    # Calculate weighted overall score
    weights = {
        "completeness": 0.2,
        "clarity": 0.2,
        "engagement": 0.25,
        "alignment": 0.2,
        "accessibility": 0.15,
    }

    metrics.overall = sum(
        getattr(metrics, metric) * weight for metric, weight in weights.items()
    )

    return metrics.overall, metrics


@router.get("/", response_model=MaterialListResponse)
async def get_materials(
    course_id: str | None = None,
    module_id: str | None = None,
    material_type: MaterialType | None = None,
    only_latest: bool = True,
    include_drafts: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get materials with filtering options.
    Users see only materials from their courses.
    """
    # Base query - join with courses for access control
    query = db.query(Material).join(Course, Material.course_id == Course.id)

    # Access control
    if current_user.role != UserRole.ADMIN.value:
        query = query.filter(Course.user_id == current_user.id)

    # Apply filters
    if course_id:
        query = query.filter(Material.course_id == course_id)
    if module_id:
        query = query.filter(Material.module_id == module_id)
    if material_type:
        query = query.filter(Material.type == material_type.value)
    if only_latest:
        query = query.filter(Material.is_latest.is_(True))
    if not include_drafts:
        query = query.filter(
            or_(Material.is_draft.is_(False), Material.is_draft.is_(None))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    materials = query.offset(skip).limit(limit).all()

    # Build response with quality scores
    material_responses = []
    for material in materials:
        quality_score, quality_metrics = calculate_quality_score(material)
        material_responses.append(
            MaterialResponse(
                id=str(material.id),
                course_id=str(material.course_id),
                module_id=str(material.module_id) if material.module_id else None,
                type=material.type,
                title=material.title,
                description=material.description,
                version=material.version,
                parent_version_id=str(material.parent_version_id)
                if material.parent_version_id
                else None,
                is_latest=material.is_latest,
                is_draft=getattr(material, "is_draft", False),
                teaching_philosophy=material.teaching_philosophy,
                quality_score=quality_score,
                quality_metrics=quality_metrics,
                content=material.content or {},
                raw_content=material.raw_content,
                created_at=material.created_at,
                updated_at=material.updated_at,
            )
        )

    return MaterialListResponse(
        materials=material_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    version: int | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a specific material by ID, optionally at a specific version.
    """
    # Build query
    query = db.query(Material).join(Course, Material.course_id == Course.id)

    if version:
        # Get specific version
        query = query.filter(
            and_(
                Material.id == material_id,
                Material.version == version,
            )
        )
    else:
        # Get latest version
        query = query.filter(Material.id == material_id)

    # Access control
    if current_user.role != UserRole.ADMIN.value:
        query = query.filter(Course.user_id == current_user.id)

    material = query.first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    quality_score, quality_metrics = calculate_quality_score(material)

    return MaterialResponse(
        id=str(material.id),
        course_id=str(material.course_id),
        module_id=str(material.module_id) if material.module_id else None,
        type=material.type,
        title=material.title,
        description=material.description,
        version=material.version,
        parent_version_id=str(material.parent_version_id)
        if material.parent_version_id
        else None,
        is_latest=material.is_latest,
        is_draft=getattr(material, "is_draft", False),
        teaching_philosophy=material.teaching_philosophy,
        quality_score=quality_score,
        quality_metrics=quality_metrics,
        content=material.content or {},
        raw_content=material.raw_content,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.post("/", response_model=MaterialResponse)
async def create_material(
    material_data: MaterialCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new material.
    User must own the course.
    """
    # Verify user owns the course
    course = (
        db.query(Course)
        .filter(Course.id == material_data.course_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or access denied",
        )

    # Verify module if provided
    if material_data.module_id:
        module = (
            db.query(CourseModule)
            .filter(CourseModule.id == material_data.module_id)
            .filter(CourseModule.course_id == material_data.course_id)
            .first()
        )
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found in this course",
            )

    # Create new material
    new_material = Material(
        id=uuid.uuid4(),
        course_id=material_data.course_id,
        module_id=material_data.module_id,
        type=material_data.type.value,
        title=material_data.title,
        description=material_data.description,
        content=material_data.content.model_dump(),
        raw_content=material_data.content.body,
        version=1,
        is_latest=True,
        is_draft=material_data.is_draft,
        teaching_philosophy=material_data.teaching_philosophy,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )

    # Calculate initial quality score
    quality_score, _ = calculate_quality_score(new_material)
    new_material.quality_score = quality_score

    db.add(new_material)

    # Update module materials count if applicable
    if material_data.module_id:
        module = (
            db.query(CourseModule)
            .filter(CourseModule.id == material_data.module_id)
            .first()
        )
        if module:
            module.materials_count = (module.materials_count or 0) + 1

    db.commit()
    db.refresh(new_material)

    quality_score, quality_metrics = calculate_quality_score(new_material)

    return MaterialResponse(
        id=str(new_material.id),
        course_id=str(new_material.course_id),
        module_id=str(new_material.module_id) if new_material.module_id else None,
        type=new_material.type,
        title=new_material.title,
        description=new_material.description,
        version=new_material.version,
        parent_version_id=None,
        is_latest=new_material.is_latest,
        is_draft=new_material.is_draft,
        teaching_philosophy=new_material.teaching_philosophy,
        quality_score=quality_score,
        quality_metrics=quality_metrics,
        content=new_material.content,
        raw_content=new_material.raw_content,
        created_at=new_material.created_at,
        updated_at=new_material.updated_at,
    )


@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: str,
    material_data: MaterialUpdate,
    create_version: bool = True,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update a material, optionally creating a new version.
    """
    # Get current material with access check
    material = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id)
        .filter(Material.is_latest.is_(True))
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    if create_version and not material.is_draft:
        # Create new version
        new_version = Material(
            id=uuid.uuid4(),
            course_id=material.course_id,
            module_id=material.module_id,
            type=material.type,
            title=material_data.title or material.title,
            description=material_data.description or material.description,
            content=material_data.content.model_dump()
            if material_data.content
            else material.content,
            raw_content=material_data.content.body
            if material_data.content
            else material.raw_content,
            version=material.version + 1,
            parent_version_id=material.id,
            is_latest=True,
            is_draft=material_data.is_draft
            if material_data.is_draft is not None
            else material.is_draft,
            teaching_philosophy=material.teaching_philosophy,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )

        # Mark old version as not latest
        material.is_latest = False

        # Calculate quality score for new version
        quality_score, _ = calculate_quality_score(new_version)
        new_version.quality_score = quality_score

        db.add(new_version)
        updated_material = new_version
    else:
        # Update in place
        update_data = material_data.model_dump(exclude_unset=True)

        if update_data.get("content"):
            material.content = update_data.pop("content")
            if material_data.content:
                material.raw_content = material_data.content.body

        for field, value in update_data.items():
            if hasattr(material, field):
                setattr(material, field, value)

        material.updated_at = datetime.utcnow()
        material.updated_by_id = current_user.id

        # Recalculate quality score
        quality_score, _ = calculate_quality_score(material)
        material.quality_score = quality_score

        updated_material = material

    db.commit()
    db.refresh(updated_material)

    quality_score, quality_metrics = calculate_quality_score(updated_material)

    return MaterialResponse(
        id=str(updated_material.id),
        course_id=str(updated_material.course_id),
        module_id=str(updated_material.module_id)
        if updated_material.module_id
        else None,
        type=updated_material.type,
        title=updated_material.title,
        description=updated_material.description,
        version=updated_material.version,
        parent_version_id=str(updated_material.parent_version_id)
        if updated_material.parent_version_id
        else None,
        is_latest=updated_material.is_latest,
        is_draft=updated_material.is_draft,
        teaching_philosophy=updated_material.teaching_philosophy,
        quality_score=quality_score,
        quality_metrics=quality_metrics,
        content=updated_material.content,
        raw_content=updated_material.raw_content,
        created_at=updated_material.created_at,
        updated_at=updated_material.updated_at,
    )


@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete a material and all its versions.
    """
    # Get material with access check
    material = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    # Delete all versions
    db.query(Material).filter(
        or_(
            Material.id == material_id,
            Material.parent_version_id == material_id,
        )
    ).delete()

    # Update module materials count if applicable
    if material.module_id:
        module = (
            db.query(CourseModule).filter(CourseModule.id == material.module_id).first()
        )
        if module and module.materials_count:
            module.materials_count = max(0, module.materials_count - 1)

    db.commit()

    return {"message": "Material deleted successfully", "id": str(material_id)}



@router.post("/{material_id}/clone", response_model=MaterialResponse)
async def clone_material(
    material_id: str,
    clone_data: MaterialClone,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Clone a material to another course or module.
    """
    # Get source material
    source_material = (
        db.query(Material)
        .filter(Material.id == material_id)
        .filter(Material.is_latest.is_(True))
        .first()
    )

    if not source_material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    # Verify user owns target course
    target_course = (
        db.query(Course)
        .filter(Course.id == clone_data.target_course_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not target_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target course not found or access denied",
        )

    # Create cloned material
    cloned_material = Material(
        id=uuid.uuid4(),
        course_id=clone_data.target_course_id,
        module_id=clone_data.target_module_id,
        type=source_material.type,
        title=clone_data.new_title or f"{source_material.title} (Copy)",
        description=source_material.description,
        content=source_material.content,
        raw_content=source_material.raw_content,
        version=1,
        is_latest=True,
        is_draft=clone_data.create_as_draft,
        teaching_philosophy=clone_data.adapt_to_philosophy
        or source_material.teaching_philosophy,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )

    # Calculate quality score
    quality_score, _ = calculate_quality_score(cloned_material)
    cloned_material.quality_score = quality_score

    db.add(cloned_material)

    # Update module materials count if applicable
    if clone_data.target_module_id:
        module = (
            db.query(CourseModule)
            .filter(CourseModule.id == clone_data.target_module_id)
            .first()
        )
        if module:
            module.materials_count = (module.materials_count or 0) + 1

    db.commit()
    db.refresh(cloned_material)

    quality_score, quality_metrics = calculate_quality_score(cloned_material)

    return MaterialResponse(
        id=str(cloned_material.id),
        course_id=str(cloned_material.course_id),
        module_id=str(cloned_material.module_id) if cloned_material.module_id else None,
        type=cloned_material.type,
        title=cloned_material.title,
        description=cloned_material.description,
        version=cloned_material.version,
        parent_version_id=None,
        is_latest=cloned_material.is_latest,
        is_draft=cloned_material.is_draft,
        teaching_philosophy=cloned_material.teaching_philosophy,
        quality_score=quality_score,
        quality_metrics=quality_metrics,
        content=cloned_material.content,
        raw_content=cloned_material.raw_content,
        created_at=cloned_material.created_at,
        updated_at=cloned_material.updated_at,
    )


def _bulk_publish_materials(
    materials: list[Material], operation_data: dict | None = None
) -> int:
    """Publish draft materials"""
    affected_count = 0
    for material in materials:
        if material.is_draft:
            material.is_draft = False
            material.updated_at = datetime.utcnow()
            affected_count += 1
    return affected_count


def _bulk_archive_materials(
    materials: list[Material], operation_data: dict | None = None
) -> int:
    """Archive materials by marking them as not latest"""
    affected_count = 0
    for material in materials:
        material.is_latest = False
        material.updated_at = datetime.utcnow()
        affected_count += 1
    return affected_count


def _bulk_delete_materials(
    materials: list[Material],
    operation_data: dict | None = None,
    db: Session | None = None,
) -> int:
    """Delete materials from database"""
    affected_count = 0
    for material in materials:
        if db:
            db.delete(material)
        affected_count += 1
    return affected_count


def _bulk_move_materials(
    materials: list[Material], operation_data: dict | None = None
) -> int:
    """Move materials to a different module"""
    if not operation_data:
        return 0

    new_module_id = operation_data.get("module_id")
    if not new_module_id:
        return 0

    affected_count = 0
    for material in materials:
        material.module_id = new_module_id
        material.updated_at = datetime.utcnow()
        affected_count += 1
    return affected_count


def _bulk_tag_materials(
    materials: list[Material], operation_data: dict | None = None
) -> int:
    """Add tags to materials"""
    if not operation_data:
        return 0

    tags = operation_data.get("tags", [])
    if not tags:
        return 0

    affected_count = 0
    for material in materials:
        # Add tags to content metadata
        content = material.content if material.content else {}
        if not isinstance(content, dict):
            content = {}
        content["tags"] = list(set(content.get("tags", []) + tags))
        material.content = content
        material.updated_at = datetime.utcnow()
        affected_count += 1
    return affected_count


@router.post("/bulk", response_model=dict)
async def bulk_material_operation(
    operation: MaterialBulkOperation,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Perform bulk operations on materials.
    """
    # Get materials with access check
    materials = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id.in_(operation.material_ids))
        .filter(Course.user_id == current_user.id)
        .all()
    )

    if len(materials) != len(operation.material_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to some materials",
        )

    # Define operation handlers
    def delete_handler(materials: list[Material], data: dict) -> int:
        return _bulk_delete_materials(materials, data, db)

    operation_handlers = {
        "publish": _bulk_publish_materials,
        "archive": _bulk_archive_materials,
        "delete": delete_handler,
        "move": _bulk_move_materials,
        "tag": _bulk_tag_materials,
    }

    # Get the handler for the operation
    handler = operation_handlers.get(operation.operation)
    if not handler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown operation: {operation.operation}",
        )

    # Execute the operation
    affected_count = handler(materials, operation.data)

    db.commit()

    return {
        "message": f"Bulk operation '{operation.operation}' completed",
        "affected_materials": affected_count,
    }


@router.get("/templates/{material_type}", response_model=list[MaterialTemplate])
async def get_material_templates(
    material_type: MaterialType,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get templates for creating materials of a specific type.
    """
    templates = []

    if material_type == MaterialType.LECTURE:
        templates.append(
            MaterialTemplate(
                type=MaterialType.LECTURE,
                name="Standard Lecture",
                description="Traditional lecture format with sections",
                structure={
                    "sections": [
                        "Introduction",
                        "Main Content",
                        "Summary",
                        "Questions",
                    ],
                    "includes": ["objectives", "key_points", "examples"],
                },
                default_content={
                    "format": "markdown",
                    "body": "# Lecture Title\n\n## Learning Objectives\n- Objective 1\n- Objective 2\n\n## Introduction\n\n## Main Content\n\n### Topic 1\n\n### Topic 2\n\n## Summary\n\n## Questions for Discussion\n",
                    "metadata": {"type": "lecture"},
                },
                suggested_duration=50,
                best_for=["traditional_lecture", "direct_instruction"],
            )
        )
        templates.append(
            MaterialTemplate(
                type=MaterialType.LECTURE,
                name="Flipped Classroom Pre-Class",
                description="Video-based content for pre-class preparation",
                structure={
                    "sections": [
                        "Preview",
                        "Video Content",
                        "Reading",
                        "Pre-Class Quiz",
                    ],
                    "includes": ["video_links", "reading_list", "self_check"],
                },
                default_content={
                    "format": "markdown",
                    "body": "# Pre-Class Preparation\n\n## What You'll Learn\n\n## Video Lectures\n- [Video 1: Introduction]()\n- [Video 2: Core Concepts]()\n\n## Required Reading\n\n## Self-Check Questions\n",
                    "metadata": {"type": "flipped_pre_class"},
                },
                suggested_duration=45,
                best_for=["flipped_classroom"],
            )
        )

    elif material_type == MaterialType.WORKSHEET:
        templates.append(
            MaterialTemplate(
                type=MaterialType.WORKSHEET,
                name="Problem Set",
                description="Practice problems with worked examples",
                structure={
                    "sections": [
                        "Instructions",
                        "Worked Example",
                        "Practice Problems",
                        "Challenge",
                    ],
                    "includes": ["solutions", "hints"],
                },
                default_content={
                    "format": "markdown",
                    "body": "# Worksheet: [Topic]\n\n## Instructions\n\n## Worked Example\n\n### Problem\n\n### Solution\n\n## Practice Problems\n\n1. Problem 1\n2. Problem 2\n3. Problem 3\n\n## Challenge Problem\n",
                    "metadata": {"type": "worksheet"},
                },
                suggested_duration=30,
                best_for=[
                    "traditional_lecture",
                    "direct_instruction",
                    "flipped_classroom",
                ],
            )
        )

    elif material_type == MaterialType.QUIZ:
        templates.append(
            MaterialTemplate(
                type=MaterialType.QUIZ,
                name="Formative Assessment",
                description="Quick check for understanding",
                structure={
                    "sections": ["Instructions", "Questions", "Feedback"],
                    "question_types": ["multiple_choice", "short_answer", "true_false"],
                },
                default_content={
                    "format": "markdown",
                    "body": "# Quiz: [Topic]\n\n## Instructions\nTime limit: 15 minutes\n\n## Questions\n\n### Question 1 (Multiple Choice)\n\nA) Option A\nB) Option B\nC) Option C\nD) Option D\n\n### Question 2 (Short Answer)\n\n### Question 3 (True/False)\n",
                    "metadata": {"type": "quiz", "time_limit": 15},
                },
                suggested_duration=15,
                best_for=["all"],
            )
        )

    elif material_type == MaterialType.LAB:
        templates.append(
            MaterialTemplate(
                type=MaterialType.LAB,
                name="Hands-On Lab",
                description="Practical exercise with step-by-step instructions",
                structure={
                    "sections": [
                        "Objectives",
                        "Setup",
                        "Procedure",
                        "Analysis",
                        "Cleanup",
                    ],
                    "includes": ["materials_list", "safety_notes", "troubleshooting"],
                },
                default_content={
                    "format": "markdown",
                    "body": "# Lab: [Title]\n\n## Objectives\n\n## Materials Needed\n\n## Setup Instructions\n\n## Procedure\n\n### Part 1\n1. Step 1\n2. Step 2\n\n### Part 2\n\n## Data Analysis\n\n## Discussion Questions\n\n## Cleanup\n",
                    "metadata": {"type": "lab"},
                },
                suggested_duration=120,
                best_for=["project_based", "inquiry_based", "competency_based"],
            )
        )

    return templates


@router.post("/{material_id}/validate", response_model=ContentValidation)
async def validate_material(
    material_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Validate material content for quality and accessibility.
    """
    # Get material with access check
    material = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    validation = ContentValidation(is_valid=True)

    # Check required fields
    if not material.title:
        validation.errors.append("Title is required")
        validation.is_valid = False

    if not material.content and not material.raw_content:
        validation.errors.append("Content is required")
        validation.is_valid = False

    # Check content length
    if material.raw_content and len(material.raw_content) < 100:
        validation.warnings.append("Content seems too short (less than 100 characters)")

    # Check for learning objectives
    if (
        material.content
        and isinstance(material.content, dict)
        and not material.content.get("learning_objectives")
    ):
        validation.suggestions.append("Consider adding learning objectives")

    # Basic accessibility checks
    if material.raw_content:
        # Check for images without alt text
        # Simplified check - in production would parse markdown properly
        if "![" in material.raw_content and "alt=" not in material.raw_content.lower():
            validation.accessibility_issues.append("Images may be missing alt text")

        # Check for heading structure
        if "# " not in material.raw_content:
            validation.suggestions.append(
                "Consider adding headings to structure the content"
            )

    # Calculate quality score
    quality_score, _ = calculate_quality_score(material)
    validation.quality_score = quality_score

    if quality_score < 50:
        validation.warnings.append(f"Quality score is low ({quality_score:.1f}/100)")

    return validation


@router.get("/{material_id}/analytics", response_model=MaterialAnalytics)
async def get_material_analytics(
    material_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get analytics for a material.
    """
    # Get material with access check
    material = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    # Get version count
    revision_count = (
        db.query(Material)
        .filter(
            or_(
                Material.id == material_id,
                Material.parent_version_id == material_id,
            )
        )
        .count()
    )

    # Calculate quality score
    quality_score, _ = calculate_quality_score(material)

    # Return analytics (in production, would track actual usage)
    return MaterialAnalytics(
        material_id=str(material_id),
        view_count=0,  # Would track actual views
        avg_time_spent_minutes=0.0,  # Would track actual time
        completion_rate=0.0,  # Would track completion
        feedback_score=quality_score,
        revision_count=revision_count,
        last_accessed=material.updated_at,
        engagement_metrics={
            "quality_score": quality_score,
            "has_exercises": bool(
                material.content and material.content.get("exercises")
            ),
            "has_media": bool(material.content and material.content.get("media_urls")),
        },
    )



@router.get("/{material_id}/versions", response_model=list[MaterialVersionHistory])
def get_material_versions(
    material_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> list[MaterialVersionHistory]:
    """
    Get version history for a material.
    """
    # Get the original material
    original = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    # Get all versions (including the original)
    versions = (
        db.query(Material)
        .filter(
            or_(
                Material.id == material_id,
                Material.parent_version_id == material_id,
            )
        )
        .order_by(Material.version.desc())
        .all()
    )

    # Convert to response model
    version_history = []
    for version in versions:
        # Calculate change summary (simplified - in production would do proper diff)
        change_summary = "Initial version"
        if version.parent_version_id:
            change_summary = f"Updated content (version {version.version})"
            if version.generation_context and isinstance(version.generation_context, dict):
                if version.generation_context.get("change_reason"):
                    change_summary = version.generation_context["change_reason"]

        version_history.append(
            MaterialVersionHistory(
                id=str(version.id),
                version=version.version,
                created_at=version.created_at,
                updated_at=version.updated_at,
                is_latest=version.is_latest,
                parent_version_id=str(version.parent_version_id) if version.parent_version_id else None,
                change_summary=change_summary,
                quality_score=version.quality_score or 0,
                teaching_philosophy=version.teaching_philosophy,
            )
        )

    return version_history


@router.get("/{material_id}/versions/{version_id}", response_model=MaterialResponse)
def get_material_version(
    material_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> MaterialResponse:
    """
    Get a specific version of a material.
    """
    # Verify access to the original material
    original = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    # Get the specific version
    version = (
        db.query(Material)
        .filter(Material.id == version_id)
        .filter(
            or_(
                Material.id == material_id,
                Material.parent_version_id == material_id,
            )
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    # Calculate quality score
    quality_score, quality_metrics = calculate_quality_score(version)

    return MaterialResponse(
        id=str(version.id),
        course_id=str(version.course_id),
        module_id=str(version.module_id) if version.module_id else None,
        type=version.type,
        title=version.title,
        description=version.description,
        content=version.content or {},
        raw_content=version.raw_content or "",
        version=version.version,
        parent_version_id=str(version.parent_version_id) if version.parent_version_id else None,
        is_latest=version.is_latest,
        validation_results=version.validation_results,
        quality_score=quality_score,
        quality_metrics=quality_metrics,
        generation_context=version.generation_context,
        teaching_philosophy=version.teaching_philosophy,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


@router.post("/{material_id}/restore/{version_id}", response_model=MaterialResponse)
def restore_material_version(
    material_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> MaterialResponse:
    """
    Restore a previous version of a material by creating a new version with the old content.
    """
    # Verify access
    original = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id)
        .filter(Course.user_id == current_user.id)
        .first()
    )

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or access denied",
        )

    # Get the version to restore
    version_to_restore = (
        db.query(Material)
        .filter(Material.id == version_id)
        .filter(
            or_(
                Material.id == material_id,
                Material.parent_version_id == material_id,
            )
        )
        .first()
    )

    if not version_to_restore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    # Get current latest version to determine new version number
    current_latest = (
        db.query(Material)
        .filter(
            or_(
                Material.id == material_id,
                Material.parent_version_id == material_id,
            )
        )
        .filter(Material.is_latest == True)
        .first()
    )

    # Create new version with content from the old version
    new_version = Material(
        course_id=version_to_restore.course_id,
        module_id=version_to_restore.module_id,
        type=version_to_restore.type,
        title=version_to_restore.title,
        description=version_to_restore.description,
        content=version_to_restore.content,
        raw_content=version_to_restore.raw_content,
        version=(current_latest.version + 1) if current_latest else 1,
        parent_version_id=material_id,
        is_latest=True,
        validation_results=version_to_restore.validation_results,
        quality_score=version_to_restore.quality_score,
        generation_context={
            "restored_from_version": version_to_restore.version,
            "change_reason": f"Restored from version {version_to_restore.version}",
            "restored_at": datetime.utcnow().isoformat(),
        },
        teaching_philosophy=version_to_restore.teaching_philosophy,
    )

    # Mark current latest as not latest
    if current_latest:
        current_latest.is_latest = False

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    # Calculate quality score
    quality_score, quality_metrics = calculate_quality_score(new_version)

    return MaterialResponse(
        id=str(new_version.id),
        course_id=str(new_version.course_id),
        module_id=str(new_version.module_id) if new_version.module_id else None,
        type=new_version.type,
        title=new_version.title,
        description=new_version.description,
        content=new_version.content or {},
        raw_content=new_version.raw_content or "",
        version=new_version.version,
        parent_version_id=str(new_version.parent_version_id) if new_version.parent_version_id else None,
        is_latest=new_version.is_latest,
        validation_results=new_version.validation_results,
        quality_score=quality_score,
        quality_metrics=quality_metrics,
        generation_context=new_version.generation_context,
        teaching_philosophy=new_version.teaching_philosophy,
        created_at=new_version.created_at,
        updated_at=new_version.updated_at,
    )

