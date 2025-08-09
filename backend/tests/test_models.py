"""
Tests for database models
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import (
    User,
    UserRole,
    EmailWhitelist,
    EmailVerification,
    PasswordReset,
    LoginAttempt,
    SecurityLog,
    SecurityEventType,
)


class TestUserModel:
    """Test User model"""

    def test_create_user(self, db: Session):
        """Test creating a user"""
        user = User(
            email="newuser@example.com",
            password_hash="hashed_password",
            name="New User",
            role=UserRole.LECTURER.value,
            is_verified=False,
            is_active=True,
        )
        db.add(user)
        db.commit()

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_unique_constraint(self, db: Session):
        """Test that email must be unique"""
        user1 = User(
            email="duplicate@example.com",
            password_hash="hash1",
            name="User 1",
            role=UserRole.LECTURER.value,
        )
        db.add(user1)
        db.commit()

        user2 = User(
            email="duplicate@example.com",
            password_hash="hash2",
            name="User 2",
            role=UserRole.LECTURER.value,
        )
        db.add(user2)

        with pytest.raises(IntegrityError):
            db.commit()

    def test_user_roles(self):
        """Test user role enum values"""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.LECTURER.value == "lecturer"


class TestEmailWhitelistModel:
    """Test EmailWhitelist model"""

    def test_create_whitelist_pattern(self, db: Session):
        """Test creating email whitelist pattern"""
        pattern = EmailWhitelist(
            pattern="@university.edu", description="University domain", is_active=True
        )
        db.add(pattern)
        db.commit()

        assert pattern.id is not None
        assert pattern.pattern == "@university.edu"

    def test_whitelist_pattern_validation(self):
        """Test pattern validation"""
        # Valid patterns
        valid_patterns = ["@example.com", "specific@example.com", "@sub.domain.com"]

        for valid in valid_patterns:
            pattern = EmailWhitelist(pattern=valid)
            validated = pattern.validate_pattern("pattern", valid)
            assert validated == valid.lower()

    def test_whitelist_matches_email(self, db: Session):
        """Test email matching against patterns"""
        domain_pattern = EmailWhitelist(pattern="@allowed.com", is_active=True)
        specific_pattern = EmailWhitelist(pattern="admin@special.com", is_active=True)

        # Test domain pattern matching
        assert domain_pattern.matches_email("user@allowed.com") is True
        assert domain_pattern.matches_email("user@notallowed.com") is False

        # Test specific email matching
        assert specific_pattern.matches_email("admin@special.com") is True
        assert specific_pattern.matches_email("user@special.com") is False

    def test_is_email_whitelisted(self, db: Session):
        """Test class method for checking whitelist"""
        # Add patterns
        patterns = [
            EmailWhitelist(pattern="@allowed.com", is_active=True),
            EmailWhitelist(pattern="@inactive.com", is_active=False),
        ]
        for p in patterns:
            db.add(p)
        db.commit()

        # Test whitelisting
        assert EmailWhitelist.is_email_whitelisted(db, "user@allowed.com") is True
        assert EmailWhitelist.is_email_whitelisted(db, "user@inactive.com") is False
        assert EmailWhitelist.is_email_whitelisted(db, "user@random.com") is False


class TestEmailVerificationModel:
    """Test EmailVerification model"""

    def test_create_verification(self, db: Session, test_user):
        """Test creating email verification record"""
        verification = EmailVerification(
            user_id=test_user.id,
            code="123456",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used=False,
        )
        db.add(verification)
        db.commit()

        assert verification.id is not None
        assert verification.code == "123456"
        assert verification.used is False

    def test_is_valid_method(self, db: Session, test_user):
        """Test verification validity checking"""
        # Valid verification
        valid_verification = EmailVerification(
            user_id=test_user.id,
            code="111111",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used=False,
        )
        assert valid_verification.is_valid() is True

        # Expired verification
        expired_verification = EmailVerification(
            user_id=test_user.id,
            code="222222",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            used=False,
        )
        assert expired_verification.is_valid() is False

        # Used verification
        used_verification = EmailVerification(
            user_id=test_user.id,
            code="333333",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used=True,
        )
        assert used_verification.is_valid() is False


class TestLoginAttemptModel:
    """Test LoginAttempt model"""

    def test_create_login_attempt(self, db: Session):
        """Test creating login attempt record"""
        attempt = LoginAttempt(
            email="test@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=False,
            failure_reason="Invalid password",
        )
        db.add(attempt)
        db.commit()

        assert attempt.id is not None
        assert attempt.success is False
        assert attempt.consecutive_failures == 1

    def test_get_recent_attempts(self, db: Session):
        """Test getting recent login attempts"""
        email = "test@example.com"
        ip = "192.168.1.1"

        # Create some attempts
        for i in range(3):
            attempt = LoginAttempt(email=email, ip_address=ip, success=False)
            db.add(attempt)
        db.commit()

        # Get recent attempts
        recent = LoginAttempt.get_recent_attempts(db, email, hours=1)
        assert len(recent) == 3

        recent_by_ip = LoginAttempt.get_recent_attempts(db, ip_address=ip, hours=1)
        assert len(recent_by_ip) == 3

    def test_lockout_check(self, db: Session):
        """Test account lockout checking"""
        email = "locked@example.com"

        # Create failed attempts
        for i in range(5):
            attempt = LoginAttempt(
                email=email,
                ip_address="192.168.1.1",
                success=False,
                consecutive_failures=i + 1,
            )
            db.add(attempt)
        db.commit()

        # Update last attempt to trigger lockout
        last_attempt = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.email == email)
            .order_by(LoginAttempt.timestamp.desc())
            .first()
        )
        last_attempt.consecutive_failures = 5
        last_attempt.is_locked = True
        db.commit()

        # Check lockout
        is_locked = LoginAttempt.is_account_locked(db, email)
        assert is_locked is True


class TestSecurityLogModel:
    """Test SecurityLog model"""

    def test_create_security_log(self, db: Session):
        """Test creating security log entry"""
        log = SecurityLog.log_event(
            db_session=db,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            ip_address="192.168.1.1",
            user_id="user123",
            user_email="test@example.com",
            event_description="Successful login",
            severity="info",
            success="success",
        )

        assert log.id is not None
        assert log.event_type == SecurityEventType.LOGIN_SUCCESS.value
        assert log.is_critical is False
        assert log.is_attack_attempt is False
        assert log.is_authentication_event is True

    def test_get_recent_events(self, db: Session):
        """Test retrieving recent security events"""
        # Create various events
        events = [
            (SecurityEventType.LOGIN_SUCCESS, "info"),
            (SecurityEventType.LOGIN_FAILED, "warning"),
            (SecurityEventType.BRUTE_FORCE_DETECTED, "critical"),
        ]

        for event_type, severity in events:
            SecurityLog.log_event(
                db_session=db,
                event_type=event_type,
                ip_address="192.168.1.1",
                severity=severity,
            )

        # Get recent events
        recent = SecurityLog.get_recent_events(db, hours=1)
        assert len(recent) == 3

        # Filter by event type
        login_events = SecurityLog.get_recent_events(
            db,
            hours=1,
            event_types=[
                SecurityEventType.LOGIN_SUCCESS,
                SecurityEventType.LOGIN_FAILED,
            ],
        )
        assert len(login_events) == 2

    def test_attack_summary(self, db: Session):
        """Test getting attack summary"""
        # Create attack events
        attack_types = [
            SecurityEventType.BRUTE_FORCE_DETECTED,
            SecurityEventType.CSRF_ATTACK_BLOCKED,
            SecurityEventType.MALICIOUS_REQUEST_BLOCKED,
        ]

        for attack_type in attack_types:
            for i in range(2):
                SecurityLog.log_event(
                    db_session=db,
                    event_type=attack_type,
                    ip_address=f"192.168.1.{i + 1}",
                )

        # Get attack summary
        summary = SecurityLog.get_attack_summary(db, hours=24)
        assert summary["total_attacks"] == 6
        assert len(summary["by_type"]) == 3
        assert len(summary["top_attacking_ips"]) >= 2
