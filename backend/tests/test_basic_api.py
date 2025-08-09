"""
Basic API tests to verify core functionality
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Curriculum Curator API"
    assert data["version"] == "0.1.0"


def test_health_endpoint(client: TestClient):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "curriculum-curator"


def test_login_endpoint_exists(client: TestClient):
    """Test that login endpoint exists"""
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    # Should get 401/422/423 for wrong credentials, not 404
    assert response.status_code in [401, 403, 422, 423]  # Not 404


def test_register_endpoint_exists(client: TestClient, db):
    """Test that register endpoint exists"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Password123!",
            "name": "Test User"
        }
    )
    # Should get some response, not 404
    assert response.status_code != 404