"""
Security utilities for authentication protection
"""

from datetime import datetime, timedelta

from fastapi import Request
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt, LoginAttemptType
from app.models.user import User


class SecurityManager:
    """Security manager for handling authentication security"""

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get client IP address from request, handling proxies"""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header (some proxies use this)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    @staticmethod
    def get_user_agent(request: Request) -> str:
        """Get user agent from request"""
        return request.headers.get("User-Agent", "Unknown")[:500]  # Limit length

    @staticmethod
    def check_account_lockout(
        db: Session, email: str, ip_address: str
    ) -> tuple[bool, str | None, int | None]:
        """
        Check if account/IP is locked out
        Returns: (is_locked, lockout_reason, minutes_until_unlock)
        """
        # Check email-based lockout
        email_attempt = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.email == email.lower())
            .filter(LoginAttempt.is_locked)
            .first()
        )

        if email_attempt and email_attempt.is_currently_locked:
            return (
                True,
                f"Account locked: {email_attempt.lockout_reason}",
                email_attempt.lockout_expires_in_minutes,
            )

        # Check IP-based rate limiting (20 attempts in 15 minutes)
        if LoginAttempt.is_ip_rate_limited(db, ip_address, max_attempts=20, window_minutes=15):
            return (
                True,
                "IP address temporarily blocked due to excessive requests",
                15,  # Standard IP lockout duration
            )

        return False, None, None

    @staticmethod
    def record_login_attempt(
        db: Session,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        user: User | None = None,  # noqa: ARG004
        failure_reason: str = "Invalid credentials",
    ) -> LoginAttempt:
        """Record login attempt and handle lockouts"""
        # Get or create attempt record for this email/IP
        attempt = LoginAttempt.get_or_create_for_email_ip(db, email, ip_address)

        # Update user agent if provided
        if user_agent:
            attempt.user_agent = user_agent

        if success:
            # Record successful login
            attempt.record_success()

            # Also reset any other attempts from this email (different IPs)
            other_attempts = (
                db.query(LoginAttempt)
                .filter(LoginAttempt.email == email.lower())
                .filter(LoginAttempt.ip_address != ip_address)
                .all()
            )

            for other_attempt in other_attempts:
                other_attempt.record_success()
        else:
            # Record failed attempt
            attempt.record_failure(failure_reason)

        db.commit()
        return attempt

    @staticmethod
    def is_suspicious_activity(
        db: Session, email: str, ip_address: str, user_agent: str  # noqa: ARG004
    ) -> tuple[bool, str]:
        """
        Detect suspicious login activity
        Returns: (is_suspicious, reason)
        """
        # Check for rapid attempts from same IP
        recent_attempts = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.ip_address == ip_address)
            .filter(
                LoginAttempt.last_attempt >= datetime.utcnow() - timedelta(minutes=5)
            )
            .count()
        )

        if recent_attempts >= 10:
            return True, "Too many rapid attempts from same IP"

        # Check for attempts on multiple accounts from same IP
        unique_emails = (
            db.query(LoginAttempt.email)
            .filter(LoginAttempt.ip_address == ip_address)
            .filter(
                LoginAttempt.last_attempt >= datetime.utcnow() - timedelta(hours=1)
            )
            .distinct()
            .count()
        )

        if unique_emails >= 5:
            return True, "Multiple account enumeration from same IP"

        # Check for unusual user agent patterns
        if user_agent:
            # Very basic bot detection
            bot_indicators = ["bot", "crawler", "spider", "scraper", "curl", "wget"]
            user_agent_lower = user_agent.lower()

            if any(indicator in user_agent_lower for indicator in bot_indicators):
                return True, "Automated tool detected"

        return False, ""

    @staticmethod
    def cleanup_old_records(db: Session, days_old: int = 30) -> int:
        """Clean up old login attempt records"""
        deleted_count = LoginAttempt.cleanup_old_attempts(db, days_old)
        db.commit()
        return deleted_count

    @staticmethod
    def get_lockout_status_message(
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

    @staticmethod
    def manual_unlock_account(db: Session, email: str, admin_reason: str = "Admin unlock") -> bool:
        """Manually unlock an account (admin function)"""
        attempts = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.email == email.lower())
            .filter(LoginAttempt.is_locked)
            .all()
        )

        if not attempts:
            return False

        for attempt in attempts:
            attempt.unlock_account(admin_reason)

        db.commit()
        return True

    @staticmethod
    def get_security_stats(db: Session, hours: int = 24) -> dict:
        """Get security statistics for monitoring"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        total_attempts = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.last_attempt >= cutoff_time)
            .count()
        )

        failed_attempts = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.last_attempt >= cutoff_time)
            .filter(LoginAttempt.attempt_type == LoginAttemptType.LOGIN_FAILED.value)
            .count()
        )

        locked_accounts = (
            db.query(LoginAttempt)
            .filter(
                and_(
                    LoginAttempt.is_locked,
                    LoginAttempt.locked_until.is_not(None),
                    LoginAttempt.locked_until > datetime.utcnow()  # type: ignore[operator]
                )
            )
            .count()
        )

        unique_ips = (
            db.query(LoginAttempt.ip_address)
            .filter(LoginAttempt.last_attempt >= cutoff_time)
            .distinct()
            .count()
        )

        return {
            "period_hours": hours,
            "total_login_attempts": total_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": (
                round(((total_attempts - failed_attempts) / total_attempts) * 100, 2)
                if total_attempts > 0
                else 100.0
            ),
            "currently_locked_accounts": locked_accounts,
            "unique_ip_addresses": unique_ips,
            "timestamp": datetime.utcnow().isoformat(),
        }
