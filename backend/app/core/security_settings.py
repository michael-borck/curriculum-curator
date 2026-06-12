"""
Runtime security settings, configured by admins via /admin/settings.

Values are persisted in SystemConfig under security.* keys; anything unset
falls back to the defaults below (which match the historic hardcoded
behavior). Enforcement points (password validation, lockout, session
timeout, registration/whitelist toggles) and the admin settings endpoints
both read through get_security_settings() so the admin UI always shows
the values actually in force.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig


@dataclass(frozen=True)
class SecuritySettings:
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    session_timeout_minutes: int = 30
    enable_user_registration: bool = True
    enable_email_whitelist: bool = True


SETTINGS_CONFIG_KEYS: dict[str, str] = {
    "password_min_length": "security.password_min_length",
    "password_require_uppercase": "security.password_require_uppercase",
    "password_require_lowercase": "security.password_require_lowercase",
    "password_require_numbers": "security.password_require_numbers",
    "password_require_special": "security.password_require_special",
    "max_login_attempts": "security.max_login_attempts",
    "lockout_duration_minutes": "security.lockout_duration",
    "session_timeout_minutes": "security.session_timeout",
    "enable_user_registration": "security.enable_user_registration",
    "enable_email_whitelist": "security.enable_email_whitelist",
}


# Values come from a JSON column; guard against rows edited to the wrong
# type via the generic /admin/config endpoints.
def _int_setting(stored: dict[str, Any], field: str, default: int) -> int:
    value = stored.get(SETTINGS_CONFIG_KEYS[field], default)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _bool_setting(stored: dict[str, Any], field: str, default: bool) -> bool:
    value = stored.get(SETTINGS_CONFIG_KEYS[field], default)
    if isinstance(value, bool):
        return value
    return default


def get_security_settings(db: Session) -> SecuritySettings:
    """Load effective security settings, falling back to defaults per field."""
    rows = (
        db.query(SystemConfig)
        .filter(SystemConfig.key.in_(list(SETTINGS_CONFIG_KEYS.values())))
        .all()
    )
    stored: dict[str, Any] = {row.key: row.value for row in rows}
    d = SecuritySettings()
    return SecuritySettings(
        password_min_length=_int_setting(
            stored, "password_min_length", d.password_min_length
        ),
        password_require_uppercase=_bool_setting(
            stored, "password_require_uppercase", d.password_require_uppercase
        ),
        password_require_lowercase=_bool_setting(
            stored, "password_require_lowercase", d.password_require_lowercase
        ),
        password_require_numbers=_bool_setting(
            stored, "password_require_numbers", d.password_require_numbers
        ),
        password_require_special=_bool_setting(
            stored, "password_require_special", d.password_require_special
        ),
        max_login_attempts=_int_setting(
            stored, "max_login_attempts", d.max_login_attempts
        ),
        lockout_duration_minutes=_int_setting(
            stored, "lockout_duration_minutes", d.lockout_duration_minutes
        ),
        session_timeout_minutes=_int_setting(
            stored, "session_timeout_minutes", d.session_timeout_minutes
        ),
        enable_user_registration=_bool_setting(
            stored, "enable_user_registration", d.enable_user_registration
        ),
        enable_email_whitelist=_bool_setting(
            stored, "enable_email_whitelist", d.enable_email_whitelist
        ),
    )
