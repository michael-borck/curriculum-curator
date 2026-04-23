"""API routes for CLO Sets."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.clo_sets import (
    BulkULOCLOMappingCreate,
    CLOItemCreate,
    CLOItemReorder,
    CLOItemResponse,
    CLOItemUpdate,
    CLOSetCreate,
    CLOSetResponse,
    CLOSetUpdate,
    CLOSuggestionsResponse,
    ULOCLOMappingResponse,
)
from app.services.clo_set_service import clo_set_service

router = APIRouter()


# ── CLO Set CRUD ──────────────────────────────────────────────


@router.get("", response_model=list[CLOSetResponse])
async def list_clo_sets(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return clo_set_service.list_clo_sets(db, UUID(current_user.id))


@router.post("", response_model=CLOSetResponse, status_code=status.HTTP_201_CREATED)
async def create_clo_set(
    data: CLOSetCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return clo_set_service.create_clo_set(db, UUID(current_user.id), data)


@router.get("/{set_id}", response_model=CLOSetResponse)
async def get_clo_set(
    set_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    clo_set = clo_set_service.get_clo_set(db, set_id, UUID(current_user.id))
    if not clo_set:
        raise HTTPException(status_code=404, detail="CLO set not found")
    return clo_set


@router.put("/{set_id}", response_model=CLOSetResponse)
async def update_clo_set(
    set_id: UUID,
    data: CLOSetUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    clo_set = clo_set_service.update_clo_set(db, set_id, UUID(current_user.id), data)
    if not clo_set:
        raise HTTPException(status_code=404, detail="CLO set not found")
    return clo_set


@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clo_set(
    set_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    deleted = clo_set_service.delete_clo_set(db, set_id, UUID(current_user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="CLO set not found")


# ── CLO Items ─────────────────────────────────────────────────


@router.post(
    "/{set_id}/items",
    response_model=CLOItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_clo_item(
    set_id: UUID,
    data: CLOItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    item = clo_set_service.add_clo_item(db, set_id, UUID(current_user.id), data)
    if not item:
        raise HTTPException(status_code=404, detail="CLO set not found")
    return item


@router.put("/{set_id}/items/{item_id}", response_model=CLOItemResponse)
async def update_clo_item(
    set_id: UUID,
    item_id: UUID,
    data: CLOItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    clo_set = clo_set_service.get_clo_set(db, set_id, UUID(current_user.id))
    if not clo_set:
        raise HTTPException(status_code=404, detail="CLO set not found")
    item = clo_set_service.update_clo_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="CLO item not found")
    return item


@router.delete("/{set_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clo_item(
    set_id: UUID,
    item_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    clo_set = clo_set_service.get_clo_set(db, set_id, UUID(current_user.id))
    if not clo_set:
        raise HTTPException(status_code=404, detail="CLO set not found")
    deleted = clo_set_service.delete_clo_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="CLO item not found")


@router.post("/{set_id}/items/reorder", response_model=list[CLOItemResponse])
async def reorder_clo_items(
    set_id: UUID,
    data: CLOItemReorder,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    items = clo_set_service.reorder_clo_items(
        db, set_id, UUID(current_user.id), data.item_ids
    )
    if not items:
        raise HTTPException(status_code=404, detail="CLO set not found")
    return items


# ── Unit assignments ──────────────────────────────────────────


@router.get("/units/{unit_id}/clo-sets", response_model=list[CLOSetResponse])
async def get_unit_clo_sets(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return clo_set_service.get_unit_clo_sets(db, unit_id)


@router.post(
    "/units/{unit_id}/clo-sets/{set_id}",
    status_code=status.HTTP_201_CREATED,
)
async def assign_clo_set_to_unit(
    unit_id: UUID,
    set_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    assignment = clo_set_service.assign_clo_set(db, unit_id, set_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="CLO set not found")
    return {"status": "assigned"}


@router.delete(
    "/units/{unit_id}/clo-sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def unassign_clo_set_from_unit(
    unit_id: UUID,
    set_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    clo_set_service.unassign_clo_set(db, unit_id, set_id)


# ── ULO → CLO mappings ────────────────────────────────────────


@router.get("/ulos/{ulo_id}/clo-mappings", response_model=list[ULOCLOMappingResponse])
async def get_ulo_clo_mappings(
    ulo_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return clo_set_service.get_ulo_clo_mappings(db, ulo_id)


@router.put("/ulos/{ulo_id}/clo-mappings", response_model=list[ULOCLOMappingResponse])
async def set_ulo_clo_mappings(
    ulo_id: UUID,
    data: BulkULOCLOMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return clo_set_service.set_ulo_clo_mappings(
        db, ulo_id, data.clo_item_ids, data.is_ai_suggested
    )


@router.post(
    "/units/{unit_id}/clo-suggestions", response_model=CLOSuggestionsResponse
)
async def suggest_clo_mappings(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    suggestions = await clo_set_service.suggest_clo_mappings(
        db, unit_id, current_user, db
    )
    return CLOSuggestionsResponse(
        suggestions=suggestions,
        message=f"Found {len(suggestions)} suggested mappings",
    )
