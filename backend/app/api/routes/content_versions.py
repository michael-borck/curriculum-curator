"""
API endpoints for content version history
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Content, ContentVersion, Unit, User
from app.schemas.content import (
    ContentVersionCreate,
    ContentVersionResponse,
)

router = APIRouter()


@router.get("/content/{content_id}/versions", response_model=list[ContentVersionResponse])
async def get_content_versions(
    content_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all versions of a content item.
    Only returns versions if the user owns the associated unit.
    """
    # Verify user has access to this content
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

    # Get all versions for this content
    versions = (
        db.query(ContentVersion)
        .filter(ContentVersion.content_id == content_id)
        .order_by(desc(ContentVersion.version_number))
        .all()
    )

    # Get current version number
    current_version = content.version_number if hasattr(content, 'version_number') else 1

    return [
        ContentVersionResponse(
            id=str(version.id),
            materialId=str(version.content_id),
            version=version.version_number,
            parentVersionId=str(version.parent_version_id) if hasattr(version, 'parent_version_id') and version.parent_version_id else None,
            title=version.title,
            content={"html": version.content_html, "markdown": version.content_markdown},
            raw_content=version.content_markdown,
            createdAt=version.created_at.isoformat(),
            createdBy=version.created_by.email if version.created_by else None,
            changeSummary=version.change_description,
            isLatest=(version.version_number == current_version),
            wordCount=len(version.content_markdown.split()) if version.content_markdown else 0,
            qualityScore=None,  # Could be calculated based on validators
        )
        for version in versions
    ]


@router.get("/materials/{material_id}/versions", response_model=list[ContentVersionResponse])
async def get_material_versions(
    material_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all versions of a material (alias for content versions).
    Materials and content are used interchangeably in this context.
    """
    return await get_content_versions(material_id, db, current_user)


@router.post("/content/{content_id}/restore/{version_id}")
async def restore_content_version(
    content_id: str,
    version_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Restore a content item to a previous version.
    Creates a new version with the content from the specified version.
    """
    # Verify user has access to this content
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

    # Get the version to restore
    version_to_restore = (
        db.query(ContentVersion)
        .filter(
            and_(
                ContentVersion.id == version_id,
                ContentVersion.content_id == content_id
            )
        )
        .first()
    )

    if not version_to_restore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    # Get the current max version number
    max_version = (
        db.query(ContentVersion.version_number)
        .filter(ContentVersion.content_id == content_id)
        .order_by(desc(ContentVersion.version_number))
        .first()
    )
    new_version_number = (max_version[0] + 1) if max_version else 1

    # Create a new version with content from the restored version
    new_version = ContentVersion(
        content_id=content_id,
        version_number=new_version_number,
        content_markdown=version_to_restore.content_markdown,
        content_html=version_to_restore.content_html,
        title=version_to_restore.title,
        change_description=f"Restored from version {version_to_restore.version_number}",
        created_by_id=current_user.id,
    )

    # Update the current content with the restored version
    content.content_markdown = version_to_restore.content_markdown
    content.content_html = version_to_restore.content_html
    content.title = version_to_restore.title
    if hasattr(content, 'version_number'):
        content.version_number = new_version_number

    db.add(new_version)
    db.commit()
    db.refresh(content)

    return {
        "message": f"Content restored to version {version_to_restore.version_number}",
        "new_version": new_version_number,
    }


@router.post("/materials/{material_id}/restore/{version_id}")
async def restore_material_version(
    material_id: str,
    version_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Restore a material to a previous version (alias for content restore).
    """
    return await restore_content_version(material_id, version_id, db, current_user)


@router.post("/content/{content_id}/versions", response_model=ContentVersionResponse)
async def create_content_version(
    content_id: str,
    version_data: ContentVersionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new version of content (for manual saves).
    """
    # Verify user has access to this content
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

    # Get the current max version number
    max_version = (
        db.query(ContentVersion.version_number)
        .filter(ContentVersion.content_id == content_id)
        .order_by(desc(ContentVersion.version_number))
        .first()
    )
    new_version_number = (max_version[0] + 1) if max_version else 1

    # Create new version
    new_version = ContentVersion(
        content_id=content_id,
        version_number=new_version_number,
        content_markdown=version_data.content_markdown,
        content_html=version_data.content_html,
        title=version_data.title,
        change_description=version_data.change_description,
        created_by_id=current_user.id,
    )

    # Update the content with new version
    content.content_markdown = version_data.content_markdown
    content.content_html = version_data.content_html
    content.title = version_data.title
    if hasattr(content, 'version_number'):
        content.version_number = new_version_number

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return ContentVersionResponse(
        id=str(new_version.id),
        materialId=str(new_version.content_id),
        version=new_version.version_number,
        parentVersionId=None,
        title=new_version.title,
        content={"html": new_version.content_html, "markdown": new_version.content_markdown},
        raw_content=new_version.content_markdown,
        createdAt=new_version.created_at.isoformat(),
        createdBy=current_user.email,
        changeSummary=new_version.change_description,
        isLatest=True,
        wordCount=len(new_version.content_markdown.split()) if new_version.content_markdown else 0,
        qualityScore=None,
    )
