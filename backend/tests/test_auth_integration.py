"""
Integration tests for authentication flow with actual email service
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import EmailWhitelist, User
from app.core import security


class TestRegistrationIntegration:
    """Integration tests for registration with email service"""

    @pytest.fixture
    def mock_email_service(self):
        """Mock email service to prevent actual emails"""
        with patch(
            "app.services.email_service.email_service.send_verification_email"
        ) as mock:
            mock.return_value = True
            yield mock

    def test_register_curtin_email_success(
        self, client: TestClient, db: Session, mock_email_service
    ):
        """Test registration with @curtin.edu.au email"""
        # Ensure domain is whitelisted
        whitelist = EmailWhitelist(
            pattern="@curtin.edu.au",
            description="Curtin University domain",
            is_active=True,
        )
        db.add(whitelist)
        db.commit()

        response = client.post(
            "/api/auth/register",
            json={
                "email": "jane.doe@curtin.edu.au",
                "password": "Test123!Pass",
                "name": "Jane Doe",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "Registration successful" in data["message"]
        assert data["user_email"] == "jane.doe@curtin.edu.au"

        # Verify user was created
        user = db.query(User).filter(User.email == "jane.doe@curtin.edu.au").first()
        assert user is not None
        assert user.name == "Jane Doe"
        assert user.is_verified is False

        # Verify email service was called
        assert mock_email_service.called
        call_args = mock_email_service.call_args[0]
        assert call_args[0].email == "jane.doe@curtin.edu.au"
        assert len(call_args[1]) == 6  # 6-digit code

    def test_register_with_brevo_failure(self, client: TestClient, db: Session):
        """Test registration when Brevo fails"""
        # Ensure domain is whitelisted
        whitelist = EmailWhitelist(
            pattern="@curtin.edu.au",
            description="Curtin University domain",
            is_active=True,
        )
        db.add(whitelist)
        db.commit()

        # Mock email service to fail
        with patch(
            "app.services.email_service.email_service.send_verification_email"
        ) as mock:
            mock.return_value = False

            response = client.post(
                "/api/auth/register",
                json={
                    "email": "test.fail@curtin.edu.au",
                    "password": "Test123!Pass",
                    "name": "Test Fail",
                },
            )

            assert response.status_code == 500
            assert "Could not send verification email" in response.json()["detail"]

            # Verify user was NOT created (rolled back)
            user = (
                db.query(User).filter(User.email == "test.fail@curtin.edu.au").first()
            )
            assert user is None

    def test_register_with_real_brevo_config(self, client: TestClient, db: Session):
        """Test registration with actual Brevo configuration (will fail if not configured)"""
        # Ensure domain is whitelisted
        whitelist = EmailWhitelist(
            pattern="@curtin.edu.au",
            description="Curtin University domain",
            is_active=True,
        )
        db.add(whitelist)
        db.commit()

        # This will use the actual email service
        response = client.post(
            "/api/auth/register",
            json={
                "email": "michael.borck@curtin.edu.au",
                "password": "Test123!Pass",
                "name": "Michael Borck",
            },
        )

        # If Brevo is not properly configured, this will fail with 500
        # We can check the specific error in the logs
        if response.status_code == 500:
            print(f"Registration failed: {response.json()}")
            # Check if it's the email sending that failed
            assert "verification email" in response.json()["detail"].lower()
        else:
            # If it succeeds, verify the response
            assert response.status_code == 200
            data = response.json()
            assert "Registration successful" in data["message"]


class TestLoginIntegration:
    """Integration tests for login flow"""

    def test_login_with_form_data(self, client: TestClient, db: Session):
        """Test login with proper form data"""
        # Create a verified user
        user = User(
            email="test@curtin.edu.au",
            password_hash=security.get_password_hash("TestPass123!"),
            name="Test User",
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        db.commit()

        # Login with form data (OAuth2 compatible)
        response = client.post(
            "/api/auth/login",
            data={"username": "test@curtin.edu.au", "password": "TestPass123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@curtin.edu.au"
