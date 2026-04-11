"""
Security repository - database operations for security logging and login tracking

Handles login attempts, account lockouts, and security audit logs using SQLAlchemy.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt
from app.models.security_log import SecurityEventType, SecurityLog


# Login attempt tracking
def get_or_create_login_attempt(
    db: Session, email: str, ip_address: str
) -> LoginAttempt:
    """Get or create login attempt record for email/IP combination"""
    email = email.lower().strip()

    attempt = (
        db.query(LoginAttempt)
        .filter(LoginAttempt.email == email, LoginAttempt.ip_address == ip_address)
        .first()
    )

    if attempt:
        return attempt

    # Create new record
    attempt = LoginAttempt(
        id=str(uuid.uuid4()),
        email=email,
        ip_address=ip_address,
        attempt_type="login_failed",
        failed_attempts=0,
        consecutive_failures=0,
        is_locked=False,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def record_login_success(
    db: Session, email: str, ip_address: str, user_agent: str | None = None
) -> None:
    """Record successful login and reset failure count"""
    email = email.lower().strip()

    # Get or create attempt record
    attempt = get_or_create_login_attempt(db, email, ip_address)

    # Use the model's method to record success
    attempt.record_success()
    if user_agent:
        attempt.user_agent = user_agent

    db.commit()

    # Also reset other attempts from same email (different IPs)
    db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.ip_address != ip_address,
    ).update(
        {
            "failed_attempts": 0,
            "consecutive_failures": 0,
            "is_locked": False,
            "locked_until": None,
        }
    )
    db.commit()


def record_login_failure(
    db: Session,
    email: str,
    ip_address: str,
    user_agent: str | None = None,
    reason: str = "Invalid credentials",
) -> LoginAttempt:
    """Record failed login attempt and potentially lock account"""
    email = email.lower().strip()

    # Get or create attempt record
    attempt = get_or_create_login_attempt(db, email, ip_address)

    # Use the model's method to record failure (includes lockout logic)
    attempt.record_failure(reason)
    if user_agent:
        attempt.user_agent = user_agent

    db.commit()
    db.refresh(attempt)

    # Aggregate lockout: if many IPs are failing for the same email, lock all records
    total_failures = (
        db.query(func.sum(LoginAttempt.consecutive_failures))
        .filter(LoginAttempt.email == email)
        .scalar()
    ) or 0

    if total_failures >= 15 and not attempt.is_locked:
        # Lock all records for this email (distributed brute force)
        db.query(LoginAttempt).filter(
            LoginAttempt.email == email,
        ).update({
            "is_locked": True,
            "locked_until": datetime.now(UTC) + timedelta(minutes=30),
            "lockout_reason": "Account locked due to excessive failed attempts from multiple sources",
        })
        db.commit()

    return attempt


def check_account_lockout(
    db: Session, email: str, ip_address: str
) -> tuple[bool, str | None, int | None]:
    """
    Check if account/IP is locked out.
    Returns: (is_locked, lockout_reason, minutes_until_unlock)
    """
    email = email.lower().strip()
    now = datetime.now(UTC)

    # Check email-based lockout
    attempt = (
        db.query(LoginAttempt)
        .filter(LoginAttempt.email == email, LoginAttempt.is_locked == True)  # noqa: E712
        .first()
    )

    if attempt and attempt.locked_until:
        if attempt.locked_until > now:
            minutes_remaining = (
                int((attempt.locked_until - now).total_seconds() / 60) + 1
            )
            return True, attempt.lockout_reason, minutes_remaining
        # Lock expired, clear it
        attempt.unlock_account("Lockout expired")
        db.commit()

    # Check IP-based rate limiting using model method
    if LoginAttempt.is_ip_rate_limited(db, ip_address):
        return True, "IP address temporarily blocked due to excessive requests", 15

    return False, None, None


def is_ip_rate_limited(
    db: Session, ip_address: str, max_attempts: int = 20, window_minutes: int = 15
) -> bool:
    """Check if IP has exceeded rate limit"""
    return LoginAttempt.is_ip_rate_limited(db, ip_address, max_attempts, window_minutes)


# Security logging
def log_security_event(
    db: Session,
    event_type: str | SecurityEventType,
    ip_address: str | None = None,
    user_id: str | None = None,
    user_email: str | None = None,
    user_role: str | None = None,
    user_agent: str | None = None,
    request_path: str | None = None,
    request_method: str | None = None,
    description: str | None = None,
    severity: str = "info",
    success: str = "success",
    details: dict[str, Any] | None = None,
    response_time_ms: int | None = None,
) -> SecurityLog:
    """Log a security event"""
    # Convert enum to value if needed
    event_type_value = (
        event_type.value if isinstance(event_type, SecurityEventType) else event_type
    )

    log = SecurityLog(
        id=str(uuid.uuid4()),
        event_type=event_type_value,
        ip_address=ip_address or "unknown",
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method,
        event_description=description,
        severity=severity,
        success=success,
        details=details or {},
        response_time_ms=str(response_time_ms) if response_time_ms else None,
    )
    db.add(log)
    db.commit()
    return log


def get_lockout_message(
    is_locked: bool, reason: str | None, minutes_remaining: int | None
) -> str:
    """Generate user-friendly lockout status message"""
    if not is_locked:
        return ""

    if minutes_remaining and minutes_remaining > 60:
        hours = minutes_remaining // 60
        remaining_minutes = minutes_remaining % 60
        time_msg = f"{hours} hour(s)"
        if remaining_minutes > 0:
            time_msg += f" and {remaining_minutes} minute(s)"
    elif minutes_remaining:
        time_msg = f"{minutes_remaining} minute(s)"
    else:
        time_msg = "a short while"

    base_message = f"Account temporarily locked. Try again in {time_msg}."

    if reason and "excessive" in reason.lower():
        base_message += " If this persists, contact your system administrator."

    return base_message
