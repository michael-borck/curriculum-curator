"""
API endpoints for managing Learning Requirements Documents (LRDs)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.lrd import LRD
from app.schemas.lrd import LRDCreate, LRDListItem, LRDResponse, LRDUpdate
from app.schemas.user import UserResponse
from app.services.lrd_service import lrd_service

router = APIRouter()


@router.get("/units/{unit_id}/lrds", response_model=list[LRDListItem])
async def list_lrds(
    unit_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> list[LRDListItem]:
    """List all LRDs for a unit"""
    lrds = await lrd_service.list_by_unit(db, unit_id)
    return [
        LRDListItem(
            id=str(lrd.id),
            unit_id=str(lrd.unit_id),
            version=lrd.version,
            status=lrd.status,
            created_at=lrd.created_at,
            updated_at=lrd.updated_at,
        )
        for lrd in lrds
    ]


@router.post("/lrds", response_model=LRDResponse, status_code=status.HTTP_201_CREATED)
async def create_lrd(
    lrd_data: LRDCreate,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> LRDResponse:
    """Create a new LRD"""
    try:
        lrd = await lrd_service.create_lrd(db, lrd_data)
        return _lrd_to_response(lrd)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/lrds/{lrd_id}", response_model=LRDResponse)
async def get_lrd(
    lrd_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> LRDResponse:
    """Get a single LRD"""
    lrd = await lrd_service.get_lrd(db, lrd_id)
    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found",
        )
    return _lrd_to_response(lrd)


@router.put("/lrds/{lrd_id}", response_model=LRDResponse)
async def update_lrd(
    lrd_id: str,
    lrd_data: LRDUpdate,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> LRDResponse:
    """Update an LRD"""
    try:
        lrd = await lrd_service.update_lrd(db, lrd_id, lrd_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found",
        )
    return _lrd_to_response(lrd)


@router.delete("/lrds/{lrd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lrd(
    lrd_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> None:
    """Delete an LRD"""
    deleted = await lrd_service.delete_lrd(db, lrd_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found",
        )


@router.post("/lrds/{lrd_id}/submit-review", response_model=LRDResponse)
async def submit_for_review(
    lrd_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> LRDResponse:
    """Submit an LRD for review"""
    try:
        lrd = await lrd_service.submit_for_review(db, lrd_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found",
        )
    return _lrd_to_response(lrd)


@router.post("/lrds/{lrd_id}/clone", response_model=LRDResponse, status_code=status.HTTP_201_CREATED)
async def clone_lrd(
    lrd_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> LRDResponse:
    """Clone an LRD with incremented version"""
    lrd = await lrd_service.clone_lrd(db, lrd_id)
    if not lrd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found",
        )
    return _lrd_to_response(lrd)


@router.post("/lrds/{lrd_id}/generate-tasks")
async def generate_tasks(
    lrd_id: str,
    db: Session = Depends(deps.get_db),
    current_user: UserResponse = Depends(deps.get_current_active_user),
) -> dict[str, object]:
    """Generate a TaskList from LRD content"""
    task_list = await lrd_service.generate_tasks(db, lrd_id)
    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LRD not found",
        )
    return {
        "id": str(task_list.id),
        "lrdId": str(task_list.lrd_id),
        "unitId": str(task_list.unit_id),
        "totalTasks": task_list.total_tasks,
        "completedTasks": task_list.completed_tasks,
        "tasks": task_list.tasks,
        "status": task_list.status,
    }


def _lrd_to_response(lrd: LRD) -> LRDResponse:
    """Convert an LRD model to a response schema"""
    return LRDResponse(
        id=str(lrd.id),
        unit_id=str(lrd.unit_id),
        version=lrd.version,
        status=lrd.status,
        content=lrd.content,
        approval_history=lrd.approval_history,
        created_at=lrd.created_at,
        updated_at=lrd.updated_at,
    )
