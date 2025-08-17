"""
Plugin system API endpoints
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
# from app.models import Material, User  # Material disabled - table dropped
from app.models import User
from app.plugins.plugin_manager import PluginConfig, plugin_manager

router = APIRouter()


class ValidateContentRequest(BaseModel):
    """Request for content validation"""

    content: str = Field(..., description="Content to validate")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    validators: list[str] | None = Field(None, description="Specific validators to run")


class RemediateContentRequest(BaseModel):
    """Request for content remediation"""

    content: str = Field(..., description="Content to remediate")
    issues: list[dict[str, Any]] = Field(..., description="Issues to remediate")
    remediators: list[str] | None = Field(
        None, description="Specific remediators to run"
    )


class PluginConfigRequest(BaseModel):
    """Plugin configuration request"""

    name: str = Field(..., description="Plugin name")
    enabled: bool = Field(True, description="Whether plugin is enabled")
    priority: int = Field(0, description="Plugin priority (higher runs first)")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Plugin-specific config"
    )


class ValidateMaterialRequest(BaseModel):
    """Request to validate a material"""

    material_id: str = Field(..., description="Material ID to validate")
    validators: list[str] | None = Field(None, description="Specific validators to run")


class RemediateMaterialRequest(BaseModel):
    """Request to remediate a material"""

    material_id: str = Field(..., description="Material ID to remediate")
    apply_changes: bool = Field(
        False, description="Whether to apply changes to material"
    )
    remediators: list[str] | None = Field(
        None, description="Specific remediators to run"
    )


@router.get("/validators")
async def get_validators(
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get list of available validator plugins"""
    # Ensure plugins are loaded
    plugin_manager.load_plugins()

    return {
        "validators": plugin_manager.get_available_validators(),
        "total": len(plugin_manager.validators),
    }


@router.get("/remediators")
async def get_remediators(
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get list of available remediator plugins"""
    # Ensure plugins are loaded
    plugin_manager.load_plugins()

    return {
        "remediators": plugin_manager.get_available_remediators(),
        "total": len(plugin_manager.remediators),
    }


@router.post("/validate")
async def validate_content(
    request: ValidateContentRequest,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Validate content using specified plugins
    """
    # Ensure plugins are loaded
    plugin_manager.load_plugins()

    # Add user context to metadata
    metadata = {
        **request.metadata,
        "user_id": str(current_user.id),
        "user_language": getattr(current_user, "language_preference", "en-US"),
    }

    # Run validation
    results = await plugin_manager.validate_content(
        request.content,
        metadata,
        request.validators,
    )

    # Aggregate results
    all_passed = all(result.success for result in results.values())
    total_issues = sum(
        len(result.data.get("issues", [])) if result.data else 0
        for result in results.values()
    )
    all_suggestions = []
    for result in results.values():
        if result.suggestions:
            all_suggestions.extend(result.suggestions)

    return {
        "passed": all_passed,
        "total_issues": total_issues,
        "validators_run": len(results),
        "results": {
            name: {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "suggestions": result.suggestions,
            }
            for name, result in results.items()
        },
        "aggregated_suggestions": all_suggestions[:20],  # Limit to 20
    }


@router.post("/remediate")
async def remediate_content(
    request: RemediateContentRequest,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Remediate content using specified plugins
    """
    # Ensure plugins are loaded
    plugin_manager.load_plugins()

    # Run remediation
    results = await plugin_manager.remediate_content(
        request.content,
        request.issues,
        request.remediators,
    )

    # Get final content (from last successful remediation)
    final_content = request.content
    for result in results.values():
        if result.success and result.data and "content" in result.data:
            final_content = result.data["content"]

    # Aggregate changes
    all_changes = []
    for result in results.values():
        if result.data and "changes_made" in result.data:
            all_changes.extend(result.data["changes_made"])

    return {
        "success": any(result.success for result in results.values()),
        "final_content": final_content,
        "content_changed": final_content != request.content,
        "total_changes": len(all_changes),
        "remediators_run": len(results),
        "results": {
            name: {
                "success": result.success,
                "message": result.message,
                "data": result.data,
            }
            for name, result in results.items()
        },
        "all_changes": all_changes,
    }


@router.post("/configure")
async def configure_plugin(
    config: PluginConfigRequest,
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    Configure a plugin (admin only)
    """
    # Ensure plugins are loaded
    plugin_manager.load_plugins()

    # Check if plugin exists
    if (
        config.name not in plugin_manager.validators
        and config.name not in plugin_manager.remediators
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{config.name}' not found",
        )

    # Configure plugin
    plugin_config = PluginConfig(
        name=config.name,
        enabled=config.enabled,
        priority=config.priority,
        config=config.config,
    )
    plugin_manager.configure_plugin(plugin_config)

    return {
        "message": f"Plugin '{config.name}' configured successfully",
        "config": {
            "name": plugin_config.name,
            "enabled": plugin_config.enabled,
            "priority": plugin_config.priority,
            "config": plugin_config.config,
        },
    }


@router.post("/validate/material")
async def validate_material(
    request: ValidateMaterialRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Validate a material using plugins
    """
    # Get material with access check
    material = db.query(Material).filter(Material.id == request.material_id).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    # Check access (simplified - in production would check course ownership)
    # For now, any authenticated user can validate

    # Prepare content
    content = material.raw_content or ""
    if not content and material.content and isinstance(material.content, dict):
        # Try to extract text from structured content
        content = material.content.get("body", "")

    if not content:
        return {
            "error": "No content to validate",
            "material_id": request.material_id,
        }

    # Prepare metadata
    metadata = {
        "material_id": str(material.id),
        "material_type": material.type,
        "teaching_philosophy": material.teaching_philosophy,
        "difficulty_level": getattr(material, "difficulty_level", "intermediate"),
    }

    # Run validation
    plugin_manager.load_plugins()
    results = await plugin_manager.validate_content(
        content,
        metadata,
        request.validators,
    )

    # Aggregate results
    all_passed = all(result.success for result in results.values())
    quality_scores = {}

    for name, result in results.items():
        if result.data:
            if "score" in result.data:
                quality_scores[name] = result.data["score"]
            elif "flesch_reading_ease" in result.data:
                quality_scores[name] = result.data["flesch_reading_ease"]

    avg_score = (
        sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0
    )

    return {
        "material_id": request.material_id,
        "passed": all_passed,
        "average_score": round(avg_score, 2),
        "quality_scores": quality_scores,
        "validators_run": len(results),
        "results": {
            name: {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "suggestions": result.suggestions,
            }
            for name, result in results.items()
        },
    }


@router.post("/remediate/material")
async def remediate_material(
    request: RemediateMaterialRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Remediate a material using plugins
    """
    # Get material with access check
    material = db.query(Material).filter(Material.id == request.material_id).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    # Prepare content
    content = material.raw_content or ""
    if not content and material.content and isinstance(material.content, dict):
        content = material.content.get("body", "")

    if not content:
        return {
            "error": "No content to remediate",
            "material_id": request.material_id,
        }

    # First run validation to get issues
    plugin_manager.load_plugins()
    validation_results = await plugin_manager.validate_content(content, {}, None)

    # Collect all issues
    all_issues = [
        {"source": name, "issue": issue}
        for name, result in validation_results.items()
        if result.data and "issues" in result.data
        for issue in result.data["issues"]
    ]

    # Run remediation
    remediation_results = await plugin_manager.remediate_content(
        content,
        all_issues,
        request.remediators,
    )

    # Get final content
    final_content = content
    for result in remediation_results.values():
        if result.success and result.data and "content" in result.data:
            final_content = result.data["content"]

    # Apply changes if requested
    if request.apply_changes and final_content != content:
        material.raw_content = final_content
        # Update content field if it exists
        if material.content and isinstance(material.content, dict):
            material.content["body"] = final_content

        db.commit()
        db.refresh(material)

    return {
        "material_id": request.material_id,
        "content_changed": final_content != content,
        "changes_applied": request.apply_changes and final_content != content,
        "issues_found": len(all_issues),
        "remediators_run": len(remediation_results),
        "results": {
            name: {
                "success": result.success,
                "message": result.message,
                "changes": result.data.get("changes_made", []) if result.data else [],
            }
            for name, result in remediation_results.items()
        },
        "preview": final_content[:500] if final_content else "",  # First 500 chars
    }
