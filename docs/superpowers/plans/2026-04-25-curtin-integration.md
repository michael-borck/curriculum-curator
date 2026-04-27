# Curtin Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate `outline-dl` and `course-dl` (both already published on PyPI by the same author) into the curriculum-curator import workflow, letting users download Curtin unit outline PDFs and Blackboard course archives directly from the app instead of manually downloading and uploading.

**Architecture:** Both libraries use Playwright + ForgeRock SSO (headless Chromium); we run them in a thread pool via `asyncio.to_thread` so FastAPI stays non-blocking. Per-user credentials (Curtin username/password) and configurable base URLs are stored in the existing `User.teaching_preferences["curtin"]` JSON blob — same pattern as Research settings. The outline download feeds into the existing `parseOutline`/`applyOutline` flow; the course archive hands a pre-seeded File to the existing `PackageImport` page via React Router state.

**Tech Stack:** `outline-dl 0.2.1`, `course-dl 0.3.1`, `playwright`, Python `asyncio.to_thread`, FastAPI, SQLAlchemy, React + TypeScript, React Router v6.

---

## File Map

**New backend files:**
- `backend/app/models/curtin_job.py` — `CurtinExportJob` SQLAlchemy model (tracks course archive build jobs)
- `backend/app/schemas/curtin.py` — Pydantic schemas for settings + requests + responses
- `backend/app/services/curtin_service.py` — Playwright wrappers (sync fns + async thread-executor entry points)
- `backend/app/api/routes/curtin_import.py` — 6 FastAPI routes
- `backend/tests/test_curtin_service.py` — unit tests (mocked Playwright)

**Modified backend files:**
- `backend/pyproject.toml` — add `outline-dl`, `course-dl`, `playwright` deps
- `backend/app/models/__init__.py` — export `CurtinExportJob`
- `backend/app/main.py` — register `curtin_import` router

**New frontend files:**
- `frontend/src/services/curtinApi.ts` — Axios calls to Curtin routes
- `frontend/src/features/settings/CurtinSettings.tsx` — settings form component
- `frontend/src/features/import/CurtinImport.tsx` — import page (outline + course sections)

**Modified frontend files:**
- `frontend/src/features/settings/Settings.tsx` — add "Curtin" tab
- `frontend/src/features/import/PackageImport.tsx` — accept pre-seeded `File` from router state
- `frontend/src/App.tsx` — register `/import/curtin` route

---

## Task 1: Add backend dependencies

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add the three packages to `[project].dependencies`**

In `backend/pyproject.toml`, append to the `dependencies` array (after the existing doc-processing entries):

```toml
    # Curtin integration
    "outline-dl>=0.2.1",
    "course-dl>=0.3.1",
    "playwright>=1.40.0",
```

- [ ] **Step 2: Sync the venv**

```bash
cd backend
uv sync
```

Expected: `outline-dl`, `course-dl`, `playwright`, and `rapidfuzz` appear in the resolved packages.

- [ ] **Step 3: Install the Playwright browser binary**

```bash
cd backend
.venv/bin/playwright install chromium
```

Expected: Downloads Chromium browser to `~/.cache/ms-playwright/`. One-time operation per machine.

- [ ] **Step 4: Verify imports work**

```bash
cd backend
.venv/bin/python -c "import outline_dl; import course_dl; from playwright.sync_api import sync_playwright; print('OK')"
```

Expected output: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add outline-dl, course-dl, playwright dependencies"
```

---

## Task 2: CurtinExportJob database model

**Files:**
- Create: `backend/app/models/curtin_job.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_curtin_service.py` (model test only at this stage)

- [ ] **Step 1: Write the failing model test**

Create `backend/tests/test_curtin_service.py`:

```python
"""Tests for Curtin integration service and routes."""

from app.models.curtin_job import CurtinExportJob


def test_curtin_job_model_exists() -> None:
    assert CurtinExportJob.__tablename__ == "curtin_export_jobs"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py::test_curtin_job_model_exists -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.curtin_job'`

- [ ] **Step 3: Create the model**

Create `backend/app/models/curtin_job.py`:

```python
"""SQLAlchemy model tracking Blackboard course-archive export jobs."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.common import GUID


class CurtinExportJob(Base):
    __tablename__ = "curtin_export_jobs"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_name: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(20), default="triggered"
    )  # triggered | downloaded | failed
    triggered_at: Mapped[datetime] = mapped_column(default=func.now())
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Step 4: Export from models package**

In `backend/app/models/__init__.py`, add:

```python
from .curtin_job import CurtinExportJob
```

And add `"CurtinExportJob"` to `__all__`.

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py::test_curtin_job_model_exists -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/curtin_job.py backend/app/models/__init__.py backend/tests/test_curtin_service.py
git commit -m "feat(curtin): add CurtinExportJob model"
```

---

## Task 3: Pydantic schemas

**Files:**
- Create: `backend/app/schemas/curtin.py`
- Modify: `backend/tests/test_curtin_service.py`

- [ ] **Step 1: Write the failing schema tests**

Append to `backend/tests/test_curtin_service.py`:

```python
from app.schemas.curtin import CurtinSettings, CurtinJobResponse


def test_curtin_settings_defaults() -> None:
    s = CurtinSettings()
    assert s.litec_url == "https://litec.curtin.edu.au/outline.cfm"
    assert s.blackboard_url == "https://lms.curtin.edu.au/"
    assert s.campus == "Bentley Perth Campus"
    assert s.curtin_username == ""
    assert s.curtin_password == ""


def test_curtin_settings_camel_alias() -> None:
    """Schema serialises snake_case to camelCase for the frontend."""
    s = CurtinSettings(curtin_username="u", curtin_password="p")
    d = s.model_dump(by_alias=True)
    assert "curtinUsername" in d
    assert "curtinPassword" in d
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py -k "settings" -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create the schemas file**

Create `backend/app/schemas/curtin.py`:

```python
"""Pydantic schemas for Curtin integration endpoints."""

from __future__ import annotations

from datetime import datetime

from app.schemas.base import CamelModel


class CurtinSettings(CamelModel):
    curtin_username: str = ""
    curtin_password: str = ""
    litec_url: str = "https://litec.curtin.edu.au/outline.cfm"
    blackboard_url: str = "https://lms.curtin.edu.au/"
    campus: str = "Bentley Perth Campus"


class CurtinOutlineRequest(CamelModel):
    unit_code: str


class CurtinCourseBuildRequest(CamelModel):
    course_name: str


class CurtinJobResponse(CamelModel):
    id: str
    course_name: str
    status: str
    triggered_at: datetime
    error_message: str | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py -k "settings" -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/curtin.py backend/tests/test_curtin_service.py
git commit -m "feat(curtin): add Pydantic schemas"
```

---

## Task 4: Backend service with Playwright wrappers

**Files:**
- Create: `backend/app/services/curtin_service.py`
- Modify: `backend/tests/test_curtin_service.py`

- [ ] **Step 1: Write the failing service tests**

Append to `backend/tests/test_curtin_service.py`:

```python
import pytest
from unittest.mock import MagicMock, patch, call
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from app.services.curtin_service import _forgerock_login, CurtinServiceError


def test_forgerock_login_raises_on_username_field_not_found() -> None:
    """_forgerock_login raises CurtinServiceError when SSO field is absent."""
    mock_page = MagicMock()
    mock_page.wait_for_selector.side_effect = PlaywrightTimeout("timeout")

    with pytest.raises(CurtinServiceError, match="Could not find SSO username field"):
        _forgerock_login(mock_page, "https://litec.curtin.edu.au/outline.cfm", "user", "pass")


def test_forgerock_login_raises_on_wrong_redirect() -> None:
    """_forgerock_login raises CurtinServiceError when login redirects away from curtin.edu.au."""
    mock_page = MagicMock()
    mock_page.wait_for_selector.return_value = None  # field found
    mock_page.url = "https://unexpected-domain.com/error"

    with pytest.raises(CurtinServiceError, match="Login may have failed"):
        _forgerock_login(mock_page, "https://litec.curtin.edu.au/outline.cfm", "user", "pass")


def test_forgerock_login_succeeds() -> None:
    """_forgerock_login completes without error on happy path."""
    mock_page = MagicMock()
    mock_page.wait_for_selector.return_value = None
    mock_page.url = "https://litec.curtin.edu.au/outline.cfm"

    _forgerock_login(mock_page, "https://litec.curtin.edu.au/outline.cfm", "user", "pass")

    mock_page.goto.assert_called_once_with(
        "https://litec.curtin.edu.au/outline.cfm",
        wait_until="networkidle",
        timeout=30000,
    )
    mock_page.fill.assert_any_call("input[name='callback_1']", "user")
    mock_page.fill.assert_any_call("input[type='password']", "pass")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py -k "forgerock" -v
```

Expected: FAIL with `ImportError: cannot import name '_forgerock_login'`

- [ ] **Step 3: Create the service**

Create `backend/app/services/curtin_service.py`:

```python
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
    from playwright.sync_api import sync_playwright
    from outline_dl.downloader import download_outlines

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
    from playwright.sync_api import sync_playwright
    from course_dl.exporter import build_packages, fuzzy_match_courses, get_available_courses

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
    from playwright.sync_api import sync_playwright
    from course_dl.exporter import download_packages, fuzzy_match_courses, get_available_courses

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py -k "forgerock" -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Run full linter and type check**

```bash
cd backend
.venv/bin/ruff check app/services/curtin_service.py
.venv/bin/basedpyright app/services/curtin_service.py
```

Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/curtin_service.py backend/tests/test_curtin_service.py
git commit -m "feat(curtin): add curtin_service with Playwright wrappers"
```

---

## Task 5: Backend API routes

**Files:**
- Create: `backend/app/api/routes/curtin_import.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_curtin_service.py`

- [ ] **Step 1: Write the failing route tests**

Append to `backend/tests/test_curtin_service.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.api.deps import get_current_active_user, get_db

client = TestClient(app)


def _override_deps(test_db: Session, test_user: User) -> None:
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_current_active_user] = lambda: test_user


def _clear_deps() -> None:
    app.dependency_overrides.clear()


def test_get_curtin_settings_returns_defaults(test_db: Session, test_user: User) -> None:
    """GET /api/curtin/settings returns defaults when no curtin prefs stored."""
    _override_deps(test_db, test_user)
    try:
        r = client.get("/api/curtin/settings")
        assert r.status_code == 200
        data = r.json()
        assert data["litecUrl"] == "https://litec.curtin.edu.au/outline.cfm"
        assert data["blackboardUrl"] == "https://lms.curtin.edu.au/"
        assert data["campus"] == "Bentley Perth Campus"
        assert data["curtinUsername"] == ""
    finally:
        _clear_deps()


def test_put_curtin_settings_persists(test_db: Session, test_user: User) -> None:
    """PUT /api/curtin/settings saves and GET returns the updated values."""
    _override_deps(test_db, test_user)
    try:
        r = client.put(
            "/api/curtin/settings",
            json={
                "curtinUsername": "jsmith",
                "curtinPassword": "secret",
                "litecUrl": "https://litec.curtin.edu.au/outline.cfm",
                "blackboardUrl": "https://lms.curtin.edu.au/",
                "campus": "Bentley Perth Campus",
            },
        )
        assert r.status_code == 200
        r2 = client.get("/api/curtin/settings")
        assert r2.json()["curtinUsername"] == "jsmith"
    finally:
        _clear_deps()


def test_outline_download_rejects_missing_credentials(test_db: Session, test_user: User) -> None:
    """POST /api/curtin/outline/download returns 400 when no credentials set."""
    _override_deps(test_db, test_user)
    try:
        r = client.post("/api/curtin/outline/download", json={"unitCode": "COMP1000"})
        assert r.status_code == 400
        assert "credentials" in r.json()["detail"].lower()
    finally:
        _clear_deps()


def test_course_build_rejects_missing_credentials(test_db: Session, test_user: User) -> None:
    """POST /api/curtin/course/build returns 400 when no credentials set."""
    _override_deps(test_db, test_user)
    try:
        r = client.post("/api/curtin/course/build", json={"courseName": "COMP1000"})
        assert r.status_code == 400
    finally:
        _clear_deps()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py -k "settings or credentials" -v
```

Expected: FAIL with 404 (routes not registered yet)

- [ ] **Step 3: Create the routes file**

Create `backend/app/api/routes/curtin_import.py`:

```python
"""Curtin-specific import routes: outline PDF download and Blackboard course archive."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import deps
from app.models.curtin_job import CurtinExportJob
from app.models.user import User
from app.schemas.curtin import (
    CurtinCourseBuildRequest,
    CurtinJobResponse,
    CurtinOutlineRequest,
    CurtinSettings,
)
from app.services import curtin_service
from app.services.curtin_service import CurtinServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/curtin", tags=["curtin"])


def _load_settings(user: User) -> CurtinSettings:
    prefs = user.teaching_preferences or {}
    curtin = prefs.get("curtin")
    if isinstance(curtin, dict):
        return CurtinSettings(**curtin)
    return CurtinSettings()


def _require_credentials(cfg: CurtinSettings) -> None:
    if not cfg.curtin_username or not cfg.curtin_password:
        raise HTTPException(
            status_code=400,
            detail="Curtin credentials not configured — add your username and password in Settings → Curtin.",
        )


# ── Settings ─────────────────────────────────────────────────────────────────


@router.get("/settings", response_model=CurtinSettings)
def get_settings(
    current_user: User = Depends(deps.get_current_active_user),
) -> CurtinSettings:
    return _load_settings(current_user)


@router.put("/settings", response_model=CurtinSettings)
def update_settings(
    data: CurtinSettings,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> CurtinSettings:
    prefs = dict(current_user.teaching_preferences or {})
    prefs["curtin"] = data.model_dump()
    current_user.teaching_preferences = prefs
    db.commit()
    return data


# ── Outline download ──────────────────────────────────────────────────────────


@router.post("/outline/download")
async def download_outline(
    request: CurtinOutlineRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Response:
    """Download a unit outline PDF from LITEC and return it as application/pdf."""
    cfg = _load_settings(current_user)
    _require_credentials(cfg)

    try:
        filename, pdf_bytes = await curtin_service.download_outline(
            request.unit_code.upper().strip(),
            cfg.curtin_username,
            cfg.curtin_password,
            cfg.litec_url,
            cfg.campus,
        )
    except CurtinServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Outline download failed for %s", request.unit_code)
        raise HTTPException(status_code=502, detail="Outline download failed — see server logs.") from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Course archive ────────────────────────────────────────────────────────────


@router.post("/course/build", response_model=CurtinJobResponse, status_code=201)
async def build_course_archive(
    request: CurtinCourseBuildRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> CurtinJobResponse:
    """Trigger a Blackboard Common Cartridge export build.

    Returns immediately with a job record. The build takes 15-30 minutes on
    Blackboard's side. Call /course/download/{job_id} when ready.
    """
    cfg = _load_settings(current_user)
    _require_credentials(cfg)

    job = CurtinExportJob(
        user_id=str(current_user.id),
        course_name=request.course_name,
        status="triggered",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        await curtin_service.trigger_course_build(
            request.course_name,
            cfg.curtin_username,
            cfg.curtin_password,
            cfg.blackboard_url,
        )
    except CurtinServiceError as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        job.status = "failed"
        job.error_message = "Unexpected error"
        db.commit()
        logger.exception("Course build trigger failed for %s", request.course_name)
        raise HTTPException(status_code=502, detail="Build trigger failed — see server logs.") from exc

    return CurtinJobResponse.model_validate(job)


@router.get("/course/jobs", response_model=list[CurtinJobResponse])
def list_course_jobs(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> list[CurtinJobResponse]:
    """List all course archive jobs for the current user, newest first."""
    jobs = (
        db.query(CurtinExportJob)
        .filter(CurtinExportJob.user_id == str(current_user.id))
        .order_by(CurtinExportJob.triggered_at.desc())
        .all()
    )
    return [CurtinJobResponse.model_validate(j) for j in jobs]


@router.post("/course/download/{job_id}")
async def download_course_archive(
    job_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Response:
    """Download a ready Blackboard course archive.

    Returns 409 if Blackboard hasn't finished building it yet.
    """
    job = (
        db.query(CurtinExportJob)
        .filter(
            CurtinExportJob.id == job_id,
            CurtinExportJob.user_id == str(current_user.id),
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    cfg = _load_settings(current_user)
    _require_credentials(cfg)

    try:
        filename, archive_bytes = await curtin_service.download_course_archive(
            job.course_name,
            cfg.curtin_username,
            cfg.curtin_password,
            cfg.blackboard_url,
        )
    except CurtinServiceError as exc:
        if str(exc) == "not_ready":
            raise HTTPException(
                status_code=409,
                detail="Archive not ready yet — Blackboard is still building it. Wait 15-30 minutes and try again.",
            ) from exc
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Course archive download failed for job %s", job_id)
        raise HTTPException(status_code=502, detail="Download failed — see server logs.") from exc

    job.status = "downloaded"
    db.commit()

    return Response(
        content=archive_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 4: Register router in main.py**

In `backend/app/main.py`, find the block where routers are included (search for `app.include_router`) and add:

```python
from app.api.routes import curtin_import
# ... (after the other import statements at the top of the file)

app.include_router(curtin_import.router)
```

The exact location: add the import near the other route imports, and the `include_router` call alongside the other `include_router` calls.

- [ ] **Step 5: Run route tests**

```bash
cd backend
.venv/bin/pytest tests/test_curtin_service.py -k "settings or credentials" -v
```

Expected: PASS (4 tests)

- [ ] **Step 6: Run linters**

```bash
cd backend
.venv/bin/ruff check app/api/routes/curtin_import.py
.venv/bin/basedpyright app/api/routes/curtin_import.py
```

Expected: 0 errors

- [ ] **Step 7: Run full test suite**

```bash
cd backend
.venv/bin/pytest --tb=short -q
```

Expected: all existing tests still pass

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/routes/curtin_import.py backend/app/main.py backend/tests/test_curtin_service.py
git commit -m "feat(curtin): add API routes for settings, outline download, course archive"
```

---

## Task 6: Frontend types and API service

**Files:**
- Create: `frontend/src/services/curtinApi.ts`

- [ ] **Step 1: Create the API client**

Create `frontend/src/services/curtinApi.ts`:

```typescript
import api from './api';

export interface CurtinSettings {
  curtinUsername: string;
  curtinPassword: string;
  litecUrl: string;
  blackboardUrl: string;
  campus: string;
}

export interface CurtinJobResponse {
  id: string;
  courseName: string;
  status: 'triggered' | 'downloaded' | 'failed';
  triggeredAt: string;
  errorMessage: string | null;
}

export const getSettings = async (): Promise<CurtinSettings> => {
  const r = await api.get<CurtinSettings>('/api/curtin/settings');
  return r.data;
};

export const saveSettings = async (data: CurtinSettings): Promise<CurtinSettings> => {
  const r = await api.put<CurtinSettings>('/api/curtin/settings', data);
  return r.data;
};

/** Downloads a unit outline PDF. Returns an ArrayBuffer of the PDF bytes. */
export const downloadOutline = async (unitCode: string): Promise<{ filename: string; data: ArrayBuffer }> => {
  const r = await api.post<ArrayBuffer>(
    '/api/curtin/outline/download',
    { unitCode },
    { responseType: 'arraybuffer' },
  );
  const disposition = r.headers['content-disposition'] ?? '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : `${unitCode}.pdf`;
  return { filename, data: r.data };
};

/** Triggers a Blackboard export build. Returns the job record. */
export const triggerCourseBuild = async (courseName: string): Promise<CurtinJobResponse> => {
  const r = await api.post<CurtinJobResponse>('/api/curtin/course/build', { courseName });
  return r.data;
};

export const listCourseJobs = async (): Promise<CurtinJobResponse[]> => {
  const r = await api.get<CurtinJobResponse[]>('/api/curtin/course/jobs');
  return r.data;
};

/**
 * Downloads a ready Blackboard archive for a job.
 * Throws with status 409 if not ready yet.
 */
export const downloadCourseArchive = async (
  jobId: string,
): Promise<{ filename: string; data: ArrayBuffer }> => {
  const r = await api.post<ArrayBuffer>(
    `/api/curtin/course/download/${jobId}`,
    null,
    { responseType: 'arraybuffer' },
  );
  const disposition = r.headers['content-disposition'] ?? '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : 'course-archive.zip';
  return { filename, data: r.data };
};
```

- [ ] **Step 2: Type-check**

```bash
cd frontend
npm run type-check
```

Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/curtinApi.ts
git commit -m "feat(curtin): add frontend API client"
```

---

## Task 7: CurtinSettings component + wire into Settings

**Files:**
- Create: `frontend/src/features/settings/CurtinSettings.tsx`
- Modify: `frontend/src/features/settings/Settings.tsx`

- [ ] **Step 1: Create the settings component**

Create `frontend/src/features/settings/CurtinSettings.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { Save, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';
import * as curtinApi from '../../services/curtinApi';
import type { CurtinSettings as CurtinSettingsType } from '../../services/curtinApi';

const DEFAULT: CurtinSettingsType = {
  curtinUsername: '',
  curtinPassword: '',
  litecUrl: 'https://litec.curtin.edu.au/outline.cfm',
  blackboardUrl: 'https://lms.curtin.edu.au/',
  campus: 'Bentley Perth Campus',
};

const CurtinSettings = () => {
  const [settings, setSettings] = useState<CurtinSettingsType>(DEFAULT);
  const [showPassword, setShowPassword] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    curtinApi.getSettings().then(setSettings).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await curtinApi.saveSettings(settings);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch {
      setError('Failed to save Curtin settings');
    } finally {
      setSaving(false);
    }
  };

  const field = (
    label: string,
    key: keyof CurtinSettingsType,
    type: string = 'text',
    placeholder: string = '',
  ) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="relative">
        <input
          type={key === 'curtinPassword' ? (showPassword ? 'text' : 'password') : type}
          value={settings[key]}
          onChange={e => setSettings(prev => ({ ...prev, [key]: e.target.value }))}
          placeholder={placeholder}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
        />
        {key === 'curtinPassword' && (
          <button
            type="button"
            onClick={() => setShowPassword(v => !v)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Curtin Integration</h3>
        <p className="mt-1 text-sm text-gray-500">
          Download unit outlines and Blackboard course archives directly from Curtin systems.
          Credentials are stored in your profile and never shared.
        </p>
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Credentials</h4>
        {field('Curtin Username (staff ID)', 'curtinUsername', 'text', 'e.g. jsmith')}
        {field('Curtin Password', 'curtinPassword', 'password')}
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">URLs</h4>
        <p className="text-xs text-gray-500">
          Only change these if Curtin changes their system URLs.
        </p>
        {field('Unit Outline URL (LITEC)', 'litecUrl')}
        {field('Blackboard URL', 'blackboardUrl')}
        {field('Campus Filter', 'campus', 'text', 'e.g. Bentley Perth Campus')}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {saved ? (
          <>
            <CheckCircle className="h-4 w-4" />
            Saved
          </>
        ) : (
          <>
            <Save className="h-4 w-4" />
            {saving ? 'Saving…' : 'Save'}
          </>
        )}
      </button>
    </div>
  );
};

export default CurtinSettings;
```

- [ ] **Step 2: Add Curtin tab to Settings.tsx**

In `frontend/src/features/settings/Settings.tsx`:

Add the import near the other settings imports:
```typescript
import CurtinSettings from './CurtinSettings';
```

Find the `tabs` array (around line 157) and add a new entry. Import `GraduationCap` from `lucide-react` (or use `Building2` if already imported):
```typescript
import { ..., Building2 } from 'lucide-react';
```

Add to `tabs`:
```typescript
{ id: 'curtin', label: 'Curtin', icon: Building2 },
```

Find the block of `{activeTab === '...' && ...}` conditionals and add:
```typescript
{activeTab === 'curtin' && <CurtinSettings />}
```

- [ ] **Step 3: Type-check and lint**

```bash
cd frontend
npm run type-check && npm run lint
```

Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/settings/CurtinSettings.tsx frontend/src/features/settings/Settings.tsx
git commit -m "feat(curtin): add CurtinSettings component and Settings tab"
```

---

## Task 8: CurtinImport page

**Files:**
- Create: `frontend/src/features/import/CurtinImport.tsx`

The outline section downloads the PDF and runs it through the same `parseOutline` + `OutlineReviewForm` flow that `OutlineImport` uses — no modifications to existing components needed.

The course section downloads the archive, stores the resulting `File` in React Router state, and navigates to `/import/package`. PackageImport will be modified in Task 9 to accept this pre-seeded file.

- [ ] **Step 1: Create the component**

Create `frontend/src/features/import/CurtinImport.tsx`:

```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Package,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  RefreshCw,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { OutlineReviewForm } from './OutlineReviewForm';
import { applyOutline, parseOutline } from '../../services/outlineImportApi';
import type { OutlineApplyRequest, OutlineParseResponse } from '../../services/outlineImportApi';
import * as curtinApi from '../../services/curtinApi';
import type { CurtinJobResponse } from '../../services/curtinApi';

type OutlinePhase = 'idle' | 'downloading' | 'review' | 'applying' | 'done' | 'error';
type CoursePhase = 'idle' | 'triggering' | 'triggered' | 'downloading' | 'error';

const CurtinImport = () => {
  const navigate = useNavigate();

  // ── Outline state ─────────────────────────────────────────────────────────
  const [unitCode, setUnitCode] = useState('');
  const [outlinePhase, setOutlinePhase] = useState<OutlinePhase>('idle');
  const [outlineError, setOutlineError] = useState<string | null>(null);
  const [parseResult, setParseResult] = useState<OutlineParseResponse | null>(null);

  const handleDownloadOutline = async () => {
    if (!unitCode.trim()) return;
    setOutlinePhase('downloading');
    setOutlineError(null);
    try {
      const { filename, data } = await curtinApi.downloadOutline(unitCode.trim().toUpperCase());
      const file = new File([data], filename, { type: 'application/pdf' });
      const result = await parseOutline(file, 'auto');
      setParseResult(result);
      setOutlinePhase('review');
    } catch (e: unknown) {
      const msg =
        e instanceof Error
          ? e.message
          : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            'Download failed';
      setOutlineError(msg);
      setOutlinePhase('error');
    }
  };

  const handleApplyOutline = async (request: OutlineApplyRequest) => {
    setOutlinePhase('applying');
    try {
      const result = await applyOutline(request);
      setOutlinePhase('done');
      navigate(`/units/${result.unitId}`);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to create unit';
      setOutlineError(msg);
      setOutlinePhase('review');
    }
  };

  // ── Course archive state ──────────────────────────────────────────────────
  const [courseName, setCourseName] = useState('');
  const [coursePhase, setCoursePhase] = useState<CoursePhase>('idle');
  const [courseError, setCourseError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<CurtinJobResponse[]>([]);
  const [downloadingJobId, setDownloadingJobId] = useState<string | null>(null);

  const handleTriggerBuild = async () => {
    if (!courseName.trim()) return;
    setCoursePhase('triggering');
    setCourseError(null);
    try {
      const job = await curtinApi.triggerCourseBuild(courseName.trim());
      setJobs(prev => [job, ...prev]);
      setCoursePhase('triggered');
      toast.success('Export triggered! Come back in 15-30 minutes to download.');
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to trigger export';
      setCourseError(msg);
      setCoursePhase('error');
    }
  };

  const handleLoadJobs = async () => {
    try {
      const fetched = await curtinApi.listCourseJobs();
      setJobs(fetched);
    } catch {
      toast.error('Could not load jobs');
    }
  };

  const handleDownloadArchive = async (job: CurtinJobResponse) => {
    setDownloadingJobId(job.id);
    setCourseError(null);
    try {
      const { filename, data } = await curtinApi.downloadCourseArchive(job.id);
      const file = new File([data], filename, { type: 'application/zip' });
      navigate('/import/package', { state: { curtinFile: file } });
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        toast.error('Archive not ready yet — Blackboard is still building it. Check back in a few minutes.');
      } else {
        const msg =
          (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Download failed';
        setCourseError(msg);
      }
    } finally {
      setDownloadingJobId(null);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (outlinePhase === 'review' && parseResult) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <OutlineReviewForm
          parseResult={parseResult}
          onApply={handleApplyOutline}
          onBack={() => { setOutlinePhase('idle'); setParseResult(null); }}
        />
        {outlinePhase === 'applying' && (
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Creating unit…
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Curtin Import</h1>
        <p className="mt-1 text-sm text-gray-500">
          Download content directly from Curtin systems. Configure credentials in{' '}
          <a href="/settings" className="text-blue-600 hover:underline">Settings → Curtin</a>.
        </p>
      </div>

      {/* ── Unit Outline ────────────────────────────────────────────────── */}
      <section className="rounded-lg border border-gray-200 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <FileText className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Unit Outline</h2>
        </div>
        <p className="text-sm text-gray-600">
          Downloads the latest PDF outline for a unit code from LITEC, then opens it in the outline
          review flow so you can import its content into a new unit.
        </p>

        <div className="flex gap-3">
          <input
            type="text"
            value={unitCode}
            onChange={e => setUnitCode(e.target.value.toUpperCase())}
            placeholder="e.g. COMP1000"
            maxLength={10}
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm uppercase focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyDown={e => { if (e.key === 'Enter') void handleDownloadOutline(); }}
          />
          <button
            onClick={() => void handleDownloadOutline()}
            disabled={!unitCode.trim() || outlinePhase === 'downloading'}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {outlinePhase === 'downloading' ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Downloading…</>
            ) : (
              <><Download className="h-4 w-4" /> Download & Import</>
            )}
          </button>
        </div>

        {outlinePhase === 'error' && outlineError && (
          <div className="flex items-start gap-2 text-sm text-red-600">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <span>{outlineError}</span>
          </div>
        )}
      </section>

      {/* ── Course Archive ───────────────────────────────────────────────── */}
      <section className="rounded-lg border border-gray-200 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Package className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Course Archive</h2>
        </div>
        <p className="text-sm text-gray-600">
          Triggers a Blackboard Common Cartridge export. Blackboard takes <strong>15-30 minutes</strong>{' '}
          to build the archive — come back after that and click Download.
        </p>

        <div className="flex gap-3">
          <input
            type="text"
            value={courseName}
            onChange={e => setCourseName(e.target.value)}
            placeholder="Course name or code, e.g. COMP1000"
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyDown={e => { if (e.key === 'Enter') void handleTriggerBuild(); }}
          />
          <button
            onClick={() => void handleTriggerBuild()}
            disabled={!courseName.trim() || coursePhase === 'triggering'}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {coursePhase === 'triggering' ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Triggering…</>
            ) : (
              <>Trigger Export</>
            )}
          </button>
        </div>

        {coursePhase === 'error' && courseError && (
          <div className="flex items-start gap-2 text-sm text-red-600">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <span>{courseError}</span>
          </div>
        )}

        {/* Jobs list */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Pending exports</span>
            <button
              onClick={() => void handleLoadJobs()}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              <RefreshCw className="h-3 w-3" /> Refresh
            </button>
          </div>

          {jobs.length === 0 ? (
            <p className="text-sm text-gray-400 italic">
              No exports yet. Trigger one above, then come back to download.
            </p>
          ) : (
            <ul className="divide-y divide-gray-100 rounded-md border border-gray-200">
              {jobs.map(job => (
                <li key={job.id} className="flex items-center justify-between px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-gray-900 truncate max-w-xs">{job.courseName}</p>
                    <p className="text-xs text-gray-500">
                      Triggered {new Date(job.triggeredAt).toLocaleString()}
                    </p>
                    {job.status === 'failed' && job.errorMessage && (
                      <p className="text-xs text-red-500 mt-0.5">{job.errorMessage}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    {job.status === 'downloaded' && (
                      <CheckCircle2 className="h-4 w-4 text-green-500" title="Downloaded" />
                    )}
                    {job.status === 'triggered' && (
                      <button
                        onClick={() => void handleDownloadArchive(job)}
                        disabled={downloadingJobId === job.id}
                        className="flex items-center gap-1 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        {downloadingJobId === job.id ? (
                          <><Loader2 className="h-3 w-3 animate-spin" /> Downloading…</>
                        ) : (
                          <><Download className="h-3 w-3" /> Download</>
                        )}
                      </button>
                    )}
                    {job.status === 'failed' && (
                      <Clock className="h-4 w-4 text-red-400" title="Failed" />
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
};

export default CurtinImport;
```

- [ ] **Step 2: Type-check and lint**

```bash
cd frontend
npm run type-check && npm run lint
```

Expected: 0 errors. If Prettier complains, run `npm run format` then recheck.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/import/CurtinImport.tsx
git commit -m "feat(curtin): add CurtinImport page"
```

---

## Task 9: Wire CurtinImport into App + modify PackageImport to accept pre-seeded file

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/features/import/PackageImport.tsx`

- [ ] **Step 1: Add the route in App.tsx**

In `frontend/src/App.tsx`, add the import near the other import-feature imports:

```typescript
import CurtinImport from './features/import/CurtinImport';
```

Find the block with `/import/package` and `/import/outline` routes (around line 176) and add:

```typescript
<Route path='/import/curtin' element={<CurtinImport />} />
```

- [ ] **Step 2: Modify PackageImport to accept a pre-seeded file from router state**

In `frontend/src/features/import/PackageImport.tsx`, import `useLocation`:

```typescript
import { useNavigate, useLocation } from 'react-router-dom';
```

Find the component definition (around line 122) and add a `useLocation` call and a `useEffect` that seeds the file if one was passed via router state. Insert immediately after the existing `useState`/`useNavigate` declarations:

```typescript
const location = useLocation();
```

Find the existing `const [file, setFile] = useState<File | null>(null);` line (or similar) and add a `useEffect` after the state declarations:

```typescript
useEffect(() => {
  const state = location.state as { curtinFile?: File } | null;
  if (state?.curtinFile) {
    setFile(state.curtinFile);
    // Clear state so browser-back doesn't re-seed
    window.history.replaceState({}, '');
  }
}, []); // eslint-disable-line react-hooks/exhaustive-deps
```

This causes PackageImport to behave as if the user uploaded the file — the existing upload phase will immediately have the file set, so when the user clicks "Analyze" (or if the component auto-analyzes), it will use the Curtin-downloaded archive.

**Note:** Look at how `file` state is used in PackageImport. If it auto-starts analysis when `file` is set, this will seamlessly jump to the preview phase. If the user needs to click "Analyze", they'll see the filename already filled in. Either way, no further changes to PackageImport are needed.

- [ ] **Step 3: Type-check and lint**

```bash
cd frontend
npm run type-check && npm run lint
```

Expected: 0 errors

- [ ] **Step 4: Run backend tests one final time**

```bash
cd backend
.venv/bin/pytest --tb=short -q
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/features/import/PackageImport.tsx
git commit -m "feat(curtin): register /import/curtin route, wire pre-seeded file into PackageImport"
```

---

## Self-Review

**Spec coverage check:**
- ✅ Both packages installed from PyPI (Task 1)
- ✅ Configurable LITEC URL, Blackboard URL, campus filter stored per-user (Tasks 3, 7)
- ✅ Graceful failure: credentials missing → 400, Playwright error → 422, not ready → 409 (Tasks 4, 5)
- ✅ Latest version only: `outline-dl` auto-selects latest by default, `interactive=False` enforces it (Task 4)
- ✅ Settings in app settings page (Task 7)
- ✅ Import workflow surface: dedicated `/import/curtin` page (Tasks 8, 9)
- ✅ Outline PDF feeds into existing `parseOutline`/`OutlineReviewForm` flow (Task 8)
- ✅ Course archive feeds into existing `PackageImport` flow (Tasks 8, 9)
- ✅ 15-30 min async wait handled: trigger returns immediately, download retried by user (Tasks 5, 8)

**No placeholders present.** All code is complete.

**Type consistency:** `CurtinSettings` schema field names match between backend (`curtin_username`) and frontend camelCase (`curtinUsername`). `CurtinJobResponse` fields match model attributes. `curtinFile` key in router state used consistently in both CurtinImport and PackageImport.
