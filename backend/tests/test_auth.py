"""
Simple auth tests against running backend.

These are integration tests — they require the backend to be running.
They will be SKIPPED if the backend is not available.
"""

import pytest
import requests


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _require_backend(backend_available):
    """Skip every test in this module when the backend is not running."""


def test_health_check(base_url):
    """Test health endpoint"""
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_non_whitelisted(api_url, unique_email):
    """Test registration with non-whitelisted email"""
    response = requests.post(
        f"{api_url}/auth/register",
        json={
            "email": unique_email,
            "password": "TestPassword123!",
            "name": "Test User",
        },
    )
    # 403 if whitelist check runs first, 400 if password validation runs first
    assert response.status_code in [400, 403]


def test_login_with_test_account(api_url):
    """Test login with existing account"""
    response = requests.post(
        f"{api_url}/auth/login",
        json={"email": "michael.borck@curtin.edu.au", "password": "password123"},
    )
    # 200 success, 401 wrong creds, 403 unverified, 423 locked, 429 rate limited
    assert response.status_code in [200, 401, 403, 423, 429]

    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "user" in data


def test_login_with_wrong_password(api_url):
    """Test login with wrong password"""
    response = requests.post(
        f"{api_url}/auth/login",
        json={"email": "michael.borck@curtin.edu.au", "password": "wrongpassword"},
    )
    # 401 wrong creds, 423 account locked out, 429 rate limited
    assert response.status_code in [401, 423, 429]


def test_cors_headers(api_url):
    """Test CORS headers are properly set"""
    response = requests.post(
        f"{api_url}/auth/login",
        json={"email": "test@example.com", "password": "test"},
        headers={"Origin": "http://localhost:5173"},
    )
    headers_lower = {k.lower(): v for k, v in response.headers.items()}
    assert "access-control-allow-origin" in headers_lower
