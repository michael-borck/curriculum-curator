"""
API endpoints for content export using Quarto
"""

import os
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models import Content, Unit, User
from app.schemas.quarto import (
    QuartoExportRequest,
    QuartoExportResponse,
    QuartoPresetCreate,
    QuartoPresetResponse,
    QuartoPreviewRequest,
    QuartoSettingsUpdate,
)
from app.services.quarto_service import quarto_service

router = APIRouter()


@router.post("/content/{content_id}/export", response_model=QuartoExportResponse)
async def export_content(
    content_id: str,
    export_request: QuartoExportRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Export content in specified formats using Quarto
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
    
    # Get the content markdown
    content_text = content.content_markdown or ""
    
    # Render using Quarto
    result = await quarto_service.render_content(
        content=content_text,
        mode=export_request.mode,
        settings=export_request.settings,
        content_id=content_id,
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {result.get('error', 'Unknown error')}",
        )
    
    return QuartoExportResponse(
        success=result["success"],
        render_id=result["render_id"],
        outputs=result["outputs"],
        yaml_used=result.get("yaml_used", ""),
    )


@router.get("/content/{content_id}/export/{render_id}/{filename}")
async def download_exported_file(
    content_id: str,
    render_id: str,
    filename: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Download an exported file
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
    
    # Construct file path
    file_path = quarto_service.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Determine media type based on extension
    media_types = {
        ".html": "text/html",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    
    media_type = media_types.get(file_path.suffix, "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


@router.post("/content/{content_id}/preview")
async def preview_content(
    content_id: str,
    preview_request: QuartoPreviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate HTML preview of content with Quarto rendering
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
    
    # Use provided content or fetch from database
    content_text = preview_request.content or content.content_markdown or ""
    
    # Generate preview
    html_preview = await quarto_service.preview_content(
        content=content_text,
        settings=preview_request.settings,
    )
    
    return {"html": html_preview}


@router.get("/content/{content_id}/quarto-settings")
async def get_content_quarto_settings(
    content_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get Quarto settings for a content item
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
    
    # Get or create settings
    settings = content.quarto_settings
    if not settings:
        from app.models.content_quarto_settings import ContentQuartoSettings
        
        settings = ContentQuartoSettings(
            content_id=content_id,
            simple_settings={
                "formats": ["html"],
                "theme": "default",
                "toc": True,
                "author": current_user.name,
            },
            active_mode="simple",
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return {
        "simple_settings": settings.simple_settings,
        "advanced_yaml": settings.advanced_yaml,
        "active_mode": settings.active_mode,
        "active_preset": settings.active_preset,
    }


@router.put("/content/{content_id}/quarto-settings")
async def update_content_quarto_settings(
    content_id: str,
    settings_update: QuartoSettingsUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update Quarto settings for a content item
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
    
    # Get or create settings
    settings = content.quarto_settings
    if not settings:
        from app.models.content_quarto_settings import ContentQuartoSettings
        
        settings = ContentQuartoSettings(content_id=content_id)
        db.add(settings)
    
    # Update settings
    if settings_update.simple_settings is not None:
        settings.simple_settings = settings_update.simple_settings
    if settings_update.advanced_yaml is not None:
        settings.advanced_yaml = settings_update.advanced_yaml
    if settings_update.active_mode is not None:
        settings.active_mode = settings_update.active_mode
    if settings_update.active_preset is not None:
        settings.active_preset = settings_update.active_preset
    
    db.commit()
    db.refresh(settings)
    
    return {
        "simple_settings": settings.simple_settings,
        "advanced_yaml": settings.advanced_yaml,
        "active_mode": settings.active_mode,
        "active_preset": settings.active_preset,
    }


@router.get("/presets", response_model=List[QuartoPresetResponse])
async def get_user_presets(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get user's saved Quarto presets
    """
    presets = await quarto_service.get_user_presets(db, current_user.id)
    return presets


@router.post("/presets", response_model=QuartoPresetResponse)
async def save_preset(
    preset_data: QuartoPresetCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Save a new Quarto preset for the user
    """
    preset = await quarto_service.save_preset(
        db=db,
        user_id=current_user.id,
        name=preset_data.name,
        yaml_content=preset_data.yaml_content,
        is_default=preset_data.is_default,
    )
    return preset


@router.delete("/presets/{preset_id}")
async def delete_preset(
    preset_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a user's preset
    """
    success = await quarto_service.delete_preset(db, current_user.id, preset_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preset not found or access denied",
        )
    
    return {"success": True}


@router.get("/themes")
async def get_available_themes() -> Any:
    """
    Get available themes for different output formats
    """
    themes = await quarto_service.get_available_themes()
    return themes