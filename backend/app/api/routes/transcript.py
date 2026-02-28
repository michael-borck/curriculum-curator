"""
Transcript API routes — fetch YouTube transcripts and parse VTT/SRT uploads.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.schemas.user import UserResponse
from app.services.transcript_service import fetch_youtube_transcript, parse_vtt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcript", tags=["transcript"])


class YouTubeRequest(BaseModel):
    url: str


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptResponse(BaseModel):
    segments: list[TranscriptSegment]
    source: str
    language: str | None = None


@router.post("/fetch-youtube", response_model=TranscriptResponse)
async def fetch_youtube(
    body: YouTubeRequest,
    _current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> dict[str, Any]:
    """Fetch auto-generated transcript from a YouTube video."""
    try:
        result = await fetch_youtube_transcript(body.url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return result


@router.post("/parse-vtt", response_model=TranscriptResponse)
async def parse_vtt_upload(
    file: UploadFile,
    _current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> dict[str, Any]:
    """Parse an uploaded VTT or SRT subtitle file."""
    if file.filename and not file.filename.lower().endswith((".vtt", ".srt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be .vtt or .srt format",
        )

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    segments = parse_vtt(text)

    return {
        "segments": segments,
        "source": "upload",
        "language": None,
    }
