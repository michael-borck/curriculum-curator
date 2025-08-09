"""
Simple authentication tests to debug issues
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import EmailWhitelist, User, UserRole


@pytest.mark.skip(reason="OAuth2PasswordRequestForm form data handling issue with TestClient")
def test_login_with_form_data(client: TestClient, test_user: User):
    """Test login with proper form data"""
    # Get CSRF token first
    csrf_response = client.get("/csrf-token")
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.json()["csrf_token"]
    
    # Login with form data (OAuth2PasswordRequestForm expects form-encoded data)
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        },
        headers={
            "X-CSRF-Token": csrf_token,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    
    # Print response for debugging
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_register_with_whitelist(client: TestClient, db: Session):
    """Test registration with email whitelist"""
    # Create whitelist entry
    whitelist = EmailWhitelist(
        pattern="@test.com",
        description="Test domain",
        is_active=True
    )
    db.add(whitelist)
    db.commit()
    db.refresh(whitelist)
    print(f"Created whitelist: {whitelist.pattern}")
    
    # Get CSRF token
    csrf_response = client.get("/csrf-token")
    csrf_token = csrf_response.json()["csrf_token"]
    
    # Register user
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "StrongPassword123!",
            "name": "New User"
        },
        headers={
            "X-CSRF-Token": csrf_token
        }
    )
    
    print(f"Register Status: {response.status_code}")
    if response.status_code != 201:
        print(f"Register Response: {response.json()}")
    
    assert response.status_code == 201


def test_get_csrf_token(client: TestClient):
    """Test getting CSRF token"""
    response = client.get("/csrf-token")
    assert response.status_code == 200
    assert "csrf_token" in response.json()
    print(f"CSRF Token: {response.json()['csrf_token']}")