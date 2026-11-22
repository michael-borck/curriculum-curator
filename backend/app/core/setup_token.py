"""One-time setup token that gates creation of the first admin account.

A fresh deployment has no users and no admin to configure the email
whitelist. Rather than letting any anonymous caller become the first
(admin) user, the first registration must present a setup token:

* ``SETUP_TOKEN`` from the environment when the operator sets it, or
* a token generated on demand and written to a 0600 file beside the
  database, which the operator can read on the server.

The token stops mattering once the first user exists.
"""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

_TOKEN_FILE_NAME = "setup_token"


def _token_path() -> Path:
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        db_path = Path(url.removeprefix("sqlite:///")).expanduser()
        parent = db_path.parent
    else:
        parent = Path("data")
    return parent / _TOKEN_FILE_NAME


def _read_or_create_file_token() -> str:
    path = _token_path()
    try:
        if path.exists():
            existing = path.read_text(encoding="utf-8").strip()
            if existing:
                return existing
        path.parent.mkdir(parents=True, exist_ok=True)
        token = secrets.token_urlsafe(32)
        # Create with 0600 from the start so it is never world-readable.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token + "\n")
        logger.warning(
            "First-admin setup token written to %s — read it on the server "
            "and use it to create the first account.",
            path,
        )
        return token
    except OSError:
        logger.exception("Could not persist setup token to %s", path)
        return ""


def expected_setup_token() -> str:
    """Return the token the first registrant must present ('' if unknown)."""
    if settings.SETUP_TOKEN:
        return settings.SETUP_TOKEN
    return _read_or_create_file_token()


def verify_setup_token(provided: str | None) -> bool:
    expected = expected_setup_token()
    if not expected or not provided:
        return False
    return secrets.compare_digest(expected, provided)


def rotate_setup_token() -> None:
    """Invalidate the file token once the first admin has been created."""
    if settings.SETUP_TOKEN:
        return
    path = _token_path()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.exception("Could not remove setup token file %s", path)
