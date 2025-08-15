"""
Admin configuration management endpoints
"""

import json
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import ConfigCategory, SystemConfig, User, UserRole
from app.schemas.admin_config import (
    ConfigBulkUpdate,
    ConfigCreate,
    ConfigListResponse,
    ConfigResponse,
    ConfigUpdate,
)
from app.services.security_logger import SecurityLogger

router = APIRouter()


def get_current_admin_user(
    current_user: User = Depends(deps.get_current_active_user),
) -> User:
    """Ensure current user is an admin"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/configs", response_model=ConfigListResponse)
async def list_configurations(
    category: ConfigCategory | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """List all system configurations with optional filtering"""
    query = db.query(SystemConfig)

    # Apply filters
    if category:
        query = query.filter(SystemConfig.category == category)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (SystemConfig.key.ilike(search_term)) |
            (SystemConfig.description.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    configs = query.offset(skip).limit(limit).all()

    # Convert to response model
    config_responses = [
        ConfigResponse(
            id=str(config.id),
            key=config.key,
            value=config.value,
            category=config.category,
            value_type=config.value_type,
            description=config.description,
            is_sensitive=config.is_sensitive,
            validation_regex=config.validation_regex,
            min_value=config.min_value,
            max_value=config.max_value,
            allowed_values=config.allowed_values,
            requires_restart=config.requires_restart,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )
        for config in configs
    ]

    return ConfigListResponse(
        configs=config_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/configs/{key}", response_model=ConfigResponse)
async def get_configuration(
    key: str,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Get a specific configuration by key"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )

    return ConfigResponse(
        id=str(config.id),
        key=config.key,
        value=config.value if not config.is_sensitive else "***HIDDEN***",
        category=config.category,
        value_type=config.value_type,
        description=config.description,
        is_sensitive=config.is_sensitive,
        validation_regex=config.validation_regex,
        min_value=config.min_value,
        max_value=config.max_value,
        allowed_values=config.allowed_values,
        requires_restart=config.requires_restart,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.post("/configs", response_model=ConfigResponse)
async def create_configuration(
    config_data: ConfigCreate,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Create a new configuration setting"""
    # Check if key already exists
    existing = db.query(SystemConfig).filter(
        SystemConfig.key == config_data.key
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Configuration key already exists"
        )

    # Validate value based on type and constraints
    validated_value = _validate_config_value(
        value=config_data.value,
        value_type=config_data.value_type,
        validation_regex=config_data.validation_regex,
        min_value=config_data.min_value,
        max_value=config_data.max_value,
        allowed_values=config_data.allowed_values,
    )

    new_config = SystemConfig(
        key=config_data.key,
        value=validated_value,
        category=config_data.category,
        value_type=config_data.value_type,
        description=config_data.description,
        is_sensitive=config_data.is_sensitive,
        validation_regex=config_data.validation_regex,
        min_value=config_data.min_value,
        max_value=config_data.max_value,
        allowed_values=config_data.allowed_values,
        requires_restart=config_data.requires_restart,
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Created configuration: {new_config.key}",
    )

    return ConfigResponse(
        id=str(new_config.id),
        key=new_config.key,
        value=new_config.value if not new_config.is_sensitive else "***HIDDEN***",
        category=new_config.category,
        value_type=new_config.value_type,
        description=new_config.description,
        is_sensitive=new_config.is_sensitive,
        validation_regex=new_config.validation_regex,
        min_value=new_config.min_value,
        max_value=new_config.max_value,
        allowed_values=new_config.allowed_values,
        requires_restart=new_config.requires_restart,
        created_at=new_config.created_at.isoformat(),
        updated_at=new_config.updated_at.isoformat(),
    )


@router.put("/configs/{key}", response_model=ConfigResponse)
async def update_configuration(
    key: str,
    config_data: ConfigUpdate,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Update a configuration setting"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )

    # Validate and update value if provided
    if config_data.value is not None:
        validated_value = _validate_config_value(
            value=config_data.value,
            value_type=config.value_type,
            validation_regex=config.validation_regex,
            min_value=config.min_value,
            max_value=config.max_value,
            allowed_values=config.allowed_values,
        )
        config.value = validated_value

    # Update other fields if provided
    if config_data.description is not None:
        config.description = config_data.description

    if config_data.validation_regex is not None:
        config.validation_regex = config_data.validation_regex

    if config_data.min_value is not None:
        config.min_value = config_data.min_value

    if config_data.max_value is not None:
        config.max_value = config_data.max_value

    if config_data.allowed_values is not None:
        config.allowed_values = config_data.allowed_values

    db.commit()
    db.refresh(config)

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Updated configuration: {config.key}",
    )

    # Check if restart is required
    if config.requires_restart:
        return ConfigResponse(
            id=str(config.id),
            key=config.key,
            value=config.value if not config.is_sensitive else "***HIDDEN***",
            category=config.category,
            value_type=config.value_type,
            description=config.description,
            is_sensitive=config.is_sensitive,
            validation_regex=config.validation_regex,
            min_value=config.min_value,
            max_value=config.max_value,
            allowed_values=config.allowed_values,
            requires_restart=config.requires_restart,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
            warning="This configuration change requires a system restart to take effect",
        )

    return ConfigResponse(
        id=str(config.id),
        key=config.key,
        value=config.value if not config.is_sensitive else "***HIDDEN***",
        category=config.category,
        value_type=config.value_type,
        description=config.description,
        is_sensitive=config.is_sensitive,
        validation_regex=config.validation_regex,
        min_value=config.min_value,
        max_value=config.max_value,
        allowed_values=config.allowed_values,
        requires_restart=config.requires_restart,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.post("/configs/bulk-update")
async def bulk_update_configurations(
    updates: ConfigBulkUpdate,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Update multiple configuration settings at once"""
    updated_configs = []
    errors = []
    restart_required = False

    for key, value in updates.updates.items():
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

        if not config:
            errors.append({
                "key": key,
                "error": "Configuration not found"
            })
            continue

        try:
            # Validate value
            validated_value = _validate_config_value(
                value=value,
                value_type=config.value_type,
                validation_regex=config.validation_regex,
                min_value=config.min_value,
                max_value=config.max_value,
                allowed_values=config.allowed_values,
            )

            config.value = validated_value
            updated_configs.append(key)

            if config.requires_restart:
                restart_required = True

        except ValueError as e:
            errors.append({
                "key": key,
                "error": str(e)
            })

    if updated_configs:
        db.commit()

        # Log the action
        SecurityLogger.log_admin_action(
            db=db,
            admin_user=admin_user,
            action=f"Bulk updated {len(updated_configs)} configurations",
        )

    response = {
        "updated": updated_configs,
        "errors": errors,
        "restart_required": restart_required,
    }

    if restart_required:
        response["warning"] = "Some configuration changes require a system restart to take effect"

    return response


@router.delete("/configs/{key}")
async def delete_configuration(
    key: str,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Delete a configuration setting (only custom configs)"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )

    # Prevent deletion of core system configs
    if config.category in [ConfigCategory.SECURITY, ConfigCategory.EMAIL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete core system configurations"
        )

    db.delete(config)
    db.commit()

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Deleted configuration: {key}",
    )

    return {"message": f"Configuration {key} has been deleted"}


@router.post("/configs/reset-defaults")
async def reset_to_defaults(
    category: ConfigCategory | None = None,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Reset configurations to default values"""
    from app.models.system_config import SystemConfig  # noqa: PLC0415

    # Get default configs
    default_configs = SystemConfig.get_default_configs()

    # Filter by category if specified
    if category:
        default_configs = [c for c in default_configs if c["category"] == category]

    reset_count = 0
    for default in default_configs:
        config = db.query(SystemConfig).filter(
            SystemConfig.key == default["key"]
        ).first()

        if config:
            config.value = default["value"]
            reset_count += 1

    db.commit()

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Reset {reset_count} configurations to defaults",
    )

    return {
        "message": f"Reset {reset_count} configurations to default values",
        "category": category.value if category else "all",
    }


@router.get("/configs/export")
async def export_configurations(
    category: ConfigCategory | None = None,
    include_sensitive: bool = False,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    """Export configurations as JSON"""
    query = db.query(SystemConfig)

    if category:
        query = query.filter(SystemConfig.category == category)

    configs = query.all()

    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": admin_user.email,
        "configs": []
    }

    for config in configs:
        config_dict = {
            "key": config.key,
            "value": config.value if (not config.is_sensitive or include_sensitive) else "***HIDDEN***",
            "category": config.category.value,
            "value_type": config.value_type,
            "description": config.description,
            "is_sensitive": config.is_sensitive,
            "requires_restart": config.requires_restart,
        }

        # Include optional fields if set
        if config.validation_regex:
            config_dict["validation_regex"] = config.validation_regex
        if config.min_value is not None:
            config_dict["min_value"] = config.min_value
        if config.max_value is not None:
            config_dict["max_value"] = config.max_value
        if config.allowed_values:
            config_dict["allowed_values"] = config.allowed_values

        export_data["configs"].append(config_dict)

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Exported {len(configs)} configurations",
    )

    return export_data


def _validate_config_value(  # noqa: PLR0912
    value: str,
    value_type: str,
    validation_regex: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    allowed_values: list[str] | None = None,
) -> str:
    """Validate configuration value based on type and constraints"""

    # Type validation
    if value_type == "integer":
        try:
            int_value = int(value)
            if min_value is not None and int_value < min_value:
                raise ValueError(f"Value must be at least {min_value}")
            if max_value is not None and int_value > max_value:
                raise ValueError(f"Value must be at most {max_value}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Value must be an integer")
            raise

    elif value_type == "float":
        try:
            float_value = float(value)
            if min_value is not None and float_value < min_value:
                raise ValueError(f"Value must be at least {min_value}")
            if max_value is not None and float_value > max_value:
                raise ValueError(f"Value must be at most {max_value}")
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError("Value must be a number")
            raise

    elif value_type == "boolean":
        if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
            raise ValueError("Value must be a boolean (true/false)")
        # Normalize boolean values
        value = str(value.lower() in ["true", "1", "yes"])

    elif value_type == "json":
        try:
            json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    # Regex validation
    if validation_regex and not re.match(validation_regex, value):
        raise ValueError(f"Value does not match required pattern: {validation_regex}")

    # Allowed values validation
    if allowed_values and value not in allowed_values:
        raise ValueError(f"Value must be one of: {', '.join(allowed_values)}")

    return value
