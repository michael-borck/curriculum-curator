"""
Login attempt model for account security and lockout tracking
"""

import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Self

from sqlalchemy import Integer, String, func, or_
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base
from app.models.common import GUID


class LoginAttemptType(str, Enum):
    """Login attempt type enumeration"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    ACCOUNT_LOCKED = "account_locked"
    PASSWORD_RESET_USED = "password_reset_used"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class LoginAttempt(Base):
    """Login attempt model for security tracking and account lockout"""

    __tablename__ = "login_attempts"

    id: Mapped[str] = mapped_column(
        GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # User identification (email used for login attempts)
    email: Mapped[str] = mapped_column(String(255), index=True)
    ip_address: Mapped[str] = mapped_column(String(45), index=True)  # Support IPv6
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Attempt tracking
    attempt_type: Mapped[str] = mapped_column(
        String(30), index=True
    )  # LoginAttemptType enum
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    # Lockout management
    is_locked: Mapped[bool] = mapped_column(default=False, index=True)
    locked_until: Mapped[datetime | None] = mapped_column(nullable=True, index=True)
    lockout_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Timing
    first_attempt: Mapped[datetime] = mapped_column(default=func.now())
    last_attempt: Mapped[datetime] = mapped_column(default=func.now())
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<LoginAttempt(email='{self.email}', ip='{self.ip_address}', failures={self.failed_attempts}, locked={self.is_locked})>"

    @property
    def is_currently_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.is_locked or not self.locked_until:
            return False
        return datetime.now(UTC) < self.locked_until

    @property
    def lockout_expires_in_minutes(self) -> int:
        """Get minutes until lockout expires"""
        if not self.is_currently_locked or not self.locked_until:
            return 0
        delta = self.locked_until - datetime.now(UTC)
        return max(0, int(delta.total_seconds() / 60))

    @property
    def time_since_last_attempt(self) -> timedelta:
        """Get time since last attempt"""
        return datetime.now(UTC) - self.last_attempt

    def record_success(self) -> None:
        """Record successful login and reset failure counters"""
        self.attempt_type = LoginAttemptType.LOGIN_SUCCESS.value
        self.failed_attempts = 0
        self.consecutive_failures = 0
        self.is_locked = False
        self.locked_until = None
        self.lockout_reason = None
        self.last_attempt = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def record_failure(self, reason: str = "Invalid credentials") -> None:
        """Record failed login attempt and apply lockout if needed"""
        self.attempt_type = LoginAttemptType.LOGIN_FAILED.value
        self.failed_attempts = int(self.failed_attempts) + 1
        self.consecutive_failures = int(self.consecutive_failures) + 1
        self.last_attempt = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

        # Apply progressive lockout based on consecutive failures
        consecutive = int(self.consecutive_failures)
        if consecutive >= 10:
            # 10+ failures: 24 hour lockout
            self.apply_lockout(hours=24, reason=f"Excessive login attempts: {reason}")
        elif consecutive >= 7:
            # 7-9 failures: 4 hour lockout
            self.apply_lockout(hours=4, reason=f"Multiple failed attempts: {reason}")
        elif consecutive >= 5:
            # 5-6 failures: 30 minute lockout
            self.apply_lockout(minutes=30, reason=f"Failed login attempts: {reason}")

    def apply_lockout(
        self, minutes: int = 0, hours: int = 0, reason: str | None = None
    ) -> None:
        """Apply account lockout for specified duration"""
        lockout_duration = timedelta(minutes=minutes, hours=hours)
        self.is_locked = True
        self.locked_until = datetime.now(UTC) + lockout_duration
        self.lockout_reason = reason or "Account locked due to security policy"
        self.attempt_type = LoginAttemptType.ACCOUNT_LOCKED.value
        self.updated_at = datetime.now(UTC)

    def unlock_account(self, reason: str = "Manual unlock") -> None:
        """Manually unlock account"""
        self.is_locked = False
        self.locked_until = None
        self.consecutive_failures = 0
        self.lockout_reason = f"Unlocked: {reason}"
        self.updated_at = datetime.now(UTC)

    @classmethod
    def cleanup_old_attempts(cls, db_session: Session, days_old: int = 30) -> int:
        """Clean up old login attempt records"""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)
        return (
            db_session.query(cls)
            .filter(cls.created_at < cutoff_date)
            .filter(cls.is_locked == False)  # noqa: E712 - SQLAlchemy syntax
            .delete(synchronize_session=False)
        )

    @classmethod
    def get_or_create_for_email_ip(
        cls, db_session: Session, email: str, ip_address: str
    ) -> "LoginAttempt":
        """Get or create login attempt record for email/IP combination"""
        # First try to find existing record
        attempt = (
            db_session.query(cls)
            .filter(cls.email == email.lower())
            .filter(cls.ip_address == ip_address)
            .first()
        )

        if attempt:
            return attempt

        # Create new record
        attempt = cls(
            id=str(uuid.uuid4()),
            email=email.lower(),
            ip_address=ip_address,
            attempt_type=LoginAttemptType.LOGIN_FAILED.value,
            failed_attempts=0,
            consecutive_failures=0,
            is_locked=False,
        )

        db_session.add(attempt)
        return attempt

    @classmethod
    def is_ip_rate_limited(
        cls,
        db_session: Session,
        ip_address: str,
        max_attempts: int = 20,
        window_minutes: int = 15,
    ) -> bool:
        """Check if IP address should be rate limited based on recent attempts"""
        cutoff_time = datetime.now(UTC) - timedelta(minutes=window_minutes)

        attempt_count = (
            db_session.query(cls)
            .filter(cls.ip_address == ip_address)
            .filter(cls.last_attempt >= cutoff_time)
            .count()
        )

        return attempt_count >= max_attempts

    @classmethod
    def get_recent_suspicious_activity(
        cls, db_session: Session, hours: int = 24
    ) -> list[Self]:
        """Get recent suspicious activity for monitoring"""
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        return (
            db_session.query(cls)
            .filter(cls.last_attempt >= cutoff_time)
            .filter(
                or_(
                    cls.consecutive_failures >= 3,
                    cls.is_locked == True,  # noqa: E712 - SQLAlchemy syntax
                    cls.attempt_type == LoginAttemptType.SUSPICIOUS_ACTIVITY.value,
                )
            )
            .order_by(cls.last_attempt.desc())
            .limit(100)
            .all()
        )
