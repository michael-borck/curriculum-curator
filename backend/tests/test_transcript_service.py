"""Tests for transcript parsing and YouTube fetch service."""

from unittest.mock import MagicMock, patch

import app.services.transcript_service as ts_mod

import pytest

from app.services.transcript_service import (
    extract_youtube_id,
    fetch_youtube_transcript,
    parse_vtt,
)

# ── VTT Parsing ─────────────────────────────────────────────────

SAMPLE_VTT = """\
WEBVTT

00:00:01.000 --> 00:00:04.500
Hello and welcome to this lecture.

00:00:04.500 --> 00:00:08.200
Today we'll cover the basics
of web development.

00:00:08.200 --> 00:00:12.000
Let's get started.
"""


def test_parse_vtt_standard():
    segments = parse_vtt(SAMPLE_VTT)
    assert len(segments) == 3
    assert segments[0]["start"] == 1.0
    assert segments[0]["end"] == 4.5
    assert segments[0]["text"] == "Hello and welcome to this lecture."
    assert segments[1]["text"] == "Today we'll cover the basics of web development."
    assert segments[2]["start"] == 8.2


SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:04,500
Hello and welcome.

2
00:00:04,500 --> 00:00:08,200
Today we cover the basics.

3
00:00:08,200 --> 00:00:12,000
Let's get started.
"""


def test_parse_srt_standard():
    segments = parse_vtt(SAMPLE_SRT)
    assert len(segments) == 3
    assert segments[0]["start"] == 1.0
    assert segments[0]["end"] == 4.5
    assert segments[0]["text"] == "Hello and welcome."
    assert segments[2]["start"] == 8.2


def test_parse_vtt_with_html_tags():
    vtt = """\
WEBVTT

00:00:01.000 --> 00:00:05.000
<b>Important:</b> This is <i>key</i> content.
"""
    segments = parse_vtt(vtt)
    assert len(segments) == 1
    assert segments[0]["text"] == "Important: This is key content."


def test_parse_vtt_empty_input():
    assert parse_vtt("") == []
    assert parse_vtt("WEBVTT\n\n") == []


def test_parse_vtt_with_hours():
    vtt = """\
WEBVTT

1:30:00.000 --> 1:35:00.000
This is after 90 minutes.
"""
    segments = parse_vtt(vtt)
    assert len(segments) == 1
    assert segments[0]["start"] == 5400.0
    assert segments[0]["end"] == 5700.0


def test_merge_consecutive_duplicates():
    vtt = """\
WEBVTT

00:00:01.000 --> 00:00:02.000
Hello world.

00:00:02.000 --> 00:00:03.000
Hello world.

00:00:03.000 --> 00:00:05.000
Something different.
"""
    segments = parse_vtt(vtt)
    assert len(segments) == 2
    assert segments[0]["text"] == "Hello world."
    assert segments[0]["start"] == 1.0
    assert segments[0]["end"] == 3.0  # merged
    assert segments[1]["text"] == "Something different."


# ── YouTube ID Extraction ────────────────────────────────────────


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://example.com/not-youtube", None),
        ("not-a-url", None),
    ],
)
def test_extract_youtube_id(url: str, expected: str | None):
    assert extract_youtube_id(url) == expected


# ── YouTube Fetch ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_youtube_transcript_success():
    mock_entry_1 = MagicMock()
    mock_entry_1.start = 0.0
    mock_entry_1.duration = 5.0
    mock_entry_1.text = "Hello"

    mock_entry_2 = MagicMock()
    mock_entry_2.start = 5.0
    mock_entry_2.duration = 4.0
    mock_entry_2.text = "World"

    mock_transcript = [mock_entry_1, mock_entry_2]

    mock_api_instance = MagicMock()
    mock_api_instance.fetch.return_value = mock_transcript

    mock_cls = MagicMock(return_value=mock_api_instance)
    with patch.object(ts_mod, "YouTubeTranscriptApi", mock_cls):
        result = await fetch_youtube_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

    assert result["source"] == "youtube"
    assert len(result["segments"]) == 2
    assert result["segments"][0]["start"] == 0.0
    assert result["segments"][0]["end"] == 5.0
    assert result["segments"][0]["text"] == "Hello"


@pytest.mark.asyncio
async def test_fetch_youtube_transcript_invalid_url():
    with pytest.raises(ValueError, match="Could not extract YouTube video ID"):
        await fetch_youtube_transcript("https://example.com/not-youtube")


@pytest.mark.asyncio
async def test_fetch_youtube_transcript_api_error():
    mock_api_instance = MagicMock()
    mock_api_instance.fetch.side_effect = Exception("No captions available")

    mock_cls = MagicMock(return_value=mock_api_instance)
    with (
        patch.object(
            __import__("app.services.transcript_service", fromlist=["YouTubeTranscriptApi"]),
            "YouTubeTranscriptApi",
            mock_cls,
        ),
        pytest.raises(ValueError, match="Could not fetch transcript"),
    ):
        await fetch_youtube_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
