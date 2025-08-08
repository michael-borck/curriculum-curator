"""
Login attempt model for account security and lockout tracking
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, or_

from app.core.database import Base
from app.models.user import GUID


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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # User identification (email used for login attempts)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)  # Support IPv6
    user_agent = Column(String(500), nullable=True)

    # Attempt tracking
    attempt_type = Column(String(30), nullable=False, index=True)  # LoginAttemptType enum
    failed_attempts = Column(Integer, default=0, nullable=False)
    consecutive_failures = Column(Integer, default=0, nullable=False)

    # Lockout management
    is_locked = Column(Boolean, default=False, nullable=False, index=True)
    locked_until = Column(DateTime, nullable=True, index=True)
    lockout_reason = Column(String(200), nullable=True)

    # Timing
    first_attempt = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_attempt = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<LoginAttempt(email='{self.email}', ip='{self.ip_address}', failures={self.failed_attempts}, locked={self.is_locked})>"

    @property
    def is_currently_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.is_locked or not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until

    @property
    def lockout_expires_in_minutes(self) -> int:
        """Get minutes until lockout expires"""
        if not self.is_currently_locked or not self.locked_until:
            return 0
        delta = self.locked_until - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 60))

    @property
    def time_since_last_attempt(self) -> timedelta:
        """Get time since last attempt"""
        return datetime.utcnow() - self.last_attempt

    def record_success(self):
        """Record successful login and reset failure counters"""
        self.attempt_type = LoginAttemptType.LOGIN_SUCCESS.value
        self.failed_attempts = 0
        self.consecutive_failures = 0
        self.is_locked = False
        self.locked_until = None
        self.lockout_reason = None
        self.last_attempt = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def record_failure(self, reason: str = "Invalid credentials"):
        """Record failed login attempt and apply lockout if needed"""
        self.attempt_type = LoginAttemptType.LOGIN_FAILED.value
        self.failed_attempts += 1
        self.consecutive_failures += 1
        self.last_attempt = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Apply progressive lockout based on consecutive failures
        if self.consecutive_failures >= 10:
            # 10+ failures: 24 hour lockout
            self.apply_lockout(hours=24, reason=f"Excessive login attempts: {reason}")
        elif self.consecutive_failures >= 7:
            # 7-9 failures: 4 hour lockout
            self.apply_lockout(hours=4, reason=f"Multiple failed attempts: {reason}")
        elif self.consecutive_failures >= 5:
            # 5-6 failures: 30 minute lockout
            self.apply_lockout(minutes=30, reason=f"Failed login attempts: {reason}")

    def apply_lockout(self, minutes: int = 0, hours: int = 0, reason: str | None = None):
        """Apply account lockout for specified duration"""
        lockout_duration = timedelta(minutes=minutes, hours=hours)
        self.is_locked = True
        self.locked_until = datetime.utcnow() + lockout_duration
        self.lockout_reason = reason or "Account locked due to security policy"
        self.attempt_type = LoginAttemptType.ACCOUNT_LOCKED.value
        self.updated_at = datetime.utcnow()

    def unlock_account(self, reason: str = "Manual unlock"):
        """Manually unlock account"""
        self.is_locked = False
        self.locked_until = None
        self.lockout_reason = None
        self.consecutive_failures = 0
        self.lockout_reason = f"Unlocked: {reason}"
        self.updated_at = datetime.utcnow()

    @classmethod
    def cleanup_old_attempts(cls, db_session, days_old: int = 30):
        """Clean up old login attempt records"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        return (
            db_session.query(cls)
            .filter(cls.created_at < cutoff_date)
            .filter(~cls.is_locked)  # Don't delete locked accounts
            .delete(synchronize_session=False)
        )

    @classmethod
    def get_or_create_for_email_ip(cls, db_session, email: str, ip_address: str):
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
            id=uuid.uuid4(),
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
    def is_ip_rate_limited(cls, db_session, ip_address: str, max_attempts: int = 20, window_minutes: int = 15) -> bool:
        """Check if IP address should be rate limited based on recent attempts"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        attempt_count = (
            db_session.query(cls)
            .filter(cls.ip_address == ip_address)
            .filter(cls.last_attempt >= cutoff_time)
            .count()
        )

        return attempt_count >= max_attempts

    @classmethod
    def get_recent_suspicious_activity(cls, db_session, hours: int = 24):
        """Get recent suspicious activity for monitoring"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        return (
            db_session.query(cls)
            .filter(cls.last_attempt >= cutoff_time)
            .filter(
                or_(
                    cls.consecutive_failures >= 3,
                    cls.is_locked,
                    cls.attempt_type == LoginAttemptType.SUSPICIOUS_ACTIVITY.value
                )
            )
            .order_by(cls.last_attempt.desc())
            .limit(100)
            .all()
        )

