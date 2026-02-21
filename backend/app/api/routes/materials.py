"""
API endpoints for managing weekly materials
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.weekly_material import WeeklyMaterial
from app.schemas.learning_outcomes import LLOResponse, ULOResponse
from app.schemas.materials import (
    MaterialCreate,
    MaterialDuplicate,
    MaterialFilter,
    MaterialHistory,
    MaterialMapping,
    MaterialReorder,
    MaterialResponse,
    MaterialRevert,
    MaterialUpdate,
    MaterialVersion,
    MaterialWithOutcomes,
    WeekMaterials,
)
from app.services.git_content_service import get_git_service
from app.services.materials_service import materials_service

router = APIRouter()


# =============================================================================
# Response Helpers
# =============================================================================


def _to_material_response(material: WeeklyMaterial) -> MaterialResponse:
    """Convert a WeeklyMaterial model to MaterialResponse schema."""
    return MaterialResponse(
        id=str(material.id),
        unit_id=str(material.unit_id),
        week_number=material.week_number,
        title=material.title,
        type=material.type,
        description=material.description,
        duration_minutes=material.duration_minutes,
        file_path=material.file_path,
        material_metadata=material.material_metadata,
        order_index=material.order_index,
        status=material.status,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


def _to_ulo_response(ulo: Any) -> ULOResponse:
    """Convert a UnitLearningOutcome model to ULOResponse schema."""
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


def _to_llo_response(llo: Any) -> LLOResponse:
    """Convert a LocalLearningOutcome model to LLOResponse schema."""
    return LLOResponse(
        id=str(llo.id),
        material_id=str(llo.material_id),
        description=llo.description,
        order_index=llo.order_index,
        created_at=llo.created_at,
        updated_at=llo.updated_at,
    )


@router.post("/units/{unit_id}/materials", response_model=MaterialResponse)
async def create_material(
    unit_id: UUID,
    material_data: MaterialCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new weekly material"""
    try:
        material = await materials_service.create_material(
            db=db,
            unit_id=unit_id,
            material_data=material_data,
            user_email=current_user.email,
        )
        return _to_material_response(material)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/units/{unit_id}/materials", response_model=list[MaterialResponse])
async def get_unit_materials(
    unit_id: UUID,
    week_number: int | None = Query(None, ge=1, le=52),
    material_type: str | None = Query(None, alias="type"),
    status: str | None = None,
    search: str | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all materials for a unit with optional filtering"""
    filter_params = MaterialFilter(
        week_number=week_number,
        type=material_type,
        status=status,
        search=search,
    )

    materials = await materials_service.get_materials_by_unit(
        db=db,
        unit_id=unit_id,
        filter_params=filter_params,
    )

    return [_to_material_response(mat) for mat in materials]


@router.get(
    "/units/{unit_id}/weeks/{week_number}/materials", response_model=WeekMaterials
)
async def get_week_materials(
    unit_id: UUID,
    week_number: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all materials for a specific week"""
    materials = await materials_service.get_materials_by_week(
        db=db,
        unit_id=unit_id,
        week_number=week_number,
    )

    summary = await materials_service.get_week_summary(
        db=db,
        unit_id=unit_id,
        week_number=week_number,
    )

    return WeekMaterials(
        week_number=week_number,
        total_duration_minutes=summary["total_duration_minutes"],
        material_count=len(materials),
        materials=[
            MaterialResponse(
                id=str(mat.id),
                unit_id=str(mat.unit_id),
                week_number=mat.week_number,
                title=mat.title,
                type=mat.type,
                description=mat.description,
                duration_minutes=mat.duration_minutes,
                file_path=mat.file_path,
                material_metadata=mat.material_metadata,
                order_index=mat.order_index,
                status=mat.status,
                created_at=mat.created_at,
                updated_at=mat.updated_at,
            )
            for mat in materials
        ],
    )


@router.get("/materials/{material_id}", response_model=MaterialWithOutcomes)
async def get_material(
    material_id: UUID,
    include_outcomes: bool = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific material"""
    material = await materials_service.get_material(
        db=db,
        material_id=material_id,
        include_outcomes=include_outcomes,
    )

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    response = MaterialWithOutcomes(
        id=str(material.id),
        unit_id=str(material.unit_id),
        week_number=material.week_number,
        title=material.title,
        type=material.type,
        description=material.description,
        duration_minutes=material.duration_minutes,
        file_path=material.file_path,
        material_metadata=material.material_metadata,
        order_index=material.order_index,
        status=material.status,
        created_at=material.created_at,
        updated_at=material.updated_at,
        local_outcomes=[],
        mapped_ulos=[],
    )

    # Add outcomes if requested
    if include_outcomes:
        response.local_outcomes = [
            LLOResponse(
                id=str(llo.id),
                material_id=str(llo.material_id),
                description=llo.description,
                order_index=llo.order_index,
                created_at=llo.created_at,
                updated_at=llo.updated_at,
            )
            for llo in getattr(material, "local_outcomes", [])
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
            for ulo in getattr(material, "learning_outcomes", [])
        ]

    return response


@router.put("/materials/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: UUID,
    material_data: MaterialUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a material"""
    try:
        material = await materials_service.update_material(
            db=db,
            material_id=material_id,
            material_data=material_data,
            user_email=current_user.email,
        )

        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found",
            )

        return MaterialResponse(
            id=str(material.id),
            unit_id=str(material.unit_id),
            week_number=material.week_number,
            title=material.title,
            type=material.type,
            description=material.description,
            duration_minutes=material.duration_minutes,
            file_path=material.file_path,
            material_metadata=material.material_metadata,
            order_index=material.order_index,
            status=material.status,
            created_at=material.created_at,
            updated_at=material.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete a material"""
    success = await materials_service.delete_material(
        db=db,
        material_id=material_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    return {"message": "Material deleted successfully"}


@router.post("/materials/{material_id}/duplicate", response_model=MaterialResponse)
async def duplicate_material(
    material_id: UUID,
    duplicate_data: MaterialDuplicate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Duplicate a material to another week"""
    try:
        material = await materials_service.duplicate_material(
            db=db,
            material_id=material_id,
            duplicate_data=duplicate_data,
        )

        return MaterialResponse(
            id=str(material.id),
            unit_id=str(material.unit_id),
            week_number=material.week_number,
            title=material.title,
            type=material.type,
            description=material.description,
            duration_minutes=material.duration_minutes,
            file_path=material.file_path,
            material_metadata=material.material_metadata,
            order_index=material.order_index,
            status=material.status,
            created_at=material.created_at,
            updated_at=material.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/units/{unit_id}/weeks/{week_number}/materials/reorder",
    response_model=list[MaterialResponse],
)
async def reorder_materials(
    unit_id: UUID,
    week_number: int,
    reorder_data: MaterialReorder,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Reorder materials within a week"""
    try:
        materials = await materials_service.reorder_materials(
            db=db,
            unit_id=unit_id,
            week_number=week_number,
            reorder_data=reorder_data,
        )

        return [
            MaterialResponse(
                id=str(mat.id),
                unit_id=str(mat.unit_id),
                week_number=mat.week_number,
                title=mat.title,
                type=mat.type,
                description=mat.description,
                duration_minutes=mat.duration_minutes,
                file_path=mat.file_path,
                material_metadata=mat.material_metadata,
                order_index=mat.order_index,
                status=mat.status,
                created_at=mat.created_at,
                updated_at=mat.updated_at,
            )
            for mat in materials
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.put("/materials/{material_id}/mappings", response_model=MaterialWithOutcomes)
async def update_material_mappings(
    material_id: UUID,
    mapping_data: MaterialMapping,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update ULO mappings for a material"""
    try:
        material = await materials_service.update_ulo_mappings(
            db=db,
            material_id=material_id,
            mapping_data=mapping_data,
        )

        return MaterialWithOutcomes(
            id=str(material.id),
            unit_id=str(material.unit_id),
            week_number=material.week_number,
            title=material.title,
            type=material.type,
            description=material.description,
            duration_minutes=material.duration_minutes,
            file_path=material.file_path,
            material_metadata=material.material_metadata,
            order_index=material.order_index,
            status=material.status,
            created_at=material.created_at,
            updated_at=material.updated_at,
            local_outcomes=[
                LLOResponse(
                    id=str(llo.id),
                    material_id=str(llo.material_id),
                    description=llo.description,
                    order_index=llo.order_index,
                    created_at=llo.created_at,
                    updated_at=llo.updated_at,
                )
                for llo in getattr(material, "local_outcomes", [])
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
                for ulo in getattr(material, "learning_outcomes", [])
            ],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/units/{unit_id}/weeks/{week_number}/summary")
async def get_week_summary(
    unit_id: UUID,
    week_number: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get summary statistics for a week"""
    return await materials_service.get_week_summary(
        db=db,
        unit_id=unit_id,
        week_number=week_number,
    )


# =============================================================================
# Version History Endpoints
# =============================================================================


def _git_path_for_material(material: WeeklyMaterial) -> str:
    """Build the Git-relative path for a material's description file."""
    return f"weeks/week-{int(material.week_number):02d}/material-{material.id}.html"


@router.get("/materials/{material_id}/history", response_model=MaterialHistory)
async def get_material_history(
    material_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get version history for a material's description."""
    material = await materials_service.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    git = get_git_service()
    git_path = _git_path_for_material(material)
    commits = git.get_history(str(material.unit_id), git_path, limit=limit)

    versions = [
        MaterialVersion(
            commit=c["commit"],
            date=c["date"],
            message=c["message"],
            author_email=c.get("author_email"),
        )
        for c in commits
    ]
    return MaterialHistory(material_id=str(material_id), versions=versions)


@router.get("/materials/{material_id}/version/{commit}")
async def get_material_at_version(
    material_id: UUID,
    commit: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get material description at a specific version."""
    material = await materials_service.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    git = get_git_service()
    git_path = _git_path_for_material(material)
    try:
        body = git.get_content(str(material.unit_id), git_path, commit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found") from exc

    return {"commit": commit, "body": body}


@router.get("/materials/{material_id}/diff")
async def get_material_diff(
    material_id: UUID,
    old_commit: str = Query(...),
    new_commit: str = Query("HEAD"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get diff between two versions of a material's description."""
    material = await materials_service.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    git = get_git_service()
    git_path = _git_path_for_material(material)
    diff = git.diff(str(material.unit_id), git_path, old_commit, new_commit)

    return {
        "materialId": str(material_id),
        "oldCommit": old_commit,
        "newCommit": new_commit,
        "diff": diff,
    }


@router.post("/materials/{material_id}/revert", response_model=MaterialResponse)
async def revert_material(
    material_id: UUID,
    data: MaterialRevert,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Revert material description to a previous version."""
    material = await materials_service.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    git = get_git_service()
    git_path = _git_path_for_material(material)

    try:
        old_body = git.get_content(str(material.unit_id), git_path, data.commit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found") from exc

    # Update DB
    material.description = old_body
    db.commit()
    db.refresh(material)

    # Create new Git commit for the revert
    git.save_content(
        unit_id=str(material.unit_id),
        path=git_path,
        content=old_body,
        user_email=current_user.email,
        message=f"Reverted {material.title} to {data.commit[:8]}",
    )

    return _to_material_response(material)
