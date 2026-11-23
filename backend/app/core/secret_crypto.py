"""Encryption at rest for stored secrets (LLM API keys, bearer tokens).

Values are Fernet-encrypted (AES-128-CBC + HMAC) and prefixed with
``enc:v1:`` so legacy plaintext rows remain readable until rewritten.
The key comes from ENCRYPTION_KEY when set, otherwise it is derived from
SECRET_KEY — rotating either invalidates previously encrypted values,
which then fail closed (decrypt returns None) rather than leaking.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)

_PREFIX = "enc:v1:"


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    raw = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    try:
        return Fernet(raw.encode())
    except Exception:
        digest = hashlib.sha256(f"curriculum-curator-secret-v1:{raw}".encode()).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def is_encrypted(value: str | None) -> bool:
    return bool(value) and value.startswith(_PREFIX)


def encrypt_secret(value: str | None) -> str | None:
    """Encrypt a secret for storage; None/empty stay None."""
    if not value:
        return None
    if is_encrypted(value):
        return value
    token = _fernet().encrypt(value.encode()).decode()
    return f"{_PREFIX}{token}"


def decrypt_secret(value: str | None) -> str | None:
    """Decrypt a stored secret. Legacy plaintext passes through unchanged."""
    if not value:
        return None
    if not is_encrypted(value):
        return value
    try:
        return _fernet().decrypt(value[len(_PREFIX) :].encode()).decode()
    except InvalidToken:
        logger.warning("Stored secret could not be decrypted (key rotated?)")
        return None
