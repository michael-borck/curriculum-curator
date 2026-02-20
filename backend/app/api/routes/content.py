"""
Content API routes - CRUD operations for unit content (lectures, worksheets, etc.)

Content bodies are stored in Git for version control.
Metadata is stored in SQLAlchemy for fast querying.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.content import Content as ContentModel
from app.repositories import content_repo, unit_repo
from app.schemas.content import (
    ContentCreate,
    ContentDiff,
    ContentHistory,
    ContentList,
    ContentResponse,
    ContentRevertRequest,
    ContentType,
    ContentUpdate,
)
from app.schemas.user import UserResponse
from app.services.file_import_service import file_import_service

router = APIRouter()


# =============================================================================
# Content CRUD Operations
# =============================================================================


@router.post("", response_model=ContentResponse)
async def create_content(
    unit_id: str,
    data: ContentCreate,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Create new content for a unit.

    The content body (markdown) is saved to Git for version control.
    Metadata is saved to the database.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    return content_repo.create_content(
        db,
        unit_id=unit_id,
        data=data,
        user_email=current_user.email,
    )


@router.post("/upload")
async def upload_content(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    file: UploadFile = File(...),
    week_number: int | None = None,
    content_type: ContentType = ContentType.LECTURE,
    content_category: str = "general",
):
    """
    Upload and process a file to create content.

    Supports PDF, DOCX, PPTX, MD, TXT, HTML files.
    Automatically detects content type and provides suggestions.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Check file size (max 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit",
        )

    # Process file
    try:
        result = await file_import_service.process_file(
            contents, file.filename or "uploaded_file"
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process file: {result.get('error', 'Unknown error')}",
            )

        # Create content from processed file
        content_data = ContentCreate(
            title=file.filename or "Uploaded Content",
            content_type=ContentType(content_type),
            body=result["content"],
            week_number=week_number,
            estimated_duration_minutes=result.get("estimated_reading_time", 30),
        )

        content = content_repo.create_content(
            db,
            unit_id=unit_id,
            data=content_data,
            user_email=current_user.email,
        )

        db_content = (
            db.query(ContentModel).filter(ContentModel.id == content.id).first()
        )
        if db_content:
            db_content.content_category = content_category
            db.commit()

        # Add categorization data to response
        return {
            "content_id": str(content.id),
            "content_type": result["content_type"],
            "content_type_confidence": result["content_type_confidence"],
            "wordCount": result["word_count"],
            "sections_found": len(result["sections"]),
            "categorization": {
                "difficultyLevel": file_import_service.assess_difficulty(
                    result["content"]
                ),
                "estimatedDuration": file_import_service.estimate_duration(
                    result["content"], result["content_type"]
                ),
            },
            "suggestions": result["suggestions"],
            "gaps": result["gaps"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {e!s}",
        )


@router.post("/upload/batch")
async def upload_content_batch(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    files: list[UploadFile] = File(...),
):
    """
    Upload and process multiple files to create content items.

    Supports PDF, DOCX, PPTX, MD, TXT, HTML files.
    Automatically detects content type for each file.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    results = []

    for file in files:
        try:
            # Check file size (max 50MB)
            contents = await file.read()
            if len(contents) > 50 * 1024 * 1024:
                results.append(
                    {
                        "filename": file.filename,
                        "success": False,
                        "error": "File size exceeds 50MB limit",
                    }
                )
                continue

            # Process file
            result = await file_import_service.process_file(
                contents, file.filename or "uploaded_file"
            )

            if not result["success"]:
                results.append(
                    {
                        "filename": file.filename,
                        "success": False,
                        "error": result.get("error", "Failed to process file"),
                    }
                )
                continue

            # Create content from processed file
            content_data = ContentCreate(
                title=file.filename or "Uploaded Content",
                content_type=ContentType(result["content_type"]),
                body=result["content"],
                week_number=None,  # Let user assign week later
                estimated_duration_minutes=result.get("estimated_reading_time", 30),
            )

            content = content_repo.create_content(
                db,
                unit_id=unit_id,
                data=content_data,
                user_email=current_user.email,
            )

            db_content = (
                db.query(ContentModel).filter(ContentModel.id == content.id).first()
            )
            if db_content:
                db_content.content_category = "general"
                db.commit()

            results.append(
                {
                    "filename": file.filename,
                    "success": True,
                    "content_id": str(content.id),
                    "content_type": result["content_type"],
                    "content_type_confidence": result["content_type_confidence"],
                    "wordCount": result["word_count"],
                    "sections_found": len(result["sections"]),
                    "categorization": {
                        "difficultyLevel": file_import_service.assess_difficulty(
                            result["content"]
                        ),
                        "estimatedDuration": file_import_service.estimate_duration(
                            result["content"], result["content_type"]
                        ),
                    },
                    "suggestions": result["suggestions"],
                    "gaps": result["gaps"],
                }
            )

        except Exception as e:
            results.append(
                {
                    "filename": file.filename,
                    "success": False,
                    "error": f"Error processing file: {e!s}",
                }
            )

    return {"results": results}


@router.patch("/{content_id}/type")
async def update_content_type(
    content_id: str,
    new_type: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Update content type for an existing content item.
    """
    # Get content
    content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, content.unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Validate content type
    try:
        content_type_enum = ContentType(new_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {new_type}. Valid types: {[t.value for t in ContentType]}",
        )

    # Update content type
    content.type = content_type_enum.value
    db.commit()
    db.refresh(content)

    return {
        "success": True,
        "message": f"Content type updated to {new_type}",
        "content_id": content_id,
        "content_type": new_type,
    }


@router.patch("/{content_id}/week")
async def update_content_week(
    unit_id: str,
    content_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    week_number: int | None = None,
):
    """
    Update week assignment for content.

    Set week_number to None to mark as unassigned.
    Week numbers should be between 1 and 52.
    """
    # Get content
    content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Verify content belongs to this unit
    if str(content.unit_id) != unit_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content does not belong to this unit",
        )

    # Validate week number
    if week_number is not None and (week_number < 1 or week_number > 52):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Week number must be between 1 and 52, or null for unassigned",
        )

    # Update week number
    old_week = content.week_number
    content.week_number = week_number
    db.commit()
    db.refresh(content)

    return {
        "success": True,
        "message": f"Content moved from week {old_week} to week {week_number}"
        if old_week
        else f"Content assigned to week {week_number}",
        "content_id": content_id,
        "old_week_number": old_week,
        "new_week_number": week_number,
    }


@router.get("/unassigned")
async def get_unassigned_content(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Get all content without week assignment (unassigned).
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Get unassigned content
    unassigned = (
        db.query(ContentModel)
        .filter(ContentModel.unit_id == unit_id, ContentModel.week_number.is_(None))
        .all()
    )

    # Convert to response format using list comprehension
    contents = [
        {
            "id": str(content.id),
            "title": content.title,
            "content_type": content.type,
            "created_at": content.created_at.isoformat()
            if content.created_at
            else None,
            "updated_at": content.updated_at.isoformat()
            if content.updated_at
            else None,
        }
        for content in unassigned
    ]

    return {
        "unit_id": unit_id,
        "unit_title": unit.title,
        "unassigned_count": len(unassigned),
        "contents": contents,
    }


@router.post("/bulk/week")
async def bulk_update_content_weeks(
    unit_id: str,
    updates: list[dict],
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Bulk update week assignments for multiple content items.

    Request body should be: [{"content_id": "uuid", "week_number": 1}, ...]
    Week number can be null to mark as unassigned.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    results = []
    errors = []

    for update in updates:
        content_id = update.get("content_id")
        week_number = update.get("week_number")

        if not content_id:
            errors.append({"error": "Missing content_id", "update": update})
            continue

        # Validate week number
        if week_number is not None and (week_number < 1 or week_number > 52):
            errors.append(
                {
                    "content_id": content_id,
                    "error": f"Week number {week_number} must be between 1 and 52",
                    "update": update,
                }
            )
            continue

        # Get content
        content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
        if not content:
            errors.append(
                {
                    "content_id": content_id,
                    "error": "Content not found",
                    "update": update,
                }
            )
            continue

        # Verify content belongs to this unit
        if str(content.unit_id) != unit_id:
            errors.append(
                {
                    "content_id": content_id,
                    "error": "Content does not belong to this unit",
                    "update": update,
                }
            )
            continue

        # Update week number
        old_week = content.week_number
        content.week_number = week_number
        results.append(
            {
                "content_id": content_id,
                "old_week_number": old_week,
                "new_week_number": week_number,
                "success": True,
            }
        )

    # Commit all changes
    if results:
        db.commit()

    return {
        "success": bool(results),
        "updated_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors,
    }


@router.get("", response_model=ContentList)
async def list_content(
    unit_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    week: int | None = None,
):
    """
    List all content for a unit.

    Returns metadata only (no bodies) for faster loading.
    Optionally filter by week number.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    contents = content_repo.get_content_by_unit(db, unit_id, week_number=week)
    return ContentList(contents=contents, total=len(contents))


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    unit_id: str,
    content_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Get a single content item with its body.

    The body is fetched from Git.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    content = content_repo.get_content_by_id(db, content_id)
    if not content or content.unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    unit_id: str,
    content_id: str,
    data: ContentUpdate,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Update content.

    If the body is changed, a new version is saved to Git.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Verify content belongs to this unit
    existing = content_repo.get_content_by_id(db, content_id, include_body=False)
    if not existing or existing.unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    content = content_repo.update_content(
        db,
        content_id=content_id,
        data=data,
        user_email=current_user.email,
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update content",
        )

    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    unit_id: str,
    content_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Delete content.

    Removes from both Git and database.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Verify content belongs to this unit
    existing_unit_id = content_repo.get_content_unit_id(db, content_id)
    if existing_unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    if not content_repo.delete_content(db, content_id, current_user.email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )


# =============================================================================
# Version History Operations
# =============================================================================


@router.get("/{content_id}/history", response_model=ContentHistory)
async def get_content_history(
    unit_id: str,
    content_id: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    limit: int = 10,
):
    """
    Get version history for content.

    Returns a list of previous versions from Git.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Verify content belongs to this unit
    existing_unit_id = content_repo.get_content_unit_id(db, content_id)
    if existing_unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    versions = content_repo.get_content_history(db, content_id, limit=limit)
    return ContentHistory(content_id=content_id, versions=versions)


@router.get("/{content_id}/version/{commit}")
async def get_content_at_version(
    unit_id: str,
    content_id: str,
    commit: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Get content body at a specific version.

    Returns the markdown content at the specified Git commit.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Verify content belongs to this unit
    existing_unit_id = content_repo.get_content_unit_id(db, content_id)
    if existing_unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    body = content_repo.get_content_at_version(db, content_id, commit)
    if body is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    return {"commit": commit, "body": body}


@router.get("/{content_id}/diff", response_model=ContentDiff)
async def get_content_diff(
    unit_id: str,
    content_id: str,
    old_commit: str,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
    new_commit: str = "HEAD",
):
    """
    Get diff between two versions.

    Returns a Git-style diff between two commits.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Verify content belongs to this unit
    existing_unit_id = content_repo.get_content_unit_id(db, content_id)
    if existing_unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    diff = content_repo.get_content_diff(db, content_id, old_commit, new_commit)
    if diff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not generate diff",
        )

    return ContentDiff(
        content_id=content_id,
        old_commit=old_commit,
        new_commit=new_commit,
        diff=diff,
    )


@router.post("/{content_id}/revert", response_model=ContentResponse)
async def revert_content(
    unit_id: str,
    content_id: str,
    data: ContentRevertRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: Annotated[UserResponse, Depends(deps.get_current_active_user)],
):
    """
    Revert content to a previous version.

    Creates a new commit that restores the content from the specified version.
    """
    # Verify user has access to this unit
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if not unit or (unit.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    # Verify content belongs to this unit
    existing_unit_id = content_repo.get_content_unit_id(db, content_id)
    if existing_unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    content = content_repo.revert_content(
        db, content_id, data.commit, current_user.email
    )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revert content",
        )

    return content
