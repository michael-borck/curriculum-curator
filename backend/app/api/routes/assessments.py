"""
API endpoints for managing assessments
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.assessments import (
    AssessmentCreate,
    AssessmentFilter,
    AssessmentMapping,
    AssessmentMaterialLink,
    AssessmentResponse,
    AssessmentTimeline,
    AssessmentUpdate,
    AssessmentWithOutcomes,
    GradeDistribution,
)
from app.schemas.learning_outcomes import ALOResponse, ULOResponse
from app.services.assessments_service import assessments_service

router = APIRouter()


@router.post("/units/{unit_id}/assessments", response_model=AssessmentResponse)
async def create_assessment(
    unit_id: UUID,
    assessment_data: AssessmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new assessment"""
    try:
        assessment = await assessments_service.create_assessment(
            db=db,
            unit_id=unit_id,
            assessment_data=assessment_data,
        )

        return AssessmentResponse(
            id=str(assessment.id),
            unit_id=str(assessment.unit_id),
            title=assessment.title,
            type=assessment.type,
            category=assessment.category,
            weight=assessment.weight,
            description=assessment.description,
            specification=assessment.specification,
            release_week=assessment.release_week,
            release_date=assessment.release_date,
            due_week=assessment.due_week,
            due_date=assessment.due_date,
            duration=assessment.duration,
            rubric=assessment.rubric,
            questions=assessment.questions,
            word_count=assessment.word_count,
            group_work=assessment.group_work,
            submission_type=assessment.submission_type,
            status=assessment.status,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/units/{unit_id}/assessments", response_model=list[AssessmentResponse])
async def get_unit_assessments(
    unit_id: UUID,
    assessment_type: str | None = Query(None, alias="type"),
    category: str | None = None,
    status: str | None = None,
    release_week: int | None = Query(None, ge=1, le=52),
    due_week: int | None = Query(None, ge=1, le=52),
    search: str | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all assessments for a unit with optional filtering"""
    filter_params = AssessmentFilter(
        type=assessment_type,
        category=category,
        status=status,
        release_week=release_week,
        due_week=due_week,
        search=search,
    )

    assessments = await assessments_service.get_assessments_by_unit(
        db=db,
        unit_id=unit_id,
        filter_params=filter_params,
    )

    return [
        AssessmentResponse(
            id=str(a.id),
            unit_id=str(a.unit_id),
            title=a.title,
            type=a.type,
            category=a.category,
            weight=a.weight,
            description=a.description,
            specification=a.specification,
            release_week=a.release_week,
            release_date=a.release_date,
            due_week=a.due_week,
            due_date=a.due_date,
            duration=a.duration,
            rubric=a.rubric,
            questions=a.questions,
            word_count=a.word_count,
            group_work=a.group_work,
            submission_type=a.submission_type,
            status=a.status,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in assessments
    ]


@router.get("/assessments/{assessment_id}", response_model=AssessmentWithOutcomes)
async def get_assessment(
    assessment_id: UUID,
    include_outcomes: bool = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific assessment"""
    assessment = await assessments_service.get_assessment(
        db=db,
        assessment_id=assessment_id,
        include_outcomes=include_outcomes,
    )

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    response = AssessmentWithOutcomes(
        id=str(assessment.id),
        unit_id=str(assessment.unit_id),
        title=assessment.title,
        type=assessment.type,
        category=assessment.category,
        weight=assessment.weight,
        description=assessment.description,
        specification=assessment.specification,
        release_week=assessment.release_week,
        release_date=assessment.release_date,
        due_week=assessment.due_week,
        due_date=assessment.due_date,
        duration=assessment.duration,
        rubric=assessment.rubric,
        questions=assessment.questions,
        word_count=assessment.word_count,
        group_work=assessment.group_work,
        submission_type=assessment.submission_type,
        status=assessment.status,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        assessment_outcomes=[],
        mapped_ulos=[],
        linked_materials=[],
    )

    # Add outcomes if requested
    if include_outcomes:
        response.assessment_outcomes = [
            ALOResponse(
                id=str(alo.id),
                assessment_id=str(alo.assessment_id),
                description=alo.description,
                order_index=alo.order_index,
                created_at=alo.created_at,
                updated_at=alo.updated_at,
            )
            for alo in getattr(assessment, "assessment_outcomes", [])
        ]

        response.mapped_ulos = [
            ULOResponse(
                id=str(ulo.id),
                unit_id=str(ulo.unit_id),
                code=ulo.outcome_code,
                description=ulo.outcome_text,
                bloom_level=ulo.bloom_level,
                order_index=ulo.sequence_order,
                created_at=ulo.created_at,
                updated_at=ulo.updated_at,
            )
            for ulo in getattr(assessment, "learning_outcomes", [])
        ]

        response.linked_materials = [
            str(mat.id) for mat in getattr(assessment, "linked_materials", [])
        ]

    return response


@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: UUID,
    assessment_data: AssessmentUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update an assessment"""
    try:
        assessment = await assessments_service.update_assessment(
            db=db,
            assessment_id=assessment_id,
            assessment_data=assessment_data,
        )

        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found",
            )

        return AssessmentResponse(
            id=str(assessment.id),
            unit_id=str(assessment.unit_id),
            title=assessment.title,
            type=assessment.type,
            category=assessment.category,
            weight=assessment.weight,
            description=assessment.description,
            specification=assessment.specification,
            release_week=assessment.release_week,
            release_date=assessment.release_date,
            due_week=assessment.due_week,
            due_date=assessment.due_date,
            duration=assessment.duration,
            rubric=assessment.rubric,
            questions=assessment.questions,
            word_count=assessment.word_count,
            group_work=assessment.group_work,
            submission_type=assessment.submission_type,
            status=assessment.status,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete an assessment"""
    success = await assessments_service.delete_assessment(
        db=db,
        assessment_id=assessment_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    return {"message": "Assessment deleted successfully"}


@router.get("/units/{unit_id}/assessments/grade-distribution", response_model=GradeDistribution)
async def get_grade_distribution(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get grade distribution for a unit"""
    return await assessments_service.calculate_grade_distribution(
        db=db,
        unit_id=unit_id,
    )


@router.get("/units/{unit_id}/assessments/validate-weights")
async def validate_assessment_weights(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Validate assessment weights for a unit"""
    return await assessments_service.validate_weights(
        db=db,
        unit_id=unit_id,
    )


@router.get("/units/{unit_id}/assessments/timeline", response_model=list[AssessmentTimeline])
async def get_assessment_timeline(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get assessment timeline for a unit"""
    timeline = await assessments_service.get_assessment_timeline(
        db=db,
        unit_id=unit_id,
    )

    return [
        AssessmentTimeline(
            week_number=week_data["week_number"],
            assessments=[
                AssessmentResponse(
                    id=a["id"],
                    unit_id=str(unit_id),
                    title=a["title"],
                    type=a["type"],
                    category=a["category"],
                    weight=a["weight"],
                    due_date=a.get("due_date"),
                    # Default values for required fields not in timeline
                    description=None,
                    specification=None,
                    release_week=None,
                    release_date=None,
                    due_week=week_data["week_number"],
                    duration=None,
                    rubric=None,
                    questions=None,
                    word_count=None,
                    group_work=False,
                    submission_type=None,
                    status="draft",
                    created_at=None,
                    updated_at=None,
                )
                for a in week_data["assessments"]
            ],
            total_weight=week_data["total_weight"],
        )
        for week_data in timeline
    ]


@router.get("/units/{unit_id}/assessments/workload")
async def get_assessment_workload(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Analyze assessment workload distribution"""
    return await assessments_service.get_assessment_workload(
        db=db,
        unit_id=unit_id,
    )


@router.put("/assessments/{assessment_id}/mappings", response_model=AssessmentWithOutcomes)
async def update_assessment_mappings(
    assessment_id: UUID,
    mapping_data: AssessmentMapping,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update ULO mappings for an assessment"""
    try:
        assessment = await assessments_service.update_ulo_mappings(
            db=db,
            assessment_id=assessment_id,
            mapping_data=mapping_data,
        )

        return AssessmentWithOutcomes(
            id=str(assessment.id),
            unit_id=str(assessment.unit_id),
            title=assessment.title,
            type=assessment.type,
            category=assessment.category,
            weight=assessment.weight,
            description=assessment.description,
            specification=assessment.specification,
            release_week=assessment.release_week,
            release_date=assessment.release_date,
            due_week=assessment.due_week,
            due_date=assessment.due_date,
            duration=assessment.duration,
            rubric=assessment.rubric,
            questions=assessment.questions,
            word_count=assessment.word_count,
            group_work=assessment.group_work,
            submission_type=assessment.submission_type,
            status=assessment.status,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            assessment_outcomes=[
                ALOResponse(
                    id=str(alo.id),
                    assessment_id=str(alo.assessment_id),
                    description=alo.description,
                    order_index=alo.order_index,
                    created_at=alo.created_at,
                    updated_at=alo.updated_at,
                )
                for alo in getattr(assessment, "assessment_outcomes", [])
            ],
            mapped_ulos=[
                ULOResponse(
                    id=str(ulo.id),
                    unit_id=str(ulo.unit_id),
                    code=ulo.outcome_code,
                    description=ulo.outcome_text,
                    bloom_level=ulo.bloom_level,
                    order_index=ulo.sequence_order,
                    created_at=ulo.created_at,
                    updated_at=ulo.updated_at,
                )
                for ulo in getattr(assessment, "learning_outcomes", [])
            ],
            linked_materials=[
                str(mat.id) for mat in getattr(assessment, "linked_materials", [])
            ],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put("/assessments/{assessment_id}/materials", response_model=AssessmentWithOutcomes)
async def update_assessment_materials(
    assessment_id: UUID,
    link_data: AssessmentMaterialLink,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update material links for an assessment"""
    try:
        assessment = await assessments_service.update_material_links(
            db=db,
            assessment_id=assessment_id,
            link_data=link_data,
        )

        return AssessmentWithOutcomes(
            id=str(assessment.id),
            unit_id=str(assessment.unit_id),
            title=assessment.title,
            type=assessment.type,
            category=assessment.category,
            weight=assessment.weight,
            description=assessment.description,
            specification=assessment.specification,
            release_week=assessment.release_week,
            release_date=assessment.release_date,
            due_week=assessment.due_week,
            due_date=assessment.due_date,
            duration=assessment.duration,
            rubric=assessment.rubric,
            questions=assessment.questions,
            word_count=assessment.word_count,
            group_work=assessment.group_work,
            submission_type=assessment.submission_type,
            status=assessment.status,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            assessment_outcomes=[
                ALOResponse(
                    id=str(alo.id),
                    assessment_id=str(alo.assessment_id),
                    description=alo.description,
                    order_index=alo.order_index,
                    created_at=alo.created_at,
                    updated_at=alo.updated_at,
                )
                for alo in getattr(assessment, "assessment_outcomes", [])
            ],
            mapped_ulos=[
                ULOResponse(
                    id=str(ulo.id),
                    unit_id=str(ulo.unit_id),
                    code=ulo.outcome_code,
                    description=ulo.outcome_text,
                    bloom_level=ulo.bloom_level,
                    order_index=ulo.sequence_order,
                    created_at=ulo.created_at,
                    updated_at=ulo.updated_at,
                )
                for ulo in getattr(assessment, "learning_outcomes", [])
            ],
            linked_materials=[
                str(mat.id) for mat in getattr(assessment, "linked_materials", [])
            ],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
