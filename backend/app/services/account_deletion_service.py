"""Hard-delete a user's account and owned content.

Single-owner model: delete every unit the user owns (DB rows, git repo and
templates), remove user-scoped rows, null or reassign audit references on
content that belongs to someone else, and anonymise security logs.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select, update

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base
from app.models.user import User

logger = logging.getLogger(__name__)

_USER_OWNED = (
    ("email_verifications", "user_id"),
    ("password_resets", "user_id"),
    ("login_tokens", "user_id"),
    ("webauthn_credentials", "user_id"),
    ("research_sources", "user_id"),
    ("llm_configurations", "user_id"),
    ("token_usage_logs", "user_id"),
    ("curtin_export_jobs", "user_id"),
    ("prompt_templates", "owner_id"),
)

_AUDIT_NULLS = (
    ("units", "updated_by_id"),
    ("unit_outlines", "updated_by_id"),
    ("unit_outlines", "approved_by_id"),
    ("system_config", "updated_by_id"),
    ("analytics_snapshots", "created_by_id"),
)


def _table(name: str) -> Any:
    return Base.metadata.tables[name]


def _ids(db: Session, table_name: str, column: str, value: str) -> list[str]:
    table = _table(table_name)
    return [
        str(row[0])
        for row in db.execute(select(table.c.id).where(table.c[column] == value))
    ]


def _delete_unit_subtree(db: Session, unit_ids: list[str]) -> None:
    """Delete every row that descends from the units, children first."""
    if not unit_ids:
        return
    deleted: dict[str, set[str]] = {"units": set(unit_ids)}
    tables = [t for t in Base.metadata.sorted_tables if t.name != "units"]
    changed = True
    while changed:
        changed = False
        for table in tables:
            for fk in table.foreign_keys:
                parent = fk.column.table.name
                parent_ids = deleted.get(parent)
                if not parent_ids:
                    continue
                column = table.c.get(fk.parent.name)
                if column is None:
                    continue
                id_column = table.c.get("id")
                if id_column is None:
                    # Association table with a composite key: delete by FK.
                    exists = db.execute(
                        select(column).where(column.in_(list(parent_ids))).limit(1)
                    ).first()
                    if exists:
                        db.execute(delete(table).where(column.in_(list(parent_ids))))
                        changed = True
                    continue
                ids = [
                    str(row[0])
                    for row in db.execute(
                        select(id_column).where(column.in_(list(parent_ids)))
                    )
                ]
                if not ids:
                    continue
                db.execute(delete(table).where(id_column.in_(ids)))
                deleted.setdefault(table.name, set()).update(ids)
                changed = True
    db.execute(delete(_table("units")).where(_table("units").c.id.in_(unit_ids)))


def _delete_user_owned_rows(db: Session, user_id: str, email: str) -> None:
    # Chat messages depend on sessions.
    session_ids = _ids(db, "chat_sessions", "user_id", user_id)
    if session_ids:
        db.execute(
            delete(_table("chat_messages")).where(
                _table("chat_messages").c.session_id.in_(session_ids)
            )
        )
        db.execute(
            delete(_table("chat_sessions")).where(
                _table("chat_sessions").c.id.in_(session_ids)
            )
        )

    # CLO hierarchy.
    clo_set_ids = _ids(db, "clo_sets", "user_id", user_id)
    if clo_set_ids:
        item_ids = _ids_in(db, "clo_items", "clo_set_id", clo_set_ids)
        if item_ids:
            db.execute(
                delete(_table("ulo_clo_item_mappings")).where(
                    _table("ulo_clo_item_mappings").c.clo_item_id.in_(item_ids)
                )
            )
        db.execute(
            delete(_table("unit_clo_set_assignments")).where(
                _table("unit_clo_set_assignments").c.clo_set_id.in_(clo_set_ids)
            )
        )
        db.execute(
            delete(_table("clo_items")).where(
                _table("clo_items").c.clo_set_id.in_(clo_set_ids)
            )
        )
        db.execute(
            delete(_table("clo_sets")).where(_table("clo_sets").c.id.in_(clo_set_ids))
        )

    for table_name, column in _USER_OWNED:
        table = _table(table_name)
        db.execute(delete(table).where(table.c[column] == user_id))

    db.execute(
        delete(_table("login_attempts")).where(
            _table("login_attempts").c.email == email.lower()
        )
    )

    # Keep audit history but remove identity and free-text details.
    logs = _table("security_logs")
    db.execute(
        update(logs)
        .where(logs.c.user_id == user_id)
        .values(user_id=None, user_email=None, details=None)
    )


def _ids_in(db: Session, table_name: str, column: str, values: list[str]) -> list[str]:
    table = _table(table_name)
    return [
        str(row[0])
        for row in db.execute(select(table.c.id).where(table.c[column].in_(values)))
    ]


def _reassign_audit_fields(db: Session, user_id: str) -> None:
    units = _table("units")
    db.execute(
        update(units)
        .where(units.c.created_by_id == user_id)
        .values(created_by_id=units.c.owner_id)
    )
    for table_name in (
        "unit_outlines",
        "unit_learning_outcomes",
        "weekly_topics",
        "assessment_plans",
    ):
        table = _table(table_name)
        owner = (
            select(units.c.owner_id)
            .where(units.c.id == table.c.unit_id)
            .scalar_subquery()
        )
        db.execute(
            update(table)
            .where(
                table.c.created_by_id == user_id,
                table.c.unit_id.in_(select(units.c.id)),
            )
            .values(created_by_id=owner)
        )
    for table_name, column in _AUDIT_NULLS:
        table = _table(table_name)
        db.execute(
            update(table).where(table.c[column] == user_id).values({column: None})
        )


def _remove_files(unit_ids: list[str], user_id: str) -> None:
    try:
        from app.services.git_content_service import get_git_service  # noqa: PLC0415

        git = get_git_service()
        for unit_id in unit_ids:
            try:
                git.delete_unit_repo(unit_id)
            except Exception:
                logger.warning("Could not delete git repo for unit %s", unit_id)
    except Exception:
        logger.exception("Git cleanup failed during account deletion")

    template_dir = Path(settings.TEMPLATE_UPLOAD_DIR) / user_id
    if template_dir.exists():
        try:
            shutil.rmtree(template_dir)
        except OSError:
            logger.warning("Could not remove template directory %s", template_dir)


def delete_user_account(db: Session, user_id: str) -> list[str]:
    """Delete the user and owned content; return deleted unit ids.

    Callers are responsible for authorization and for refusing to delete the
    last administrator.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return []
    units_table = _table("units")
    unit_ids = [
        str(row[0])
        for row in db.execute(
            select(units_table.c.id).where(units_table.c.owner_id == user_id)
        )
    ]

    _delete_unit_subtree(db, unit_ids)
    _delete_user_owned_rows(db, user_id, user.email)
    _reassign_audit_fields(db, user_id)
    db.execute(delete(User).where(User.id == user_id))
    db.commit()

    _remove_files(unit_ids, user_id)
    return unit_ids
