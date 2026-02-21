"""
API endpoints for managing Learning Designs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.learning_design import LearningDesign
from app.schemas.learning_design import (
    DesignCreate,
    DesignListItem,
    DesignResponse,
    DesignUpdate,
)
from app.schemas.user import UserResponse
from app.services.design_service import design_service

router = APIRouter()


@router.get("/units/{unit_id}/designs", response_model=list[DesignListItem])
async def list_designs(
    unit_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> list[DesignListItem]:
    """List all learning designs for a unit"""
    designs = await design_service.list_by_unit(db, unit_id)
    return [
        DesignListItem(
            id=str(design.id),
            unit_id=str(design.unit_id),
            version=design.version,
            status=design.status,
            created_at=design.created_at,
            updated_at=design.updated_at,
        )
        for design in designs
    ]


@router.post(
    "/designs", response_model=DesignResponse, status_code=status.HTTP_201_CREATED
)
async def create_design(
    design_data: DesignCreate,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> DesignResponse:
    """Create a new learning design"""
    try:
        design = await design_service.create_design(db, design_data)
        return _to_response(design)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/designs/{design_id}", response_model=DesignResponse)
async def get_design(
    design_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> DesignResponse:
    """Get a single learning design"""
    design = await design_service.get_design(db, design_id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning design not found",
        )
    return _to_response(design)


@router.put("/designs/{design_id}", response_model=DesignResponse)
async def update_design(
    design_id: str,
    design_data: DesignUpdate,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> DesignResponse:
    """Update a learning design"""
    try:
        design = await design_service.update_design(db, design_id, design_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning design not found",
        )
    return _to_response(design)


@router.delete("/designs/{design_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_design(
    design_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> None:
    """Delete a learning design"""
    deleted = await design_service.delete_design(db, design_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning design not found",
        )


@router.post("/designs/{design_id}/submit-review", response_model=DesignResponse)
async def submit_for_review(
    design_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> DesignResponse:
    """Submit a learning design for review"""
    try:
        design = await design_service.submit_for_review(db, design_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning design not found",
        )
    return _to_response(design)


@router.post(
    "/designs/{design_id}/clone",
    response_model=DesignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_design(
    design_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> DesignResponse:
    """Clone a learning design with incremented version"""
    design = await design_service.clone_design(db, design_id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning design not found",
        )
    return _to_response(design)


@router.post("/designs/{design_id}/generate-tasks")
async def generate_tasks(
    design_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> dict[str, object]:
    """Generate a TaskList from learning design content"""
    task_list = await design_service.generate_tasks(db, design_id)
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning design not found",
        )
    return {
        "id": str(task_list.id),
        "designId": str(task_list.design_id),
        "unitId": str(task_list.unit_id),
        "totalTasks": task_list.total_tasks,
        "completedTasks": task_list.completed_tasks,
        "tasks": task_list.tasks,
        "status": task_list.status,
    }


def _to_response(design: LearningDesign) -> DesignResponse:
    """Convert a LearningDesign model to a response schema"""
    return DesignResponse(
        id=str(design.id),
        unit_id=str(design.unit_id),
        version=design.version,
        status=design.status,
        content=design.content,
        approval_history=design.approval_history,
        created_at=design.created_at,
        updated_at=design.updated_at,
    )
