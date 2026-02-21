"""
Repository for plugin configuration persistence.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.models.plugin_configuration import PluginConfiguration


def get_all(db: Session) -> list[PluginConfiguration]:
    """Return every persisted plugin configuration."""
    return list(db.query(PluginConfiguration).all())


def get_by_name(db: Session, name: str) -> PluginConfiguration | None:
    """Look up a single plugin config by its unique name."""
    return (
        db.query(PluginConfiguration)
        .filter(PluginConfiguration.name == name)
        .first()
    )


def upsert(
    db: Session,
    name: str,
    enabled: bool,
    priority: int,
    config: dict[str, Any] | None = None,
) -> PluginConfiguration:
    """Create or update a plugin configuration row."""
    existing = get_by_name(db, name)
    if existing:
        existing.enabled = enabled
        existing.priority = priority
        existing.config = config
    else:
        existing = PluginConfiguration(
            name=name,
            enabled=enabled,
            priority=priority,
            config=config,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing
