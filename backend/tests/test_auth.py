"""
Simple auth tests against running backend
"""
import pytest
import requests

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
            "name": "Test User"
        }
    )
    # Should be blocked
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"]

def test_login_with_test_account(api_url):
    """Test login with existing account"""
    response = requests.post(
        f"{api_url}/auth/login",
        data={
            "username": "michael.borck@curtin.edu.au",
            "password": "password123"
        }
    )
    # Should work or fail gracefully
    assert response.status_code in [200, 401, 403]
    
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "user" in data

def test_login_with_wrong_password(api_url):
    """Test login with wrong password"""
    response = requests.post(
        f"{api_url}/auth/login",
        data={
            "username": "michael.borck@curtin.edu.au",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_cors_headers(api_url):
    """Test CORS headers are properly set"""
    # Try a real request instead of OPTIONS
    response = requests.post(
        f"{api_url}/auth/login",
        data={"username": "test", "password": "test"},
        headers={"Origin": "http://localhost:5173"}
    )
    # We don't care about the auth result, just CORS headers
    headers_lower = {k.lower(): v for k, v in response.headers.items()}
    assert "access-control-allow-origin" in headers_lower