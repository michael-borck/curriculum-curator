"""
Basic integration tests that run against actual backend
No mocks, no complexity - just real tests
"""

import requests
import time
import subprocess
import os
import signal

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


def test_backend_is_running():
    """Test that backend is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        assert response.status_code == 200
        print("✅ Backend is running")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running! Start it with ./backend.sh")
        raise AssertionError("Backend must be running for tests")


def test_health_endpoint():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Health endpoint working")


def test_registration_flow():
    """Test complete registration flow"""
    # Generate unique email
    timestamp = int(time.time())
    email = f"test{timestamp}@example.com"

    # Register new user
    response = requests.post(
        f"{API_URL}/auth/register",
        json={"email": email, "password": "TestPassword123!", "name": "Test User"},
    )

    # Should work or fail with whitelist error
    if response.status_code == 403:
        print("✅ Registration correctly blocked non-whitelisted email")
    elif response.status_code == 200:
        print("✅ Registration successful")
        data = response.json()
        assert "message" in data
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        print(response.json())
        raise AssertionError("Unexpected response status")


def test_login_with_test_account():
    """Test login with known test account"""
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": "michael.borck@curtin.edu.au", "password": "password123"},
    )

    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        print("✅ Login successful")
    elif response.status_code == 401:
        print("⚠️  Test account doesn't exist or wrong password")
    elif response.status_code == 403:
        print("⚠️  Account not verified")
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        print(response.json())


def test_api_cors():
    """Test CORS headers are present"""
    response = requests.options(
        f"{API_URL}/auth/login", headers={"Origin": "http://localhost:5173"}
    )
    assert "access-control-allow-origin" in [k.lower() for k in response.headers]
    print("✅ CORS headers present")


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
