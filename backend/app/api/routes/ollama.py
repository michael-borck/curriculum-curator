"""
Ollama management API routes.

Endpoints for checking Ollama status, pulling models, and testing generation.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_active_user
from app.schemas.user import UserResponse
from app.services.ollama_service import ollama_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_ollama_status(
    _current_user: UserResponse = Depends(get_current_active_user),
) -> dict:
    """Check if Ollama is reachable and list installed models."""
    available = await ollama_service.check_status()
    models = await ollama_service.list_models() if available else []
    recommendation = ollama_service.recommend_model()

    return {
        "available": available,
        "models": models,
        "recommended": recommendation["recommended_model"],
    }


@router.get("/recommend")
async def get_recommendation(
    _current_user: UserResponse = Depends(get_current_active_user),
) -> dict:
    """Get RAM-based model recommendation."""
    return ollama_service.recommend_model()


@router.post("/pull")
async def pull_model(
    body: dict,
    _current_user: UserResponse = Depends(get_current_active_user),
) -> StreamingResponse:
    """Stream model download progress as SSE."""
    model_name = body.get("model")
    if not model_name:
        raise HTTPException(status_code=400, detail="model is required")

    available = await ollama_service.check_status()
    if not available:
        raise HTTPException(status_code=503, detail="Ollama is not reachable")

    async def stream_progress():
        try:
            async for progress in ollama_service.pull_model(model_name):
                yield f"data: {json.dumps(progress)}\n\n"
            yield f"data: {json.dumps({'status': 'success'})}\n\n"
        except Exception as e:
            logger.exception("Error pulling model %s", model_name)
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(stream_progress(), media_type="text/event-stream")


@router.delete("/models/{model_name:path}")
async def delete_model(
    model_name: str,
    _current_user: UserResponse = Depends(get_current_active_user),
) -> dict:
    """Delete an installed model."""
    success = await ollama_service.delete_model(model_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete model")
    return {"deleted": True, "model": model_name}


@router.post("/test")
async def test_generation(
    body: dict,
    _current_user: UserResponse = Depends(get_current_active_user),
) -> dict:
    """Test generation with a model."""
    model_name = body.get("model")
    if not model_name:
        raise HTTPException(status_code=400, detail="model is required")

    prompt = body.get("prompt", "Say hello in one sentence.")
    return await ollama_service.test_generation(model_name, prompt)
