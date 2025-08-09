"""
Tests for security utilities and middleware
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.password_validator import PasswordValidator
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
    validate_token_security,
)
from app.core.security_utils import SecurityManager
from app.models import LoginAttempt, User


class TestPasswordHashing:
    """Test password hashing utilities"""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification"""
        password = "SecurePassword123!"
        hash = get_password_hash(password)
        
        assert hash != password
        assert verify_password(password, hash) is True
        assert verify_password("WrongPassword", hash) is False

    def test_hash_different_each_time(self):
        """Test that hashing same password gives different results"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestPasswordValidator:
    """Test password validation"""

    def test_valid_password(self):
        """Test validation of a strong password"""
        is_valid, errors = PasswordValidator.validate_password(
            "SecurePass123!",
            "John Doe",
            "john@example.com"
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_password_too_short(self):
        """Test password length validation"""
        is_valid, errors = PasswordValidator.validate_password("Short1!")
        assert is_valid is False
        assert any("at least 8 characters" in error for error in errors)

    def test_password_missing_requirements(self):
        """Test password complexity requirements"""
        test_cases = [
            ("lowercase123!", "uppercase"),
            ("UPPERCASE123!", "lowercase"),
            ("NoNumbers!", "number"),
            ("NoSpecialChars123", "special character"),
        ]
        
        for password, missing in test_cases:
            is_valid, errors = PasswordValidator.validate_password(password)
            assert is_valid is False
            assert any(missing in error for error in errors)

    def test_common_password_rejection(self):
        """Test rejection of common passwords"""
        common_passwords = ["password123", "qwerty123", "admin123"]
        
        for password in common_passwords:
            is_valid, errors = PasswordValidator.validate_password(password)
            assert is_valid is False
            assert any("too common" in error for error in errors)

    def test_personal_info_in_password(self):
        """Test rejection of passwords containing personal info"""
        is_valid, errors = PasswordValidator.validate_password(
            "John123!Doe",
            "John Doe",
            "john@example.com"
        )
        assert is_valid is False
        assert any("personal information" in error for error in errors)

    def test_password_strength_scoring(self):
        """Test password strength scoring"""
        weak_score, weak_desc = PasswordValidator.get_password_strength_score("weak")
        strong_score, strong_desc = PasswordValidator.get_password_strength_score("Str0ng!P@ssw0rd#2024")
        
        assert weak_score < strong_score
        assert weak_desc == "Very Weak"
        assert strong_desc in ["Good", "Excellent"]


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_and_decode_token(self):
        """Test creating and decoding access tokens"""
        user_data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(
            data=user_data,
            client_ip="192.168.1.1",
            user_role="user"
        )
        
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert decoded["ip"] == "192.168.1.1"
        assert decoded["role"] == "user"

    def test_token_expiration(self):
        """Test token expiration"""
        # Create token that expires in 1 second
        token = create_access_token(
            data={"sub": "user123"},
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        assert decode_access_token(token) is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should be invalid after expiration
        assert decode_access_token(token) is None

    def test_token_ip_validation(self):
        """Test token IP binding validation"""
        token = create_access_token(
            data={"sub": "user123"},
            client_ip="192.168.1.1"
        )
        
        # Valid IP match
        decoded = decode_access_token(token, verify_ip="192.168.1.1")
        assert decoded is not None
        
        # Invalid IP match
        decoded = decode_access_token(token, verify_ip="192.168.1.2")
        assert decoded is None

    def test_validate_token_security(self):
        """Test token security validation"""
        # Valid token
        payload = {
            "sub": "user123",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "jti": "token123",
            "ip": "192.168.1.1"
        }
        is_valid, error = validate_token_security(payload, client_ip="192.168.1.1")
        assert is_valid is True
        assert error == ""
        
        # Expired token
        expired_payload = payload.copy()
        expired_payload["exp"] = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        is_valid, error = validate_token_security(expired_payload)
        assert is_valid is False
        assert "expired" in error
        
        # IP mismatch
        is_valid, error = validate_token_security(payload, client_ip="192.168.1.2")
        assert is_valid is False
        assert "IP address mismatch" in error


class TestSecurityManager:
    """Test security manager utilities"""

    def test_check_account_lockout(self, db: Session):
        """Test account lockout checking"""
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # No lockout initially
        is_locked, reason, minutes = SecurityManager.check_account_lockout(db, email, ip)
        assert is_locked is False
        
        # Create failed login attempts
        for i in range(5):
            attempt = LoginAttempt(
                email=email,
                ip_address=ip,
                success=False,
                failure_reason="Invalid password"
            )
            db.add(attempt)
        db.commit()
        
        # Should be locked after 5 failures
        is_locked, reason, minutes = SecurityManager.check_account_lockout(db, email, ip)
        assert is_locked is True
        assert "Too many failed login attempts" in reason
        assert minutes > 0

    def test_suspicious_activity_detection(self, db: Session):
        """Test suspicious activity detection"""
        email = "test@example.com"
        
        # Normal activity
        is_suspicious, reason = SecurityManager.is_suspicious_activity(
            db, email, "192.168.1.1", "Mozilla/5.0"
        )
        assert is_suspicious is False
        
        # Suspicious user agent
        is_suspicious, reason = SecurityManager.is_suspicious_activity(
            db, email, "192.168.1.1", "sqlmap/1.0"
        )
        assert is_suspicious is True
        assert "Suspicious user agent" in reason

    def test_get_lockout_status_message(self):
        """Test lockout status message generation"""
        message = SecurityManager.get_lockout_status_message(
            True, "Too many attempts", 10
        )
        assert "locked" in message
        assert "10 minutes" in message
        
        message = SecurityManager.get_lockout_status_message(False, "", 0)
        assert message == "Account is not locked"

    @patch('app.core.security_utils.Request')
    def test_get_client_ip(self, mock_request):
        """Test client IP extraction"""
        # Test with X-Forwarded-For header
        mock_request.headers = {"x-forwarded-for": "10.0.0.1, 192.168.1.1"}
        ip = SecurityManager.get_client_ip(mock_request)
        assert ip == "10.0.0.1"
        
        # Test with X-Real-IP header
        mock_request.headers = {"x-real-ip": "192.168.1.2"}
        ip = SecurityManager.get_client_ip(mock_request)
        assert ip == "192.168.1.2"
        
        # Test with direct client IP
        mock_request.headers = {}
        mock_request.client = Mock(host="192.168.1.3")
        ip = SecurityManager.get_client_ip(mock_request)
        assert ip == "192.168.1.3"


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_headers(self, client, email_whitelist):
        """Test that rate limit headers are set"""
        # Make multiple requests to trigger rate limiting
        for i in range(5):
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"user{i}@example.com",
                    "password": "TestPass123!",
                    "name": f"User {i}"
                }
            )
            
            # Check rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers