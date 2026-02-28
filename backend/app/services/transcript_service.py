"""
Transcript parsing and fetching service.

Supports:
- WebVTT (.vtt) and SRT (.srt) subtitle parsing
- YouTube auto-caption fetching via youtube-transcript-api
"""

import logging
import re
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)

# Timestamp patterns
# VTT: 00:00:01.234 --> 00:00:05.678  (hours optional)
# SRT: 00:00:01,234 --> 00:00:05,678  (comma for millis)
_TIMESTAMP_RE = re.compile(
    r"(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{1,2}:)?(\d{2}):(\d{2})[.,](\d{3})"
)

# YouTube URL patterns
_YT_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)"
    r"([a-zA-Z0-9_-]{11})"
)

# HTML tag stripper
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _parse_timestamp(
    hours: str | None, minutes: str, seconds: str, millis: str
) -> float:
    """Convert timestamp parts to seconds as float."""
    h = int(hours.rstrip(":")) if hours else 0
    return h * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def _strip_html(text: str) -> str:
    """Remove HTML tags from subtitle text."""
    return _HTML_TAG_RE.sub("", text)


def _merge_consecutive(
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge consecutive segments with identical text (common in YouTube auto-captions)."""
    if not segments:
        return segments

    merged: list[dict[str, Any]] = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        if seg["text"].strip() == prev["text"].strip():
            prev["end"] = seg["end"]
        else:
            merged.append(seg.copy())
    return merged


def _flush_cue(
    segments: list[dict[str, Any]],
    start: float | None,
    end: float | None,
    text_lines: list[str],
) -> None:
    """Flush accumulated cue text into a segment dict."""
    if start is None or not text_lines:
        return
    text = _strip_html(" ".join(text_lines).strip())
    if text:
        segments.append({"start": start, "end": end, "text": text})


def parse_vtt(content: str) -> list[dict[str, Any]]:
    """Parse WebVTT or SRT subtitle text into segment dicts.

    Returns list of ``{"start": float, "end": float, "text": str}``
    sorted by start time.
    """
    segments: list[dict[str, Any]] = []
    lines = content.splitlines()

    current_start: float | None = None
    current_end: float | None = None
    text_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Skip VTT header, NOTE blocks
        if stripped.upper().startswith(("WEBVTT", "NOTE")):
            continue

        # SRT cue number — flush any pending cue
        if stripped.isdigit():
            _flush_cue(segments, current_start, current_end, text_lines)
            text_lines = []
            current_start = None
            current_end = None
            continue

        # Check for timestamp line
        m = _TIMESTAMP_RE.search(stripped)
        if m:
            _flush_cue(segments, current_start, current_end, text_lines)
            text_lines = []
            current_start = _parse_timestamp(m.group(1), m.group(2), m.group(3), m.group(4))
            current_end = _parse_timestamp(m.group(5), m.group(6), m.group(7), m.group(8))
            continue

        # Blank line = cue boundary
        if not stripped:
            _flush_cue(segments, current_start, current_end, text_lines)
            text_lines = []
            current_start = None
            current_end = None
            continue

        # Text line
        if current_start is not None:
            text_lines.append(stripped)

    # Flush last cue
    _flush_cue(segments, current_start, current_end, text_lines)

    return _merge_consecutive(segments)


def extract_youtube_id(url: str) -> str | None:
    """Extract the 11-character video ID from a YouTube URL."""
    m = _YT_ID_RE.search(url)
    return m.group(1) if m else None


async def fetch_youtube_transcript(
    url: str,
) -> dict[str, Any]:
    """Fetch transcript segments from a YouTube video.

    Returns ``{"segments": [...], "language": str, "source": "youtube"}``.
    Raises ``ValueError`` on failure.
    """
    video_id = extract_youtube_id(url)
    if not video_id:
        msg = f"Could not extract YouTube video ID from URL: {url}"
        raise ValueError(msg)

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
    except Exception as exc:
        logger.warning("YouTube transcript fetch failed for %s: %s", video_id, exc)
        msg = f"Could not fetch transcript: {exc}"
        raise ValueError(msg) from exc

    segments: list[dict[str, Any]] = [
        {
            "start": float(entry.start),
            "end": float(entry.start + entry.duration),
            "text": str(entry.text),
        }
        for entry in transcript
    ]

    language = "en"

    return {
        "segments": _merge_consecutive(segments),
        "language": language,
        "source": "youtube",
    }
