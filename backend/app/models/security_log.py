"""
Security audit logging model for tracking security events
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, String, func

from app.core.database import Base
from app.models.user import GUID


class SecurityEventType(str, Enum):
    """Security event types for audit logging"""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_SUCCESS = "password_reset_success"
    EMAIL_VERIFICATION = "email_verification"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"

    # Authorization events
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGED = "role_changed"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"

    # Security events
    CSRF_ATTACK_BLOCKED = "csrf_attack_blocked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALICIOUS_REQUEST_BLOCKED = "malicious_request_blocked"
    BRUTE_FORCE_DETECTED = "brute_force_detected"

    # Data events
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    DATA_EXPORT = "data_export"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"

    # System events
    ADMIN_ACTION = "admin_action"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_ERROR = "system_error"


class SecurityLog(Base):
    """Security audit log model for tracking security events"""

    __tablename__ = "security_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Event information
    event_type = Column(String(50), nullable=False, index=True)  # SecurityEventType
    event_description = Column(String(500), nullable=True)
    severity = Column(String(20), default="info", index=True)  # info, warning, error, critical

    # User and session information
    user_id = Column(GUID(), nullable=True, index=True)  # None for anonymous events
    user_email = Column(String(255), nullable=True, index=True)
    user_role = Column(String(20), nullable=True)

    # Request information
    ip_address = Column(String(45), nullable=False, index=True)  # Support IPv6
    user_agent = Column(String(500), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, etc.

    # Location information (if available)
    country = Column(String(2), nullable=True)  # ISO country code
    city = Column(String(100), nullable=True)

    # Session information
    session_id = Column(String(50), nullable=True)
    jwt_token_id = Column(String(50), nullable=True, index=True)  # For token blacklisting

    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    response_time_ms = Column(String(20), nullable=True)

    # Additional context (JSON field for flexibility)
    details = Column(JSON, nullable=True)  # Additional event-specific data

    # Status and outcome
    success = Column(String(10), default="unknown")  # success, failure, blocked, unknown

    def __repr__(self):
        return f"<SecurityLog(event='{self.event_type}', user='{self.user_email}', ip='{self.ip_address}', time='{self.timestamp}')>"

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical security event"""
        return self.severity == "critical"

    @property
    def is_attack_attempt(self) -> bool:
        """Check if this represents a potential attack"""
        attack_events = {
            SecurityEventType.BRUTE_FORCE_DETECTED,
            SecurityEventType.CSRF_ATTACK_BLOCKED,
            SecurityEventType.MALICIOUS_REQUEST_BLOCKED,
            SecurityEventType.PRIVILEGE_ESCALATION_ATTEMPT,
            SecurityEventType.SUSPICIOUS_ACTIVITY,
        }
        return SecurityEventType(self.event_type) in attack_events

    @property
    def is_authentication_event(self) -> bool:
        """Check if this is an authentication-related event"""
        auth_events = {
            SecurityEventType.LOGIN_SUCCESS,
            SecurityEventType.LOGIN_FAILED,
            SecurityEventType.LOGOUT,
            SecurityEventType.PASSWORD_CHANGE,
            SecurityEventType.PASSWORD_RESET_REQUEST,
            SecurityEventType.PASSWORD_RESET_SUCCESS,
            SecurityEventType.EMAIL_VERIFICATION,
            SecurityEventType.ACCOUNT_LOCKED,
            SecurityEventType.ACCOUNT_UNLOCKED,
        }
        return SecurityEventType(self.event_type) in auth_events

    @classmethod
    def log_event(
        cls,
        db_session,
        event_type: SecurityEventType,
        ip_address: str,
        user_id: str | None = None,
        user_email: str | None = None,
        user_role: str | None = None,
        user_agent: str | None = None,
        request_path: str | None = None,
        request_method: str | None = None,
        session_id: str | None = None,
        jwt_token_id: str | None = None,
        event_description: str | None = None,
        severity: str = "info",
        success: str = "unknown",
        details: dict | None = None,
        response_time_ms: int | None = None,
    ):
        """
        Create and save a security log entry

        Args:
            db_session: Database session
            event_type: Type of security event
            ip_address: Client IP address
            user_id: User ID (if authenticated)
            user_email: User email (if available)
            user_role: User role (if available)
            user_agent: User agent string
            request_path: API path that was accessed
            request_method: HTTP method
            session_id: Session identifier
            jwt_token_id: JWT token ID for blacklisting
            event_description: Human-readable description
            severity: Event severity level
            success: Event outcome
            details: Additional context data
            response_time_ms: Response time in milliseconds

        Returns:
            SecurityLog: Created log entry
        """
        log_entry = cls(
            id=uuid.uuid4(),
            event_type=event_type.value,
            event_description=event_description,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            session_id=session_id,
            jwt_token_id=jwt_token_id,
            timestamp=datetime.utcnow(),
            response_time_ms=str(response_time_ms) if response_time_ms else None,
            details=details or {},
            success=success,
        )

        db_session.add(log_entry)
        db_session.commit()
        return log_entry

    @classmethod
    def get_recent_events(
        cls,
        db_session,
        hours: int = 24,
        event_types: list | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        severity: str | None = None,
        limit: int = 100
    ):
        """
        Get recent security events with filtering

        Args:
            db_session: Database session
            hours: Number of hours to look back
            event_types: List of event types to filter by
            user_id: Filter by specific user
            ip_address: Filter by specific IP
            severity: Filter by severity level
            limit: Maximum number of results

        Returns:
            List of SecurityLog entries
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = db_session.query(cls).filter(cls.timestamp >= cutoff_time)

        if event_types:
            query = query.filter(cls.event_type.in_([et.value for et in event_types]))

        if user_id:
            query = query.filter(cls.user_id == user_id)

        if ip_address:
            query = query.filter(cls.ip_address == ip_address)

        if severity:
            query = query.filter(cls.severity == severity)

        return query.order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def get_attack_summary(cls, db_session, hours: int = 24):
        """Get summary of potential attacks in the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        attack_events = [
            SecurityEventType.BRUTE_FORCE_DETECTED.value,
            SecurityEventType.CSRF_ATTACK_BLOCKED.value,
            SecurityEventType.MALICIOUS_REQUEST_BLOCKED.value,
            SecurityEventType.PRIVILEGE_ESCALATION_ATTEMPT.value,
            SecurityEventType.SUSPICIOUS_ACTIVITY.value,
        ]

        # Count by event type
        event_counts = (
            db_session.query(cls.event_type, func.count(cls.id))
            .filter(cls.timestamp >= cutoff_time)
            .filter(cls.event_type.in_(attack_events))
            .group_by(cls.event_type)
            .all()
        )

        # Count by IP address
        ip_counts = (
            db_session.query(cls.ip_address, func.count(cls.id))
            .filter(cls.timestamp >= cutoff_time)
            .filter(cls.event_type.in_(attack_events))
            .group_by(cls.ip_address)
            .order_by(func.count(cls.id).desc())
            .limit(10)
            .all()
        )

        return {
            "time_period_hours": hours,
            "total_attacks": sum(count for _, count in event_counts),
            "by_type": dict(event_counts),
            "top_attacking_ips": [{"ip": ip, "count": count} for ip, count in ip_counts],
        }

    @classmethod
    def cleanup_old_logs(cls, db_session, days_old: int = 90):
        """Clean up old security log entries"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted_count = (
            db_session.query(cls)
            .filter(cls.timestamp < cutoff_date)
            .delete(synchronize_session=False)
        )
        db_session.commit()
        return deleted_count
