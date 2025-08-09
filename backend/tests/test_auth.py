"""
Tests for authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import EmailVerification, User
from app.utils.auth_helpers import auth_helpers


class TestRegistration:
    """Test user registration endpoint"""

    def test_register_new_user_success(self, client: TestClient, db: Session, email_whitelist):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Registration successful! Please check your email for the verification code."
        assert data["user_email"] == "newuser@example.com"
        
        # Check user was created in database
        user = db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.is_verified is False
        assert user.name == "New User"

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with existing email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPass123!",
                "name": "Duplicate User",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_register_weak_password(self, client: TestClient, email_whitelist):
        """Test registration with weak password"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "name": "Weak Password User",
            },
        )
        assert response.status_code == 400
        data = response.json()["detail"]
        assert "Password validation failed" in data["error"]
        assert len(data["issues"]) > 0

    def test_register_non_whitelisted_email(self, client: TestClient):
        """Test registration with non-whitelisted email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "notallowed@random.com",
                "password": "SecurePass123!",
                "name": "Not Allowed User",
            },
        )
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"]


class TestEmailVerification:
    """Test email verification endpoint"""

    def test_verify_email_success(self, client: TestClient, db: Session, unverified_user):
        """Test successful email verification"""
        # Create verification code
        success, code = auth_helpers.create_verification_code(db, unverified_user)
        assert success
        
        response = client.post(
            "/api/auth/verify-email",
            json={
                "email": unverified_user.email,
                "code": code,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["is_verified"] is True

    def test_verify_email_invalid_code(self, client: TestClient, unverified_user):
        """Test email verification with invalid code"""
        response = client.post(
            "/api/auth/verify-email",
            json={
                "email": unverified_user.email,
                "code": "999999",
            },
        )
        assert response.status_code == 400
        assert "verification failed" in response.json()["detail"]

    def test_verify_email_expired_code(self, client: TestClient, db: Session, unverified_user):
        """Test email verification with expired code"""
        # Create expired verification code
        from datetime import datetime, timedelta
        verification = EmailVerification(
            user_id=unverified_user.id,
            code="123456",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            used=False,
        )
        db.add(verification)
        db.commit()
        
        response = client.post(
            "/api/auth/verify-email",
            json={
                "email": unverified_user.email,
                "code": "123456",
            },
        )
        assert response.status_code == 400


class TestLogin:
    """Test login endpoint"""

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user.email

    def test_login_invalid_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_unverified_user(self, client: TestClient, unverified_user):
        """Test login with unverified email"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": unverified_user.email,
                "password": "unverifiedpass123",
            },
        )
        assert response.status_code == 403
        assert "not verified" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


class TestPasswordReset:
    """Test password reset endpoints"""

    def test_forgot_password_success(self, client: TestClient, test_user):
        """Test forgot password request"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": test_user.email},
        )
        assert response.status_code == 200
        assert "reset code has been sent" in response.json()["message"]

    def test_forgot_password_nonexistent_user(self, client: TestClient):
        """Test forgot password with non-existent user"""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200
        assert "reset code has been sent" in response.json()["message"]

    def test_reset_password_success(self, client: TestClient, db: Session, test_user):
        """Test successful password reset"""
        # Create reset code
        success, code = auth_helpers.create_password_reset_code(db, test_user)
        assert success
        
        response = client.post(
            "/api/auth/reset-password",
            json={
                "email": test_user.email,
                "code": code,
                "new_password": "NewSecurePass123!",
            },
        )
        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]
        
        # Test login with new password
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "NewSecurePass123!",
            },
        )
        assert login_response.status_code == 200

    def test_reset_password_invalid_code(self, client: TestClient, test_user):
        """Test password reset with invalid code"""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "email": test_user.email,
                "code": "999999",
                "new_password": "NewSecurePass123!",
            },
        )
        assert response.status_code == 400
        assert "Invalid or expired reset code" in response.json()["detail"]


class TestUserProfile:
    """Test user profile endpoint"""

    def test_get_profile_success(self, client: TestClient, auth_headers):
        """Test getting user profile"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["is_verified"] is True

    def test_get_profile_unauthorized(self, client: TestClient):
        """Test getting profile without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_get_profile_invalid_token(self, client: TestClient):
        """Test getting profile with invalid token"""
        headers = {"Authorization": "Bearer invalidtoken"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401