"""
API routes for LLM configuration management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.models.llm_config import LLMConfiguration
from app.models.user import User
from app.schemas.llm_config import (
    LLMConfig,
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMProvider,
    LLMTestRequest,
    LLMTestResponse,
    UserTokenStats,
)
from app.services.llm_service_enhanced import EnhancedLLMService

router = APIRouter()
llm_service = EnhancedLLMService()


@router.post("/test", response_model=LLMTestResponse)
async def test_llm_connection(
    request: LLMTestRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Test LLM connection with provided configuration"""
    result = await llm_service.test_connection(
        provider=request.provider,
        api_key=request.api_key,
        api_url=request.api_url,
        bearer_token=request.bearer_token,
        model_name=request.model_name,
        test_prompt=request.test_prompt,
    )

    return LLMTestResponse(**result)


@router.get("/models/{provider}", response_model=list[str])
async def list_available_models(
    provider: LLMProvider,
    api_key: str | None = None,
    api_url: str | None = None,
    bearer_token: str | None = None,
    current_user: User = Depends(deps.get_current_user),
):
    """List available models for a provider"""
    return await llm_service.list_models(
        provider=provider,
        api_key=api_key,
        api_url=api_url,
        bearer_token=bearer_token,
    )


@router.get("/configurations", response_model=list[LLMConfig])
def get_user_configurations(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Get all LLM configurations for the current user"""
    configs = (
        db.query(LLMConfiguration)
        .filter(
            LLMConfiguration.user_id == current_user.id,
            LLMConfiguration.is_active,
        )
        .all()
    )

    return [LLMConfig.from_orm(config) for config in configs]


@router.get("/configurations/system", response_model=list[LLMConfig])
def get_system_configurations(
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get system-wide LLM configurations (admin only)"""
    configs = (
        db.query(LLMConfiguration)
        .filter(LLMConfiguration.user_id.is_(None), LLMConfiguration.is_active)
        .all()
    )

    return [LLMConfig.from_orm(config) for config in configs]


@router.post("/configurations", response_model=LLMConfig)
def create_configuration(
    config: LLMConfigCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new LLM configuration for the current user"""
    # If setting as default, unset other defaults
    if config.is_default:
        db.query(LLMConfiguration).filter(
            LLMConfiguration.user_id == current_user.id,
            LLMConfiguration.is_default,
        ).update({"is_default": False})

    db_config = LLMConfiguration(
        user_id=current_user.id,
        provider=config.provider,
        api_key=config.api_key,  # Should be encrypted in production
        api_url=config.api_url,
        bearer_token=config.bearer_token,
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_default=config.is_default,
    )

    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return LLMConfig.from_orm(db_config)


@router.post("/configurations/system", response_model=LLMConfig)
def create_system_configuration(
    config: LLMConfigCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a system-wide LLM configuration (admin only)"""
    # If setting as default, unset other defaults
    if config.is_default:
        db.query(LLMConfiguration).filter(
            LLMConfiguration.user_id.is_(None), LLMConfiguration.is_default
        ).update({"is_default": False})

    db_config = LLMConfiguration(
        user_id=None,  # System-wide config
        provider=config.provider,
        api_key=config.api_key,  # Should be encrypted in production
        api_url=config.api_url,
        bearer_token=config.bearer_token,
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_default=config.is_default,
    )

    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return LLMConfig.from_orm(db_config)


@router.put("/configurations/{config_id}", response_model=LLMConfig)
def update_configuration(
    config_id: str,
    config_update: LLMConfigUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Update an LLM configuration"""
    db_config = (
        db.query(LLMConfiguration)
        .filter(
            LLMConfiguration.id == config_id,
            LLMConfiguration.user_id == current_user.id,
        )
        .first()
    )

    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
        )

    # If setting as default, unset other defaults
    if config_update.is_default:
        db.query(LLMConfiguration).filter(
            LLMConfiguration.user_id == current_user.id,
            LLMConfiguration.is_default,
            LLMConfiguration.id != config_id,
        ).update({"is_default": False})

    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)

    db.commit()
    db.refresh(db_config)

    return LLMConfig.from_orm(db_config)


@router.delete("/configurations/{config_id}")
def delete_configuration(
    config_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an LLM configuration"""
    db_config = (
        db.query(LLMConfiguration)
        .filter(
            LLMConfiguration.id == config_id,
            LLMConfiguration.user_id == current_user.id,
        )
        .first()
    )

    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
        )

    db.delete(db_config)
    db.commit()

    return {"message": "Configuration deleted successfully"}


@router.get("/usage/stats", response_model=UserTokenStats)
def get_token_usage_stats(
    days: int = 30,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """Get token usage statistics for the current user"""
    stats = llm_service.get_token_stats(db, str(current_user.id), days)
    return UserTokenStats(**stats)


@router.get("/usage/stats/all", response_model=list[UserTokenStats])
def get_all_users_token_stats(
    days: int = 30,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get token usage statistics for all users (admin only)"""
    users = db.query(User).all()
    stats = []

    for user in users:
        user_stats = llm_service.get_token_stats(db, str(user.id), days)
        stats.append(UserTokenStats(**user_stats))

    return stats
