import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.schemas.content import ContentGenerationRequest
from app.services.llm_service import llm_service

router = APIRouter()


@router.post("/generate")
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Generate content with AI assistance using user's configured LLM provider"""
    try:
        # Pass user and db to the service so it can determine the right provider
        async def stream_response():
            async for chunk in llm_service.generate_content(
                pedagogy=request.pedagogy_style,
                topic=request.context,
                content_type=request.content_type,
                user=current_user,
                db=db,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

        if request.stream:
            return StreamingResponse(stream_response(), media_type="text/event-stream")

        result = ""
        async for chunk in llm_service.generate_content(
            pedagogy=request.pedagogy_style,
            topic=request.context,
            content_type=request.content_type,
            user=current_user,
            db=db,
        ):
            result += chunk
        return {"content": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance")
async def enhance_content(
    request: dict[str, Any],
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Enhance existing content with AI using user's configured LLM provider"""
    try:
        content = request.get("content", "")
        enhancement_type = request.get("enhancement_type", "improve")

        result = await llm_service.enhance_content(
            content=content, enhancement_type=enhancement_type, user=current_user, db=db
        )

        return {"enhanced_content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-pedagogy")
async def analyze_pedagogy(
    request: dict[str, Any],
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Analyze content for pedagogical alignment using user's configured LLM provider"""
    # This would analyze the content based on the user's selected teaching philosophy
    request.get("content", "")
    pedagogy = request.get("pedagogy", current_user.teaching_philosophy)

    # For now, return a placeholder response
    return {
        "alignment_score": 0.85,
        "suggestions": [
            "Consider adding more interactive elements",
            "Include real-world examples",
            "Add formative assessment opportunities",
        ],
        "pedagogy": pedagogy,
    }


@router.get("/provider-status")
async def get_provider_status(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Get the current LLM provider status for the user"""
    # Check user's LLM configuration
    user_config = current_user.llm_config or {}
    if isinstance(user_config, str):
        user_config = json.loads(user_config)

    provider = user_config.get("provider", "system")

    # Get system default if using system
    if provider == "system":
        system_provider = (
            db.query(SystemSettings)
            .filter(SystemSettings.key == "default_llm_provider")
            .first()
        )
        actual_provider = system_provider.value if system_provider else "openai"
    else:
        actual_provider = provider

    # Check if API key is configured
    has_api_key = False
    if provider != "system":
        # Check for user's own API key
        if provider == "openai":
            has_api_key = bool(user_config.get("openai_api_key"))
        elif provider == "anthropic":
            has_api_key = bool(user_config.get("anthropic_api_key"))
        elif provider == "gemini":
            has_api_key = bool(user_config.get("gemini_api_key"))
    else:
        # Check for system API key
        system_key_setting = (
            db.query(SystemSettings)
            .filter(SystemSettings.key == f"system_{actual_provider}_api_key")
            .first()
        )
        has_api_key = bool(system_key_setting and system_key_setting.value)

    return {
        "provider": provider,
        "actual_provider": actual_provider,
        "has_api_key": has_api_key,
        "model": user_config.get("model"),
        "is_configured": has_api_key,
    }
