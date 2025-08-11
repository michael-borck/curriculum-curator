"""
Content management routes with user workspace isolation
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Content, ContentStatus, Unit, User
from app.schemas.content import (
    ContentCreate,
    ContentListResponse,
    ContentResponse,
    ContentUpdate,
)

router = APIRouter()


@router.get("/", response_model=ContentListResponse)
async def get_contents(
    unit_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    content_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get all content for the current user.
    If unit_id is provided, returns content for that unit (if user owns it).
    """
    # Build base query - join with units to check ownership
    query = (
        db.query(Content)
        .join(Unit, Content.unit_id == Unit.id)
        .filter(Unit.owner_id == current_user.id)
    )

    # Apply filters
    if unit_id:
        query = query.filter(Content.unit_id == unit_id)
    if content_type:
        query = query.filter(Content.type == content_type)
    if status:
        query = query.filter(Content.status == status)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    contents = query.order_by(Content.order_index).offset(skip).limit(limit).all()

    return ContentListResponse(
        contents=[
            ContentResponse(
                id=str(content.id),
                title=content.title,
                type=content.type,
                status=content.status,
                unit_id=str(content.unit_id),
                parent_content_id=str(content.parent_content_id)
                if content.parent_content_id
                else None,
                order_index=content.order_index,
                content_markdown=content.content_markdown or "",
                summary=content.summary or "",
                estimated_duration_minutes=content.estimated_duration_minutes,
                difficulty_level=content.difficulty_level,
                created_at=content.created_at.isoformat(),
                updated_at=content.updated_at.isoformat(),
            )
            for content in contents
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a specific content by ID.
    Only returns content if the user owns the associated unit.
    """
    content = (
        db.query(Content)
        .join(Unit, Content.unit_id == Unit.id)
        .filter(Content.id == content_id)
        .filter(Unit.owner_id == current_user.id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied",
        )

    return ContentResponse(
        id=str(content.id),
        title=content.title,
        type=content.type,
        status=content.status,
        unit_id=str(content.unit_id),
        parent_content_id=str(content.parent_content_id)
        if content.parent_content_id
        else None,
        order_index=content.order_index,
        content_markdown=content.content_markdown or "",
        summary=content.summary or "",
        estimated_duration_minutes=content.estimated_duration_minutes,
        difficulty_level=content.difficulty_level,
        created_at=content.created_at.isoformat(),
        updated_at=content.updated_at.isoformat(),
    )


@router.post("/", response_model=ContentResponse)
async def create_content(
    content_data: ContentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create new content for a unit.
    User must own the unit to add content to it.
    """
    import uuid
    from datetime import datetime

    # Verify user owns the unit
    unit = (
        db.query(Unit)
        .filter(Unit.id == content_data.unit_id)
        .filter(Unit.owner_id == current_user.id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Create new content
    new_content = Content(
        id=uuid.uuid4(),
        title=content_data.title,
        type=content_data.type,
        status=content_data.status or ContentStatus.DRAFT.value,
        unit_id=content_data.unit_id,
        parent_content_id=content_data.parent_content_id,
        order_index=content_data.order_index,
        content_markdown=content_data.content_markdown,
        summary=content_data.summary,
        estimated_duration_minutes=content_data.estimated_duration_minutes,
        difficulty_level=content_data.difficulty_level,
        learning_objectives=content_data.learning_objectives,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_content)
    db.commit()
    db.refresh(new_content)

    return ContentResponse(
        id=str(new_content.id),
        title=new_content.title,
        type=new_content.type,
        status=new_content.status,
        unit_id=str(new_content.unit_id),
        parent_content_id=str(new_content.parent_content_id)
        if new_content.parent_content_id
        else None,
        order_index=new_content.order_index,
        content_markdown=new_content.content_markdown or "",
        summary=new_content.summary or "",
        estimated_duration_minutes=new_content.estimated_duration_minutes,
        difficulty_level=new_content.difficulty_level,
        created_at=new_content.created_at.isoformat(),
        updated_at=new_content.updated_at.isoformat(),
    )


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    content_data: ContentUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update content.
    User must own the associated unit to update content.
    """
    from datetime import datetime

    # Get content with ownership check
    content = (
        db.query(Content)
        .join(Unit, Content.unit_id == Unit.id)
        .filter(Content.id == content_id)
        .filter(Unit.owner_id == current_user.id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied",
        )

    # Update fields if provided
    update_data = content_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)

    content.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(content)

    return ContentResponse(
        id=str(content.id),
        title=content.title,
        type=content.type,
        status=content.status,
        unit_id=str(content.unit_id),
        parent_content_id=str(content.parent_content_id)
        if content.parent_content_id
        else None,
        order_index=content.order_index,
        content_markdown=content.content_markdown or "",
        summary=content.summary or "",
        estimated_duration_minutes=content.estimated_duration_minutes,
        difficulty_level=content.difficulty_level,
        created_at=content.created_at.isoformat(),
        updated_at=content.updated_at.isoformat(),
    )


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete content.
    User must own the associated unit to delete content.
    """
    # Get content with ownership check
    content = (
        db.query(Content)
        .join(Unit, Content.unit_id == Unit.id)
        .filter(Content.id == content_id)
        .filter(Unit.owner_id == current_user.id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied",
        )

    db.delete(content)
    db.commit()

    return {"message": "Content deleted successfully"}


@router.post("/upload")
async def upload_content(
    unit_id: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Upload a file for content import.
    User must own the unit to upload content to it.
    """
    # Verify user owns the unit
    unit = (
        db.query(Unit)
        .filter(Unit.id == unit_id)
        .filter(Unit.owner_id == current_user.id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # TODO: Process file and create content
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "unit_id": unit_id,
        "message": "File uploaded successfully (processing not yet implemented)",
    }


@router.get("/templates/{content_type}")
async def get_content_template(
    content_type: str,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a template for specific content type.
    Available to all authenticated users.
    """
    templates = {
        "lecture": {
            "type": "lecture",
            "structure": [
                "introduction",
                "objectives",
                "main_content",
                "summary",
                "assignments",
            ],
            "estimated_duration": 50,
        },
        "worksheet": {
            "type": "worksheet",
            "structure": ["title", "instructions", "questions", "answer_key"],
            "estimated_duration": 30,
        },
        "quiz": {
            "type": "quiz",
            "structure": ["title", "instructions", "questions", "scoring"],
            "estimated_duration": 20,
        },
        "module": {
            "type": "module",
            "structure": [
                "overview",
                "learning_outcomes",
                "content_sections",
                "assessment",
            ],
            "estimated_duration": 180,
        },
    }

    template = templates.get(content_type)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template for content type '{content_type}' not found",
        )

    return template
