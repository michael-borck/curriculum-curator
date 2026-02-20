"""
Tests for Security Logger service using in-memory SQLite.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.security_log import SecurityEventType, SecurityLog
from app.models.user import User, UserRole
from app.services.security_logger import SecurityLogger


def _make_request(
    path: str = "/api/auth/login",
    method: str = "POST",
    client_ip: str = "192.168.1.1",
    user_agent: str = "TestBrowser/1.0",
    forwarded_for: str | None = None,
    real_ip: str | None = None,
) -> MagicMock:
    """Create a mock FastAPI Request object."""
    request = MagicMock()
    request.url.path = path
    request.method = method
    request.client.host = client_ip

    headers = {"user-agent": user_agent}
    if forwarded_for:
        headers["x-forwarded-for"] = forwarded_for
    if real_ip:
        headers["x-real-ip"] = real_ip

    request.headers = headers
    return request


def _make_user(
    email: str = "test@example.com",
    role: str = UserRole.LECTURER.value,
) -> MagicMock:
    """Create a mock User object."""
    user = MagicMock(spec=User)
    user.id = str(uuid.uuid4())
    user.email = email
    user.role = role
    return user


# ─── IP EXTRACTION ───────────────────────────────────────────


class TestGetClientIP:
    def test_direct_ip(self):
        request = _make_request(client_ip="10.0.0.1")
        assert SecurityLogger._get_client_ip(request) == "10.0.0.1"

    def test_x_forwarded_for(self):
        request = _make_request(forwarded_for="203.0.113.50, 70.41.3.18")
        assert SecurityLogger._get_client_ip(request) == "203.0.113.50"

    def test_x_real_ip(self):
        request = _make_request(real_ip="172.16.0.5")
        assert SecurityLogger._get_client_ip(request) == "172.16.0.5"

    def test_x_forwarded_for_takes_priority(self):
        request = _make_request(forwarded_for="1.2.3.4", real_ip="5.6.7.8")
        assert SecurityLogger._get_client_ip(request) == "1.2.3.4"

    def test_no_client(self):
        request = _make_request()
        request.client = None
        request.headers = {"user-agent": "Test"}
        assert SecurityLogger._get_client_ip(request) == "Unknown"


# ─── LOG AUTHENTICATION EVENT ────────────────────────────────


class TestLogAuthenticationEvent:
    def test_log_success(self, test_db: Session):
        request = _make_request()
        user = _make_user()

        SecurityLogger.log_authentication_event(
            db=test_db,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            request=request,
            user=user,
            success=True,
            description="User logged in",
        )

        logs = test_db.query(SecurityLog).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.event_type == SecurityEventType.LOGIN_SUCCESS.value
        assert log.success == "success"
        assert log.severity == "info"
        assert log.user_email == user.email

    def test_log_failure(self, test_db: Session):
        request = _make_request()

        SecurityLogger.log_authentication_event(
            db=test_db,
            event_type=SecurityEventType.LOGIN_FAILED,
            request=request,
            success=False,
            description="Bad password",
        )

        logs = test_db.query(SecurityLog).all()
        assert len(logs) == 1
        assert logs[0].success == "failure"
        assert logs[0].severity == "warning"

    def test_log_with_response_time(self, test_db: Session):
        request = _make_request()

        SecurityLogger.log_authentication_event(
            db=test_db,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            request=request,
            success=True,
            response_time_ms=150,
        )

        log = test_db.query(SecurityLog).first()
        assert log is not None
        assert log.response_time_ms == "150"


# ─── LOG SECURITY EVENT ──────────────────────────────────────


class TestLogSecurityEvent:
    def test_log_rate_limit(self, test_db: Session):
        request = _make_request()

        SecurityLogger.log_security_event(
            db=test_db,
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            request=request,
            severity="warning",
            description="Rate limit hit",
            details={"limit": 100, "window": "1m"},
        )

        log = test_db.query(SecurityLog).first()
        assert log is not None
        assert log.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED.value
        assert log.success == "blocked"
        assert log.details == {"limit": 100, "window": "1m"}

    def test_log_info_severity_is_success(self, test_db: Session):
        request = _make_request()

        SecurityLogger.log_security_event(
            db=test_db,
            event_type=SecurityEventType.CONFIGURATION_CHANGE,
            request=request,
            severity="info",
        )

        log = test_db.query(SecurityLog).first()
        assert log is not None
        assert log.success == "success"


# ─── LOG DATA ACCESS EVENT ───────────────────────────────────


class TestLogDataAccessEvent:
    def test_log_data_access(self, test_db: Session):
        request = _make_request(path="/api/units/123")
        user = _make_user()

        SecurityLogger.log_data_access_event(
            db=test_db,
            request=request,
            user=user,
            resource_type="unit",
            resource_id="123",
            action="read",
        )

        log = test_db.query(SecurityLog).first()
        assert log is not None
        assert log.event_type == SecurityEventType.SENSITIVE_DATA_ACCESS.value
        assert log.details["resource_type"] == "unit"
        assert log.details["action"] == "read"

    def test_log_data_access_default_description(self, test_db: Session):
        request = _make_request()
        user = _make_user()

        SecurityLogger.log_data_access_event(
            db=test_db,
            request=request,
            user=user,
            resource_type="assessment",
        )

        log = test_db.query(SecurityLog).first()
        assert log is not None
        assert "Accessed assessment" in log.event_description


# ─── LOG ADMIN ACTION ────────────────────────────────────────


class TestLogAdminAction:
    def test_log_admin_action(self, test_db: Session):
        admin = _make_user(role=UserRole.ADMIN.value)

        SecurityLogger.log_admin_action(
            db=test_db,
            admin_user=admin,
            action="Deleted user account",
            target_user_id="some-user-id",
            details={"reason": "spam"},
        )

        log = test_db.query(SecurityLog).first()
        assert log is not None
        assert log.event_type == SecurityEventType.ADMIN_ACTION.value
        assert log.details["action"] == "Deleted user account"
        assert log.details["target_user_id"] == "some-user-id"
        assert log.details["reason"] == "spam"

    def test_log_admin_action_without_details(self, test_db: Session):
        admin = _make_user()

        SecurityLogger.log_admin_action(
            db=test_db,
            admin_user=admin,
            action="System maintenance",
        )

        log = test_db.query(SecurityLog).first()
        assert log is not None
        assert log.details["action"] == "System maintenance"


# ─── ANALYZE LOGIN PATTERNS ──────────────────────────────────


class TestAnalyzeLoginPatterns:
    def test_empty_history(self, test_db: Session):
        result = SecurityLogger.analyze_login_patterns(test_db, str(uuid.uuid4()))
        assert result["total_attempts"] == 0
        assert result["successful_logins"] == 0
        assert result["failed_logins"] == 0
        assert result["suspicious_patterns"] == []

    def test_with_events(self, test_db: Session):
        user_id = str(uuid.uuid4())

        # Add login events directly
        for _i in range(3):
            SecurityLog.log_event(
                db_session=test_db,
                event_type=SecurityEventType.LOGIN_SUCCESS,
                ip_address="10.0.0.1",
                user_id=user_id,
                success="success",
            )
        for _i in range(2):
            SecurityLog.log_event(
                db_session=test_db,
                event_type=SecurityEventType.LOGIN_FAILED,
                ip_address="10.0.0.2",
                user_id=user_id,
                success="failure",
            )

        result = SecurityLogger.analyze_login_patterns(test_db, user_id)
        assert result["total_attempts"] == 5
        assert result["successful_logins"] == 3
        assert result["failed_logins"] == 2
        assert result["unique_ip_addresses"] == 2

    def test_suspicious_high_failure_rate(self, test_db: Session):
        user_id = str(uuid.uuid4())

        SecurityLog.log_event(
            db_session=test_db,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            ip_address="10.0.0.1",
            user_id=user_id,
            success="success",
        )
        for _i in range(5):
            SecurityLog.log_event(
                db_session=test_db,
                event_type=SecurityEventType.LOGIN_FAILED,
                ip_address="10.0.0.1",
                user_id=user_id,
                success="failure",
            )

        result = SecurityLogger.analyze_login_patterns(test_db, user_id)
        assert "High login failure rate" in result["suspicious_patterns"]

    def test_suspicious_many_ips(self, test_db: Session):
        user_id = str(uuid.uuid4())

        for i in range(6):
            SecurityLog.log_event(
                db_session=test_db,
                event_type=SecurityEventType.LOGIN_SUCCESS,
                ip_address=f"10.0.0.{i}",
                user_id=user_id,
                success="success",
            )

        result = SecurityLogger.analyze_login_patterns(test_db, user_id)
        assert "Multiple IP addresses detected" in result["suspicious_patterns"]
