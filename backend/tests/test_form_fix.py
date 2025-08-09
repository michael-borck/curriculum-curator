"""
Fix form data issues in tests
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import User, UserRole, EmailWhitelist


def test_form_data_fix(client: TestClient, db: Session):
    """Test form data with correct setup"""
    # Create test user
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        role=UserRole.LECTURER.value,
        is_verified=True,
        is_active=True,
    )
    db.add(user)

    # Create whitelist
    whitelist = EmailWhitelist(
        pattern="@example.com", description="Test domain", is_active=True
    )
    db.add(whitelist)
    db.commit()

    # Test the debug endpoint first
    response = client.post(
        "/test-form",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    print(f"Debug endpoint status: {response.status_code}")
    if response.status_code != 200:
        print(f"Debug endpoint response: {response.json()}")

    # Get CSRF token
    csrf_response = client.get("/csrf-token")
    csrf_token = csrf_response.json()["csrf_token"]

    # Test login with CSRF token in cookie
    client.cookies.set("csrf-token", csrf_token)

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
        headers={"X-CSRF-Token": csrf_token},
    )

    print(f"\nLogin status: {response.status_code}")
    if response.status_code != 200:
        print(f"Login response: {response.json()}")
        print(f"Request headers: {dict(response.request.headers)}")


def test_login_minimal(client: TestClient, test_user: User):
    """Minimal login test"""
    # Just try to login with existing user
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )

    print(f"Minimal login status: {response.status_code}")
    print(f"Minimal login response: {response.json()}")

    # Check what went wrong
    if response.status_code == 422:
        # Try with different content type
        response2 = client.post(
            "/api/auth/login",
            content="username=test@example.com&password=testpassword123",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        print(f"\nWith explicit content type status: {response2.status_code}")
        if response2.status_code != 200:
            print(f"Response: {response2.json()}")
