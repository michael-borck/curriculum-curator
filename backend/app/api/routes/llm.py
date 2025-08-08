import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.content import ContentGenerationRequest
from app.services.llm_service import llm_service

router = APIRouter()

@router.post("/generate")
async def generate_content(request: ContentGenerationRequest):
    """Generate content with AI assistance"""
    try:
        async def stream_response():
            async for chunk in llm_service.generate_content(
                content_type=request.content_type,
                pedagogy_style=request.pedagogy_style,
                context=request.context,
                stream=request.stream
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

        if request.stream:
            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream"
            )
        result = ""
        async for chunk in llm_service.generate_content(
            content_type=request.content_type,
            pedagogy_style=request.pedagogy_style,
            context=request.context,
            stream=False
        ):
            result += chunk
        return {"content": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance")
async def enhance_content(request: dict[str, Any]):
    """Enhance existing content with AI"""
    # Implementation for content enhancement

@router.post("/analyze-pedagogy")
async def analyze_pedagogy(content: str):
    """Analyze content for pedagogical alignment"""
    # Implementation for pedagogy analysis
