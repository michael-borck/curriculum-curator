"""TOTP (RFC 6238) helpers for optional multi-factor authentication."""

from __future__ import annotations

import secrets
import time
from typing import TYPE_CHECKING

from pyotp import random_base32
from pyotp.totp import TOTP

from app.core.security import hash_one_time_code

if TYPE_CHECKING:
    from app.core.config import Settings

_RECOVERY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_RECOVERY_CODES = 10
_STEP_SECONDS = 30


def generate_secret() -> str:
    return random_base32()


def provisioning_uri(secret: str, email: str, settings: Settings) -> str:
    return TOTP(secret).provisioning_uri(
        name=email, issuer_name=settings.APP_NAME
    )


def current_counter() -> int:
    return int(time.time()) // _STEP_SECONDS


def verify_totp(secret: str, code: str, last_counter: int) -> tuple[bool, int]:
    """Verify a 6-digit code and reject replays of an already-used window."""
    counter = current_counter()
    if counter <= last_counter:
        return False, last_counter
    if not TOTP(secret).verify(code.strip(), valid_window=1):
        return False, last_counter
    return True, counter


def generate_recovery_codes(count: int = _RECOVERY_CODES) -> list[str]:
    codes: list[str] = []
    for _ in range(count):
        raw = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(10))
        codes.append(f"{raw[:5]}-{raw[5:]}")
    return codes


def hash_recovery_codes(codes: list[str]) -> list[str]:
    return [hash_one_time_code(code) for code in codes]


def consume_recovery_code(
    stored_hashes: list[str] | None, code: str
) -> tuple[bool, list[str]]:
    """Return whether the code matched and the remaining hashes."""
    hashes = list(stored_hashes or [])
    candidate = hash_one_time_code(code)
    if candidate not in hashes:
        return False, hashes
    hashes.remove(candidate)
    return True, hashes
