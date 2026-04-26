"""Playwright-based wrappers for outline-dl and course-dl libraries.

All `_*_sync` functions block and must be called via `asyncio.to_thread`.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class CurtinServiceError(RuntimeError):
    """Raised for expected failures (bad credentials, not found, not ready)."""


def _forgerock_login(
    page: Any,
    url: str,
    username: str,
    password: str,
    timeout: int = 30000,
) -> None:
    """Log in to a Curtin ForgeRock SSO-protected URL.

    ForgeRock uses input[name='callback_1'] for the username step,
    then input[type='password'] for the password step.
    """
    page.goto(url, wait_until="networkidle", timeout=timeout)

    try:
        page.wait_for_selector("input[name='callback_1']", timeout=timeout)
    except PlaywrightTimeout as exc:
        raise CurtinServiceError(
            f"Could not find SSO username field at {url} — check the URL in Curtin Settings"
        ) from exc

    page.fill("input[name='callback_1']", username)
    page.click("button[type='submit']")
    page.wait_for_timeout(3000)

    try:
        page.wait_for_selector("input[type='password']", timeout=timeout)
    except PlaywrightTimeout as exc:
        raise CurtinServiceError(
            "Could not find SSO password field — check your credentials"
        ) from exc

    page.fill("input[type='password']", password)
    page.click("button[type='submit']")
    page.wait_for_timeout(5000)
    page.wait_for_load_state("networkidle", timeout=timeout)

    if "curtin.edu.au" not in page.url:
        raise CurtinServiceError(
            f"Login may have failed — unexpected redirect to {page.url}. Check your credentials."
        )


def _download_outline_sync(
    unit_code: str,
    username: str,
    password: str,
    litec_url: str,
    campus: str,
) -> tuple[str, bytes]:
    """Download a unit outline PDF and return (filename, bytes)."""
    from outline_dl.downloader import download_outlines  # noqa: PLC0415
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _forgerock_login(page, litec_url, username, password)
            with tempfile.TemporaryDirectory() as tmpdir:
                results = download_outlines(
                    page,
                    [unit_code],
                    Path(tmpdir),
                    campus=campus,
                    interactive=False,
                )
                if results.get(unit_code) != "ok":
                    raise CurtinServiceError(
                        f"Outline download failed for {unit_code}: {results.get(unit_code, 'unknown error')}. "
                        "Check the unit code is correct and has a current outline."
                    )
                pdfs = list(Path(tmpdir).glob("*.pdf"))
                if not pdfs:
                    raise CurtinServiceError(
                        f"No PDF produced for {unit_code} — the outline may not exist for the selected campus."
                    )
                f = pdfs[0]
                return f.name, f.read_bytes()
        finally:
            browser.close()


async def download_outline(
    unit_code: str,
    username: str,
    password: str,
    litec_url: str,
    campus: str,
) -> tuple[str, bytes]:
    """Async entry point — runs the sync download in a thread."""
    return await asyncio.to_thread(
        _download_outline_sync, unit_code, username, password, litec_url, campus
    )


def _trigger_build_sync(
    course_name: str,
    username: str,
    password: str,
    bb_url: str,
) -> None:
    """Log in to Blackboard and trigger a Common Cartridge export build."""
    from course_dl.exporter import (  # noqa: PLC0415
        build_packages,
        fuzzy_match_courses,
        get_available_courses,
    )
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _forgerock_login(page, bb_url, username, password)
            courses = get_available_courses(page)
            targets = fuzzy_match_courses(courses, [course_name], threshold=60)
            if not targets:
                raise CurtinServiceError(
                    f"No Blackboard course found matching '{course_name}'. "
                    "Check the course name — use the full name or a unique substring."
                )
            results = build_packages(page, targets)
            label = targets[0]["name"]
            status = results.get(label, "unknown")
            if status != "queued":
                raise CurtinServiceError(f"Build trigger failed for '{label}': {status}")
        finally:
            browser.close()


async def trigger_course_build(
    course_name: str,
    username: str,
    password: str,
    bb_url: str,
) -> None:
    """Async entry point — triggers the Blackboard export in a thread."""
    await asyncio.to_thread(_trigger_build_sync, course_name, username, password, bb_url)


def _download_archive_sync(
    course_name: str,
    username: str,
    password: str,
    bb_url: str,
) -> tuple[str, bytes]:
    """Download a ready Blackboard Common Cartridge archive.

    Raises CurtinServiceError("not_ready") if the archive isn't built yet.
    """
    from course_dl.exporter import (  # noqa: PLC0415
        download_packages,
        fuzzy_match_courses,
        get_available_courses,
    )
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _forgerock_login(page, bb_url, username, password)
            courses = get_available_courses(page)
            targets = fuzzy_match_courses(courses, [course_name], threshold=60)
            if not targets:
                raise CurtinServiceError(
                    f"No Blackboard course found matching '{course_name}'"
                )
            with tempfile.TemporaryDirectory() as tmpdir:
                results = download_packages(page, targets, Path(tmpdir))
                label = targets[0]["name"]
                status = results.get(label, "unknown")
                if status == "not ready":
                    raise CurtinServiceError("not_ready")
                if status not in ("ok", "skipped"):
                    raise CurtinServiceError(
                        f"Archive download failed for '{label}': {status}"
                    )
                files = [
                    f for f in Path(tmpdir).iterdir()
                    if f.suffix in (".zip", ".imscc")
                ]
                if not files:
                    raise CurtinServiceError("not_ready")
                f = files[0]
                return f.name, f.read_bytes()
        finally:
            browser.close()


async def download_course_archive(
    course_name: str,
    username: str,
    password: str,
    bb_url: str,
) -> tuple[str, bytes]:
    """Async entry point — downloads the Blackboard archive in a thread."""
    return await asyncio.to_thread(
        _download_archive_sync, course_name, username, password, bb_url
    )
