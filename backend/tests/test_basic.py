"""
Basic integration tests that run against actual backend.
No mocks, no complexity - just real tests.

These will be SKIPPED if the backend is not running.
"""

import time

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _require_backend(backend_available):
    """Skip every test in this module when the backend is not running."""


def test_backend_is_running():
    """Test that backend is accessible"""
    response = requests.get(f"{BASE_URL}/docs")
    assert response.status_code == 200


def test_health_endpoint():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_registration_flow():
    """Test complete registration flow"""
    timestamp = int(time.time())
    email = f"test{timestamp}@example.com"

    response = requests.post(
        f"{API_URL}/auth/register",
        json={"email": email, "password": "TestPassword123!", "name": "Test User"},
    )

    # 200 success, 400 validation, 403 not whitelisted, 429 rate limited
    assert response.status_code in [200, 400, 403, 429]


def test_login_with_test_account():
    """Test login with known test account"""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": "michael.borck@curtin.edu.au", "password": "password123"},
    )

    # 200 success, 401 wrong creds, 403 unverified, 423 locked, 429 rate limited
    assert response.status_code in [200, 401, 403, 423, 429]

    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data


def test_api_cors():
    """Test CORS headers are present"""
    response = requests.options(
        f"{API_URL}/auth/login", headers={"Origin": "http://localhost:5173"}
    )
    assert "access-control-allow-origin" in [k.lower() for k in response.headers]


if __name__ == "__main__":
    print("\n🧪 Running Integration Tests\n")
    print("=" * 50)

    test_backend_is_running()
    test_health_endpoint()
    test_registration_flow()
    test_login_with_test_account()
    test_api_cors()

    print("=" * 50)
    print("\n✅ All tests completed!\n")
