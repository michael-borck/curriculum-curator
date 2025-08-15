"""
Git-specific material endpoints for version control operations
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Material, User
from app.services.git_content_service import get_git_service

router = APIRouter()


@router.get("/{material_id}/history")
async def get_material_history(
    material_id: str,
    limit: int = 10,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> list[dict[str, Any]]:
    """
    Get version history for a material from Git.
    """
    # Get material and verify access
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    # Verify user has access to the course
    from app.models import Course  # noqa: PLC0415
    course = db.query(Course).filter(
        Course.id == material.course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get history from Git
    git_service = get_git_service()
    return git_service.get_history(material.git_path, limit=limit)



@router.get("/{material_id}/diff")
async def get_material_diff(
    material_id: str,
    old_commit: str,
    new_commit: str = "HEAD",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict[str, Any]:
    """
    Get diff between two versions of a material.
    """
    # Get material and verify access
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    # Verify user has access
    from app.models import Course  # noqa: PLC0415
    course = db.query(Course).filter(
        Course.id == material.course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get diff from Git
    git_service = get_git_service()
    diff = git_service.diff(material.git_path, old_commit, new_commit)

    return {
        "material_id": material_id,
        "old_commit": old_commit,
        "new_commit": new_commit,
        "diff": diff
    }


@router.post("/{material_id}/revert")
async def revert_material(
    material_id: str,
    commit: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict[str, Any]:
    """
    Revert a material to a previous version.
    """
    # Get material and verify access
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    # Verify user has access
    from app.models import Course  # noqa: PLC0415
    course = db.query(Course).filter(
        Course.id == material.course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Revert in Git
    git_service = get_git_service()
    new_commit = git_service.revert_to_commit(
        material.git_path,
        commit,
        current_user.email
    )

    # Update material with new commit
    material.current_commit = new_commit
    db.commit()

    return {
        "material_id": material_id,
        "reverted_to": commit,
        "new_commit": new_commit,
        "message": f"Successfully reverted to version {commit[:8]}"
    }


@router.get("/repository/stats")
async def get_repository_stats(
    current_user: User = Depends(deps.get_current_active_user),
) -> dict[str, Any]:
    """
    Get Git repository statistics.
    Admin only endpoint.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    git_service = get_git_service()
    return git_service.get_repository_stats()

