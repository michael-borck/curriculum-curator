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
from app.services.curtin_service import CurtinServiceError, NotReadyError

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
    cfg = _load_settings(current_user)
    # Never return the stored password — the frontend treats empty string as "no change"
    cfg.curtin_password = ""
    return cfg


@router.put("/settings", response_model=CurtinSettings)
def update_settings(
    data: CurtinSettings,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> CurtinSettings:
    prefs = dict(current_user.teaching_preferences or {})
    existing = prefs.get("curtin", {}) if isinstance(prefs.get("curtin"), dict) else {}
    payload = data.model_dump()
    # Preserve stored password when client sends empty string (display-only clear)
    if not payload.get("curtin_password"):
        payload["curtin_password"] = existing.get("curtin_password", "")
    prefs["curtin"] = payload
    current_user.teaching_preferences = prefs
    db.commit()
    # Return with password masked
    data.curtin_password = ""
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
    except NotReadyError as exc:
        raise HTTPException(
            status_code=409,
            detail="Archive not ready yet — Blackboard is still building it. Wait 15-30 minutes and try again.",
        ) from exc
    except CurtinServiceError as exc:
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
