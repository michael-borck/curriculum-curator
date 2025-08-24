"""
API endpoints for managing learning outcomes
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.learning_outcomes import (
    ALOCreate,
    ALOResponse,
    BulkULOCreate,
    LLOCreate,
    LLOResponse,
    OutcomeReorder,
    ULOCreate,
    ULOResponse,
    ULOUpdate,
    ULOWithMappings,
)
from app.services.materials_service import materials_service
from app.services.ulo_service import ulo_service

router = APIRouter()


# Unit Learning Outcomes (ULOs)
@router.post("/units/{unit_id}/ulos", response_model=ULOResponse)
async def create_ulo(
    unit_id: UUID,
    ulo_data: ULOCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new Unit Learning Outcome"""
    try:
        ulo = await ulo_service.create_ulo(
            db=db,
            unit_id=unit_id,
            ulo_data=ulo_data,
            user_id=current_user.id,
        )
        return ULOResponse(
            id=str(ulo.id),
            unit_id=str(ulo.unit_id),
            code=ulo.outcome_code,
            description=ulo.outcome_text,
            bloom_level=ulo.bloom_level,
            order_index=ulo.sequence_order,
            created_at=ulo.created_at,
            updated_at=ulo.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/units/{unit_id}/ulos", response_model=list[ULOWithMappings])
async def get_unit_ulos(
    unit_id: UUID,
    include_mappings: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all ULOs for a unit"""
    ulos = await ulo_service.get_ulos_by_unit(
        db=db,
        unit_id=unit_id,
        include_mappings=include_mappings,
    )

    result = []
    for ulo in ulos:
        ulo_response = ULOWithMappings(
            id=str(ulo.id),
            unit_id=str(ulo.unit_id),
            code=ulo.outcome_code,
            description=ulo.outcome_text,
            bloom_level=ulo.bloom_level,
            order_index=ulo.sequence_order,
            created_at=ulo.created_at,
            updated_at=ulo.updated_at,
            material_count=len(getattr(ulo, "materials", [])),
            assessment_count=len(getattr(ulo, "assessments", [])),
        )
        result.append(ulo_response)

    return result


@router.get("/ulos/{ulo_id}", response_model=ULOResponse)
async def get_ulo(
    ulo_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific ULO"""
    ulo = await ulo_service.get_ulo(db=db, ulo_id=ulo_id)

    if not ulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ULO not found",
        )

    return ULOResponse(
        id=str(ulo.id),
        unit_id=str(ulo.unit_id),
        code=ulo.outcome_code,
        description=ulo.outcome_text,
        bloom_level=ulo.bloom_level,
        order_index=ulo.sequence_order,
        created_at=ulo.created_at,
        updated_at=ulo.updated_at,
    )


@router.put("/ulos/{ulo_id}", response_model=ULOResponse)
async def update_ulo(
    ulo_id: UUID,
    ulo_data: ULOUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a ULO"""
    try:
        ulo = await ulo_service.update_ulo(
            db=db,
            ulo_id=ulo_id,
            ulo_data=ulo_data,
        )

        if not ulo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ULO not found",
            )

        return ULOResponse(
            id=str(ulo.id),
            unit_id=str(ulo.unit_id),
            code=ulo.outcome_code,
            description=ulo.outcome_text,
            bloom_level=ulo.bloom_level,
            order_index=ulo.sequence_order,
            created_at=ulo.created_at,
            updated_at=ulo.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/ulos/{ulo_id}")
async def delete_ulo(
    ulo_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete a ULO"""
    try:
        success = await ulo_service.delete_ulo(db=db, ulo_id=ulo_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ULO not found",
            )

        return {"message": "ULO deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/units/{unit_id}/ulos/reorder", response_model=list[ULOResponse])
async def reorder_ulos(
    unit_id: UUID,
    reorder_data: OutcomeReorder,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Reorder ULOs for a unit"""
    try:
        ulos = await ulo_service.reorder_ulos(
            db=db,
            unit_id=unit_id,
            reorder_data=reorder_data,
        )

        return [
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
            for ulo in ulos
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/units/{unit_id}/ulos/bulk", response_model=list[ULOResponse])
async def bulk_create_ulos(
    unit_id: UUID,
    bulk_data: BulkULOCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create multiple ULOs at once"""
    try:
        ulos = await ulo_service.bulk_create_ulos(
            db=db,
            unit_id=unit_id,
            bulk_data=bulk_data,
            user_id=current_user.id,
        )

        return [
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
            for ulo in ulos
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/units/{unit_id}/ulos/coverage")
async def get_ulo_coverage(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get ULO coverage statistics for a unit"""
    return await ulo_service.get_ulo_coverage(db=db, unit_id=unit_id)


# Local Learning Outcomes (LLOs) - Material-specific
@router.post("/materials/{material_id}/outcomes", response_model=LLOResponse)
async def add_material_outcome(
    material_id: UUID,
    outcome_data: LLOCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Add a local learning outcome to a material"""
    try:
        llo = await materials_service.add_local_outcome(
            db=db,
            material_id=material_id,
            outcome_data=outcome_data,
        )

        return LLOResponse(
            id=str(llo.id),
            material_id=str(llo.material_id),
            description=llo.description,
            order_index=llo.order_index,
            created_at=llo.created_at,
            updated_at=llo.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# Assessment Learning Outcomes (ALOs)
@router.post("/assessments/{assessment_id}/outcomes", response_model=ALOResponse)
async def add_assessment_outcome(
    assessment_id: UUID,
    outcome_data: ALOCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Add an assessment-specific learning outcome"""
    # Import here to avoid circular dependency
    from app.services.assessments_service import assessments_service  # noqa: PLC0415

    try:
        alo = await assessments_service.add_assessment_outcome(
            db=db,
            assessment_id=assessment_id,
            outcome_data=outcome_data,
        )

        return ALOResponse(
            id=str(alo.id),
            assessment_id=str(alo.assessment_id),
            description=alo.description,
            order_index=alo.order_index,
            created_at=alo.created_at,
            updated_at=alo.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
