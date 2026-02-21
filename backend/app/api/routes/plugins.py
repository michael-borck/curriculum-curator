"""
Plugin management endpoints — validate, remediate, list, and configure plugins.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.material import Material
from app.plugins.base import PluginResult
from app.plugins.plugin_manager import PluginConfig, plugin_manager
from app.schemas.plugins import (
    PluginConfigUpdate,
    PluginInfo,
    PluginListResponse,
    PluginRemediateRequest,
    PluginRemediateResponse,
    PluginResultData,
    PluginValidateRequest,
    PluginValidateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_result_data(result: PluginResult) -> PluginResultData:
    """Convert internal PluginResult to response schema."""
    suggestions: list[str] | None = None
    if result.suggestions is not None:
        suggestions = [str(s) for s in result.suggestions]
    return PluginResultData(
        success=result.success,
        message=result.message,
        data=result.data,
        suggestions=suggestions,
    )


@router.get("", response_model=PluginListResponse)
async def list_plugins() -> PluginListResponse:
    """List all available plugins with their enabled/disabled status."""
    validators = plugin_manager.get_available_validators()
    remediators = plugin_manager.get_available_remediators()

    plugins: list[PluginInfo] = [
        PluginInfo(
            name=v["name"],
            description=v["description"],
            plugin_type="validator",
            enabled=v["enabled"],
            priority=v["priority"],
        )
        for v in validators
    ]
    plugins.extend(
        PluginInfo(
            name=r["name"],
            description=r["description"],
            plugin_type="remediator",
            enabled=r["enabled"],
            priority=r["priority"],
        )
        for r in remediators
    )

    return PluginListResponse(plugins=plugins)


@router.patch("/{name}")
async def configure_plugin(
    name: str, body: PluginConfigUpdate, db: Session = Depends(get_db)
) -> PluginInfo:
    """Update a plugin's configuration and persist to database."""
    # Verify plugin exists
    all_names = set(plugin_manager.validators.keys()) | set(
        plugin_manager.remediators.keys()
    )
    if name not in all_names:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    # Build updated config, merging with existing
    existing = plugin_manager.plugin_configs.get(name, PluginConfig(name))
    new_enabled = body.enabled if body.enabled is not None else existing.enabled
    new_priority = body.priority if body.priority is not None else existing.priority
    new_config = {**existing.config, **(body.config or {})}

    plugin_manager.configure_plugin(
        PluginConfig(
            name=name,
            enabled=new_enabled,
            priority=new_priority,
            config=new_config,
        )
    )

    # Persist to database
    plugin_manager.save_config_to_db(db, name, new_enabled, new_priority, new_config)

    # Determine type
    plugin_type = "validator" if name in plugin_manager.validators else "remediator"
    description = ""
    if name in plugin_manager.validators:
        description = plugin_manager.validators[name].description
    elif name in plugin_manager.remediators:
        description = plugin_manager.remediators[name].description

    return PluginInfo(
        name=name,
        description=description,
        plugin_type=plugin_type,
        enabled=new_enabled,
        priority=new_priority,
    )


@router.post("/validate", response_model=PluginValidateResponse)
async def validate_content(
    body: PluginValidateRequest,
    material_id: str | None = None,
    db: Session = Depends(get_db),
) -> PluginValidateResponse:
    """Run validator plugins on content.

    Optionally pass ``material_id`` as a query parameter to persist the
    overall quality score on the corresponding material row.
    """
    raw_results = await plugin_manager.validate_content(
        body.content, validators=body.validators
    )

    results: dict[str, PluginResultData] = {}
    scores: list[float] = []
    for plugin_name, result in raw_results.items():
        results[plugin_name] = _to_result_data(result)
        if result.data and "score" in result.data:
            scores.append(float(result.data["score"]))

    overall_score = sum(scores) / len(scores) if scores else 100.0
    rounded_score = round(overall_score, 2)

    # Persist quality score to material if requested
    if material_id:
        material = db.query(Material).filter(Material.id == material_id).first()
        if material:
            material.quality_score = round(overall_score)
            db.commit()

    return PluginValidateResponse(
        results=results,
        overall_score=rounded_score,
    )


@router.post("/remediate", response_model=PluginRemediateResponse)
async def remediate_content(body: PluginRemediateRequest) -> PluginRemediateResponse:
    """Run remediator plugins on content."""
    raw_results = await plugin_manager.remediate_content(
        body.content, issues=[], remediators=body.remediators
    )

    results: dict[str, PluginResultData] = {}
    changes_made: list[str] = []
    final_content = body.content

    for plugin_name, result in raw_results.items():
        results[plugin_name] = _to_result_data(result)
        if result.success and result.data:
            if "content" in result.data:
                final_content = result.data["content"]
            if "changes" in result.data:
                changes_made.extend(
                    str(change) for change in result.data["changes"]
                )

    return PluginRemediateResponse(
        content=final_content,
        results=results,
        changes_made=changes_made,
    )
