"""
Shared helpers for managing export template metadata and file storage.

Used by both export_templates routes (Settings → Export tab) and
import_content routes (extract template from imported PPTX).
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


def user_templates_dir(user_id: str) -> Path:
    """Return the on-disk directory for a user's export templates."""
    base = Path(settings.TEMPLATE_UPLOAD_DIR)
    return base / user_id


def get_export_templates(prefs: dict[str, Any] | None) -> dict[str, Any]:
    """Extract the export_templates section from teaching_preferences."""
    if not prefs:
        return {"templates": [], "defaults": {"pptx": None, "docx": None}}
    return prefs.get(
        "export_templates",
        {"templates": [], "defaults": {"pptx": None, "docx": None}},
    )


def save_export_templates(
    db: Session, user_id: str, prefs: dict[str, Any] | None, et: dict[str, Any]
) -> None:
    """Persist the export_templates section back into teaching_preferences."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    new_prefs = dict(prefs) if prefs else {}
    new_prefs["export_templates"] = et
    user.teaching_preferences = new_prefs
    user.updated_at = datetime.now(tz=UTC)
    db.commit()
