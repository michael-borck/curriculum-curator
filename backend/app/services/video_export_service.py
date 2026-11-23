"""Render a narrated MP4 from a slide-style material.

Narration is synthesized with the operating system's own voice (macOS `say`,
Windows SAPI, Linux `espeak-ng`), so no text is sent to a cloud TTS service.
Slides are rendered locally with Pillow and assembled with ffmpeg.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.services.slide_splitter import split_at_slide_breaks

WIDTH, HEIGHT = 1280, 720
MAX_BODY_LINES = 12


class VideoExportUnavailableError(RuntimeError):
    """Raised when a required local binary is missing."""


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg  # noqa: PLC0415

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        path = shutil.which("ffmpeg")
        if path:
            return path
        raise VideoExportUnavailableError(
            "ffmpeg is not available. Install ffmpeg (or the backend's "
            "imageio-ffmpeg dependency) to export video."
        ) from None


def _tts_backend() -> str:
    if sys.platform == "darwin" and shutil.which("say"):
        return "say"
    if os.name == "nt":
        return "sapi"
    if shutil.which("espeak-ng"):
        return "espeak-ng"
    if shutil.which("espeak"):
        return "espeak"
    raise VideoExportUnavailableError(
        "No local text-to-speech engine found. On Linux install espeak-ng; "
        "macOS and Windows include a system voice."
    )


def capabilities() -> dict[str, Any]:
    try:
        return {"available": True, "ffmpeg": _ffmpeg(), "tts": _tts_backend()}
    except VideoExportUnavailableError as exc:
        return {"available": False, "reason": str(exc)}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                pass
    return ImageFont.load_default(size=size)


def _node_text(node: dict[str, Any]) -> str:
    if node.get("type") == "speakerNotes":
        return ""
    if isinstance(node.get("text"), str):
        return node["text"]
    return " ".join(
        filter(None, (_node_text(child) for child in node.get("content") or []))
    )


def _slide_text(segment: dict[str, Any]) -> str:
    return " ".join(
        filter(None, (_node_text(node) for node in segment.get("content") or []))
    ).strip()


def _notes_text(segment: dict[str, Any]) -> str:
    parts: list[str] = []
    for node in segment.get("content") or []:
        if node.get("type") != "speakerNotes":
            continue
        text = " ".join(
            filter(None, (_node_text(child) for child in node.get("content") or []))
        ).strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _title_for(segment: dict[str, Any], index: int, fallback: str) -> str:
    for node in segment.get("content") or []:
        if node.get("type") == "heading":
            text = _node_text(node).strip()
            if text:
                return text
    return f"{fallback} — slide {index + 1}"


def _wrap(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    limit: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= limit:
                break
    if current and len(lines) < limit:
        lines.append(current)
    return lines


def _render_slide(title: str, body: str, index: int, total: int, path: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#0f172a")
    draw = ImageDraw.Draw(image)
    title_font = _font(52)
    body_font = _font(30)
    footer_font = _font(20)

    draw.rectangle((0, 0, 14, HEIGHT), fill="#a78bfa")
    draw.text((70, 64), title, font=title_font, fill="#f8fafc")
    draw.line((70, 145, WIDTH - 70, 145), fill="#334155", width=2)

    y = 190
    for line in _wrap(body, body_font, WIDTH - 140, MAX_BODY_LINES):
        draw.text((70, y), line, font=body_font, fill="#cbd5e1")
        y += 44

    draw.text(
        (WIDTH - 70, HEIGHT - 50),
        f"{index + 1} / {total}",
        font=footer_font,
        fill="#64748b",
        anchor="ra",
    )
    image.save(path, "PNG")


def _synthesize(text: str, path: Path, backend: str, ffmpeg: str) -> None:
    text_file = path.with_suffix(".txt")
    text_file.write_text(text or " ", encoding="utf-8")
    raw = path.with_suffix(".raw")
    try:
        if backend == "say":
            subprocess.run(
                ["say", "-f", str(text_file), "-o", str(raw)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [ffmpeg, "-y", "-i", str(raw), "-ar", "22050", "-ac", "1", str(path)],
                check=True,
                capture_output=True,
            )
        elif backend in ("espeak-ng", "espeak"):
            subprocess.run(
                [backend, "-w", str(path), "-f", str(text_file)],
                check=True,
                capture_output=True,
            )
        else:  # Windows SAPI
            script = path.with_suffix(".ps1")
            script.write_text(
                "Add-Type -AssemblyName System.Speech\n"
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
                f"$s.SetOutputToWaveFile('{path}')\n"
                f"$s.Speak([IO.File]::ReadAllText('{text_file}'))\n"
                "$s.Dispose()\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                ],
                check=True,
                capture_output=True,
            )
    finally:
        text_file.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)
        if path.with_suffix(".ps1").exists():
            path.with_suffix(".ps1").unlink()


def build_video(
    title: str, content_json: dict[str, Any], output_path: str
) -> str:
    """Render a narrated MP4 and return its path."""
    ffmpeg = _ffmpeg()
    backend = _tts_backend()
    segments = split_at_slide_breaks(content_json) if content_json else []
    if not segments:
        raise VideoExportUnavailableError("This material has no slide content")

    with tempfile.TemporaryDirectory(prefix="cc-video-") as temp:
        temp_dir = Path(temp)
        concat_lines: list[str] = []
        for index, segment in enumerate(segments):
            slide_title = _title_for(segment, index, title)
            body = _slide_text(segment)
            narration = _notes_text(segment) or body
            image = temp_dir / f"slide-{index:03d}.png"
            audio = temp_dir / f"audio-{index:03d}.wav"
            segment_path = temp_dir / f"segment-{index:03d}.mp4"

            _render_slide(slide_title, body, index, len(segments), image)
            _synthesize(narration, audio, backend, ffmpeg)
            if not audio.exists() or audio.stat().st_size == 0:
                raise VideoExportUnavailableError("The system voice produced no audio")

            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(image),
                    "-i",
                    str(audio),
                    "-c:v",
                    "libx264",
                    "-tune",
                    "stillimage",
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    "25",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-shortest",
                    str(segment_path),
                ],
                check=True,
                capture_output=True,
            )
            concat_lines.append(f"file '{segment_path.name}'")

        concat_file = temp_dir / "concat.txt"
        concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
    return output_path


