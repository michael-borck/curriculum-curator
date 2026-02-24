"""
API endpoints for accreditation mappings (Graduate Capabilities, AoL, SDGs, PLOs)
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api import deps
from app.models.accreditation_mappings import (
    ULOGraduateCapabilityMapping,
    UnitAoLMapping,
    UnitSDGMapping,
)
from app.models.custom_alignment_framework import (
    CustomAlignmentFramework,
    FrameworkItem,
    ULOFrameworkItemMapping,
)
from app.models.learning_outcome import UnitLearningOutcome
from app.models.unit import Unit
from app.models.user import User
from app.schemas.accreditation import (
    AoLMappingCreate,
    AoLMappingResponse,
    AoLMappingSummary,
    BulkAoLMappingCreate,
    BulkGraduateCapabilityMappingCreate,
    BulkSDGMappingCreate,
    GraduateCapabilityMappingCreate,
    GraduateCapabilityMappingResponse,
    SDGMappingCreate,
    SDGMappingResponse,
    SDGMappingSummary,
)
from app.schemas.custom_framework import (
    BulkULOItemMappingCreate,
    FrameworkCreate,
    FrameworkItemCreate,
    FrameworkItemResponse,
    FrameworkItemUpdate,
    FrameworkResponse,
    FrameworkSummary,
    FrameworkUpdate,
    ULOItemMappingResponse,
)

router = APIRouter()


# ============= Graduate Capability Mappings (ULO-level) =============


@router.get(
    "/ulos/{ulo_id}/graduate-capabilities",
    response_model=list[GraduateCapabilityMappingResponse],
)
async def get_ulo_graduate_capabilities(
    ulo_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all Graduate Capability mappings for a ULO"""
    # Verify ULO exists
    ulo = db.execute(
        select(UnitLearningOutcome).where(UnitLearningOutcome.id == str(ulo_id))
    ).scalar_one_or_none()

    if not ulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ULO not found",
        )

    mappings = (
        db.execute(
            select(ULOGraduateCapabilityMapping).where(
                ULOGraduateCapabilityMapping.ulo_id == str(ulo_id)
            )
        )
        .scalars()
        .all()
    )

    return [
        GraduateCapabilityMappingResponse(
            id=str(m.id),
            ulo_id=str(m.ulo_id),
            capability_code=m.capability_code,
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in mappings
    ]


@router.post(
    "/ulos/{ulo_id}/graduate-capabilities",
    response_model=GraduateCapabilityMappingResponse,
)
async def add_ulo_graduate_capability(
    ulo_id: UUID,
    mapping_data: GraduateCapabilityMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Add a Graduate Capability mapping to a ULO"""
    # Verify ULO exists
    ulo = db.execute(
        select(UnitLearningOutcome).where(UnitLearningOutcome.id == str(ulo_id))
    ).scalar_one_or_none()

    if not ulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ULO not found",
        )

    # Check if mapping already exists
    existing = db.execute(
        select(ULOGraduateCapabilityMapping).where(
            ULOGraduateCapabilityMapping.ulo_id == str(ulo_id),
            ULOGraduateCapabilityMapping.capability_code
            == mapping_data.capability_code.value,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ULO already mapped to {mapping_data.capability_code.value}",
        )

    # Create mapping
    mapping = ULOGraduateCapabilityMapping(
        ulo_id=str(ulo_id),
        capability_code=mapping_data.capability_code.value,
        is_ai_suggested=mapping_data.is_ai_suggested,
        notes=mapping_data.notes,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return GraduateCapabilityMappingResponse(
        id=str(mapping.id),
        ulo_id=str(mapping.ulo_id),
        capability_code=mapping.capability_code,
        is_ai_suggested=mapping.is_ai_suggested,
        notes=mapping.notes,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


@router.put(
    "/ulos/{ulo_id}/graduate-capabilities",
    response_model=list[GraduateCapabilityMappingResponse],
)
async def update_ulo_graduate_capabilities(
    ulo_id: UUID,
    bulk_data: BulkGraduateCapabilityMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Replace all Graduate Capability mappings for a ULO"""
    # Verify ULO exists
    ulo = db.execute(
        select(UnitLearningOutcome).where(UnitLearningOutcome.id == str(ulo_id))
    ).scalar_one_or_none()

    if not ulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ULO not found",
        )

    # Delete existing mappings
    db.execute(
        delete(ULOGraduateCapabilityMapping).where(
            ULOGraduateCapabilityMapping.ulo_id == str(ulo_id)
        )
    )

    # Create new mappings
    new_mappings = []
    for code in bulk_data.capability_codes:
        mapping = ULOGraduateCapabilityMapping(
            ulo_id=str(ulo_id),
            capability_code=code.value,
            is_ai_suggested=bulk_data.is_ai_suggested,
        )
        db.add(mapping)
        new_mappings.append(mapping)

    db.commit()

    # Refresh all mappings
    for m in new_mappings:
        db.refresh(m)

    return [
        GraduateCapabilityMappingResponse(
            id=str(m.id),
            ulo_id=str(m.ulo_id),
            capability_code=m.capability_code,
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in new_mappings
    ]


@router.delete("/ulos/{ulo_id}/graduate-capabilities/{capability_code}")
async def remove_ulo_graduate_capability(
    ulo_id: UUID,
    capability_code: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Remove a Graduate Capability mapping from a ULO"""
    # First check if mapping exists
    existing = db.execute(
        select(ULOGraduateCapabilityMapping).where(
            ULOGraduateCapabilityMapping.ulo_id == str(ulo_id),
            ULOGraduateCapabilityMapping.capability_code == capability_code.upper(),
        )
    ).scalar_one_or_none()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found",
        )

    db.delete(existing)
    db.commit()

    return {"message": "Mapping removed successfully"}


# ============= AoL Mappings (Unit-level) =============


@router.get("/units/{unit_id}/aol-mappings", response_model=AoLMappingSummary)
async def get_unit_aol_mappings(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all AoL mappings for a unit"""
    # Verify unit exists
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )

    mappings = (
        db.execute(select(UnitAoLMapping).where(UnitAoLMapping.unit_id == str(unit_id)))
        .scalars()
        .all()
    )

    mapping_responses = [
        AoLMappingResponse(
            id=str(m.id),
            unit_id=str(m.unit_id),
            competency_code=m.competency_code,
            level=m.level,
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in mappings
    ]

    return AoLMappingSummary(
        unit_id=str(unit_id),
        mapped_count=len(mapping_responses),
        total_competencies=7,
        mappings=mapping_responses,
    )


@router.post("/units/{unit_id}/aol-mappings", response_model=AoLMappingResponse)
async def add_unit_aol_mapping(
    unit_id: UUID,
    mapping_data: AoLMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Add an AoL mapping to a unit"""
    # Verify unit exists
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )

    # Check if mapping already exists for this competency
    existing = db.execute(
        select(UnitAoLMapping).where(
            UnitAoLMapping.unit_id == str(unit_id),
            UnitAoLMapping.competency_code == mapping_data.competency_code.value,
        )
    ).scalar_one_or_none()

    if existing:
        # Update existing mapping
        existing.level = mapping_data.level.value
        existing.is_ai_suggested = mapping_data.is_ai_suggested
        existing.notes = mapping_data.notes
        db.commit()
        db.refresh(existing)
        mapping = existing
    else:
        # Create new mapping
        mapping = UnitAoLMapping(
            unit_id=str(unit_id),
            competency_code=mapping_data.competency_code.value,
            level=mapping_data.level.value,
            is_ai_suggested=mapping_data.is_ai_suggested,
            notes=mapping_data.notes,
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)

    return AoLMappingResponse(
        id=str(mapping.id),
        unit_id=str(mapping.unit_id),
        competency_code=mapping.competency_code,
        level=mapping.level,
        is_ai_suggested=mapping.is_ai_suggested,
        notes=mapping.notes,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


@router.put("/units/{unit_id}/aol-mappings", response_model=AoLMappingSummary)
async def update_unit_aol_mappings(
    unit_id: UUID,
    bulk_data: BulkAoLMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Replace all AoL mappings for a unit"""
    # Verify unit exists
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )

    # Delete existing mappings
    db.execute(delete(UnitAoLMapping).where(UnitAoLMapping.unit_id == str(unit_id)))

    # Create new mappings
    new_mappings = []
    for mapping_data in bulk_data.mappings:
        mapping = UnitAoLMapping(
            unit_id=str(unit_id),
            competency_code=mapping_data.competency_code.value,
            level=mapping_data.level.value,
            is_ai_suggested=mapping_data.is_ai_suggested,
            notes=mapping_data.notes,
        )
        db.add(mapping)
        new_mappings.append(mapping)

    db.commit()

    # Refresh all mappings
    for m in new_mappings:
        db.refresh(m)

    mapping_responses = [
        AoLMappingResponse(
            id=str(m.id),
            unit_id=str(m.unit_id),
            competency_code=m.competency_code,
            level=m.level,
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in new_mappings
    ]

    return AoLMappingSummary(
        unit_id=str(unit_id),
        mapped_count=len(mapping_responses),
        total_competencies=7,
        mappings=mapping_responses,
    )


@router.delete("/units/{unit_id}/aol-mappings/{competency_code}")
async def remove_unit_aol_mapping(
    unit_id: UUID,
    competency_code: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Remove an AoL mapping from a unit"""
    # First check if mapping exists
    existing = db.execute(
        select(UnitAoLMapping).where(
            UnitAoLMapping.unit_id == str(unit_id),
            UnitAoLMapping.competency_code == competency_code.upper(),
        )
    ).scalar_one_or_none()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found",
        )

    db.delete(existing)
    db.commit()

    return {"message": "Mapping removed successfully"}


# ============= SDG Mappings (Unit-level) =============


@router.get("/units/{unit_id}/sdg-mappings", response_model=SDGMappingSummary)
async def get_unit_sdg_mappings(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all SDG mappings for a unit"""
    # Verify unit exists
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )

    mappings = (
        db.execute(select(UnitSDGMapping).where(UnitSDGMapping.unit_id == str(unit_id)))
        .scalars()
        .all()
    )

    mapping_responses = [
        SDGMappingResponse(
            id=str(m.id),
            unit_id=str(m.unit_id),
            sdg_code=m.sdg_code,
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in mappings
    ]

    return SDGMappingSummary(
        unit_id=str(unit_id),
        mapped_count=len(mapping_responses),
        total_sdgs=17,
        mappings=mapping_responses,
    )


@router.post("/units/{unit_id}/sdg-mappings", response_model=SDGMappingResponse)
async def add_unit_sdg_mapping(
    unit_id: UUID,
    mapping_data: SDGMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Add an SDG mapping to a unit"""
    # Verify unit exists
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )

    # Check if mapping already exists for this SDG
    existing = db.execute(
        select(UnitSDGMapping).where(
            UnitSDGMapping.unit_id == str(unit_id),
            UnitSDGMapping.sdg_code == mapping_data.sdg_code.value,
        )
    ).scalar_one_or_none()

    if existing:
        # Update existing mapping
        existing.is_ai_suggested = mapping_data.is_ai_suggested
        existing.notes = mapping_data.notes
        db.commit()
        db.refresh(existing)
        mapping = existing
    else:
        # Create new mapping
        mapping = UnitSDGMapping(
            unit_id=str(unit_id),
            sdg_code=mapping_data.sdg_code.value,
            is_ai_suggested=mapping_data.is_ai_suggested,
            notes=mapping_data.notes,
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)

    return SDGMappingResponse(
        id=str(mapping.id),
        unit_id=str(mapping.unit_id),
        sdg_code=mapping.sdg_code,
        is_ai_suggested=mapping.is_ai_suggested,
        notes=mapping.notes,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


@router.put("/units/{unit_id}/sdg-mappings", response_model=SDGMappingSummary)
async def update_unit_sdg_mappings(
    unit_id: UUID,
    bulk_data: BulkSDGMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Replace all SDG mappings for a unit"""
    # Verify unit exists
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )

    # Delete existing mappings
    db.execute(delete(UnitSDGMapping).where(UnitSDGMapping.unit_id == str(unit_id)))

    # Create new mappings
    new_mappings = []
    for mapping_data in bulk_data.mappings:
        mapping = UnitSDGMapping(
            unit_id=str(unit_id),
            sdg_code=mapping_data.sdg_code.value,
            is_ai_suggested=mapping_data.is_ai_suggested,
            notes=mapping_data.notes,
        )
        db.add(mapping)
        new_mappings.append(mapping)

    db.commit()

    # Refresh all mappings
    for m in new_mappings:
        db.refresh(m)

    mapping_responses = [
        SDGMappingResponse(
            id=str(m.id),
            unit_id=str(m.unit_id),
            sdg_code=m.sdg_code,
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in new_mappings
    ]

    return SDGMappingSummary(
        unit_id=str(unit_id),
        mapped_count=len(mapping_responses),
        total_sdgs=17,
        mappings=mapping_responses,
    )


@router.delete("/units/{unit_id}/sdg-mappings/{sdg_code}")
async def remove_unit_sdg_mapping(
    unit_id: UUID,
    sdg_code: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Remove an SDG mapping from a unit"""
    # First check if mapping exists
    existing = db.execute(
        select(UnitSDGMapping).where(
            UnitSDGMapping.unit_id == str(unit_id),
            UnitSDGMapping.sdg_code == sdg_code.upper(),
        )
    ).scalar_one_or_none()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found",
        )

    db.delete(existing)
    db.commit()

    return {"message": "Mapping removed successfully"}


# ============= Custom Alignment Frameworks =============


def _framework_response(fw: CustomAlignmentFramework) -> FrameworkResponse:
    """Helper to build a FrameworkResponse from a model instance."""
    return FrameworkResponse(
        id=str(fw.id),
        unit_id=str(fw.unit_id),
        name=fw.name,
        description=fw.description,
        preset_type=fw.preset_type,
        icon_hint=fw.icon_hint,
        color_hint=fw.color_hint,
        order_index=fw.order_index,
        items=[
            FrameworkItemResponse(
                id=str(item.id),
                framework_id=str(item.framework_id),
                code=item.code,
                description=item.description,
                is_ai_suggested=item.is_ai_suggested,
                notes=item.notes,
                order_index=item.order_index,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in sorted(fw.items, key=lambda i: i.order_index)
        ],
        created_at=fw.created_at,
        updated_at=fw.updated_at,
    )


@router.get(
    "/units/{unit_id}/frameworks",
    response_model=FrameworkSummary,
)
async def get_unit_frameworks(
    unit_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all custom alignment frameworks for a unit"""
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    frameworks = (
        db.execute(
            select(CustomAlignmentFramework)
            .where(CustomAlignmentFramework.unit_id == str(unit_id))
            .order_by(CustomAlignmentFramework.order_index)
        )
        .scalars()
        .all()
    )

    return FrameworkSummary(
        unit_id=str(unit_id),
        framework_count=len(frameworks),
        frameworks=[_framework_response(fw) for fw in frameworks],
    )


@router.post(
    "/units/{unit_id}/frameworks",
    response_model=FrameworkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_framework(
    unit_id: UUID,
    data: FrameworkCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a custom alignment framework with optional initial items"""
    unit = db.execute(select(Unit).where(Unit.id == str(unit_id))).scalar_one_or_none()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found"
        )

    fw = CustomAlignmentFramework(
        unit_id=str(unit_id),
        name=data.name,
        description=data.description,
        preset_type=data.preset_type,
        icon_hint=data.icon_hint,
        color_hint=data.color_hint,
        order_index=data.order_index,
    )
    db.add(fw)
    db.flush()  # Get ID for items

    for i, item_data in enumerate(data.items):
        item = FrameworkItem(
            framework_id=str(fw.id),
            code=item_data.code,
            description=item_data.description,
            is_ai_suggested=item_data.is_ai_suggested,
            notes=item_data.notes,
            order_index=item_data.order_index if item_data.order_index else i,
        )
        db.add(item)

    db.commit()
    db.refresh(fw)

    return _framework_response(fw)


@router.put(
    "/units/{unit_id}/frameworks/{framework_id}",
    response_model=FrameworkResponse,
)
async def update_framework(
    unit_id: UUID,
    framework_id: UUID,
    data: FrameworkUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a framework's metadata"""
    fw = db.execute(
        select(CustomAlignmentFramework).where(
            CustomAlignmentFramework.id == str(framework_id),
            CustomAlignmentFramework.unit_id == str(unit_id),
        )
    ).scalar_one_or_none()

    if not fw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found"
        )

    if data.name is not None:
        fw.name = data.name
    if data.description is not None:
        fw.description = data.description
    if data.icon_hint is not None:
        fw.icon_hint = data.icon_hint
    if data.color_hint is not None:
        fw.color_hint = data.color_hint
    if data.order_index is not None:
        fw.order_index = data.order_index

    db.commit()
    db.refresh(fw)

    return _framework_response(fw)


@router.delete("/units/{unit_id}/frameworks/{framework_id}")
async def delete_framework(
    unit_id: UUID,
    framework_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete a framework (cascades to items and mappings)"""
    fw = db.execute(
        select(CustomAlignmentFramework).where(
            CustomAlignmentFramework.id == str(framework_id),
            CustomAlignmentFramework.unit_id == str(unit_id),
        )
    ).scalar_one_or_none()

    if not fw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found"
        )

    db.delete(fw)
    db.commit()

    return {"message": "Framework deleted successfully"}


# ============= Framework Items =============


@router.post(
    "/units/{unit_id}/frameworks/{framework_id}/items",
    response_model=FrameworkItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_framework_item(
    unit_id: UUID,
    framework_id: UUID,
    data: FrameworkItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Add an item to a framework"""
    fw = db.execute(
        select(CustomAlignmentFramework).where(
            CustomAlignmentFramework.id == str(framework_id),
            CustomAlignmentFramework.unit_id == str(unit_id),
        )
    ).scalar_one_or_none()

    if not fw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found"
        )

    item = FrameworkItem(
        framework_id=str(framework_id),
        code=data.code,
        description=data.description,
        is_ai_suggested=data.is_ai_suggested,
        notes=data.notes,
        order_index=data.order_index,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return FrameworkItemResponse(
        id=str(item.id),
        framework_id=str(item.framework_id),
        code=item.code,
        description=item.description,
        is_ai_suggested=item.is_ai_suggested,
        notes=item.notes,
        order_index=item.order_index,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.put(
    "/units/{unit_id}/frameworks/{framework_id}/items/{item_id}",
    response_model=FrameworkItemResponse,
)
async def update_framework_item(
    unit_id: UUID,
    framework_id: UUID,
    item_id: UUID,
    data: FrameworkItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a framework item"""
    item = db.execute(
        select(FrameworkItem)
        .join(CustomAlignmentFramework)
        .where(
            FrameworkItem.id == str(item_id),
            FrameworkItem.framework_id == str(framework_id),
            CustomAlignmentFramework.unit_id == str(unit_id),
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    if data.code is not None:
        item.code = data.code
    if data.description is not None:
        item.description = data.description
    if data.notes is not None:
        item.notes = data.notes
    if data.order_index is not None:
        item.order_index = data.order_index

    db.commit()
    db.refresh(item)

    return FrameworkItemResponse(
        id=str(item.id),
        framework_id=str(item.framework_id),
        code=item.code,
        description=item.description,
        is_ai_suggested=item.is_ai_suggested,
        notes=item.notes,
        order_index=item.order_index,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.delete("/units/{unit_id}/frameworks/{framework_id}/items/{item_id}")
async def delete_framework_item(
    unit_id: UUID,
    framework_id: UUID,
    item_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete a framework item (cascades to mappings)"""
    item = db.execute(
        select(FrameworkItem)
        .join(CustomAlignmentFramework)
        .where(
            FrameworkItem.id == str(item_id),
            FrameworkItem.framework_id == str(framework_id),
            CustomAlignmentFramework.unit_id == str(unit_id),
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    db.delete(item)
    db.commit()

    return {"message": "Item deleted successfully"}


# ============= ULO→Framework Item Mappings =============


@router.get(
    "/ulos/{ulo_id}/framework-mappings",
    response_model=list[ULOItemMappingResponse],
)
async def get_ulo_framework_mappings(
    ulo_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all framework item mappings for a ULO"""
    ulo = db.execute(
        select(UnitLearningOutcome).where(UnitLearningOutcome.id == str(ulo_id))
    ).scalar_one_or_none()

    if not ulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ULO not found"
        )

    mappings = (
        db.execute(
            select(ULOFrameworkItemMapping).where(
                ULOFrameworkItemMapping.ulo_id == str(ulo_id)
            )
        )
        .scalars()
        .all()
    )

    return [
        ULOItemMappingResponse(
            id=str(m.id),
            ulo_id=str(m.ulo_id),
            item_id=str(m.item_id),
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in mappings
    ]


@router.put(
    "/ulos/{ulo_id}/framework-mappings",
    response_model=list[ULOItemMappingResponse],
)
async def update_ulo_framework_mappings(
    ulo_id: UUID,
    bulk_data: BulkULOItemMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Replace all framework item mappings for a ULO"""
    ulo = db.execute(
        select(UnitLearningOutcome).where(UnitLearningOutcome.id == str(ulo_id))
    ).scalar_one_or_none()

    if not ulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ULO not found"
        )

    # Delete existing mappings
    db.execute(
        delete(ULOFrameworkItemMapping).where(
            ULOFrameworkItemMapping.ulo_id == str(ulo_id)
        )
    )

    # Create new mappings
    new_mappings = []
    for mapping_data in bulk_data.mappings:
        mapping = ULOFrameworkItemMapping(
            ulo_id=str(ulo_id),
            item_id=mapping_data.item_id,
            is_ai_suggested=mapping_data.is_ai_suggested,
            notes=mapping_data.notes,
        )
        db.add(mapping)
        new_mappings.append(mapping)

    db.commit()

    for m in new_mappings:
        db.refresh(m)

    return [
        ULOItemMappingResponse(
            id=str(m.id),
            ulo_id=str(m.ulo_id),
            item_id=str(m.item_id),
            is_ai_suggested=m.is_ai_suggested,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in new_mappings
    ]


@router.delete("/ulos/{ulo_id}/framework-mappings/{item_id}")
async def remove_ulo_framework_mapping(
    ulo_id: UUID,
    item_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Remove a single ULO→framework item mapping"""
    existing = db.execute(
        select(ULOFrameworkItemMapping).where(
            ULOFrameworkItemMapping.ulo_id == str(ulo_id),
            ULOFrameworkItemMapping.item_id == str(item_id),
        )
    ).scalar_one_or_none()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found"
        )

    db.delete(existing)
    db.commit()

    return {"message": "Mapping removed successfully"}
