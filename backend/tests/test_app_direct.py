"""
Test the app directly
"""

import sys
from unittest.mock import MagicMock

# Mock langchain modules
sys.modules["langchain"] = MagicMock()
sys.modules["langchain.callbacks"] = MagicMock()
sys.modules["langchain.schema"] = MagicMock()
sys.modules["langchain_anthropic"] = MagicMock()
sys.modules["langchain_openai"] = MagicMock()

# Now we can import
from fastapi.testclient import TestClient


def test_app_initialization():
    """Test app initialization and form handling"""
    # Import app after mocks are set
    from app.main import app

    print("Testing initialized app...")

    # Create client WITHOUT using our conftest fixtures
    client = TestClient(app)

    # Test the simple endpoints first
    print("\n1. Testing root endpoint:")
    response = client.get("/")
    print(f"   Status: {response.status_code}")

    print("\n2. Testing /test-form endpoint:")
    response = client.post("/test-form", data={"username": "test", "password": "pass"})
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Response: {response.json()}")

    # Try with different content
    print("\n3. Testing /test-form with urlencoded content:")
    response = client.post(
        "/test-form",
        content="username=test&password=pass",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Response: {response.json()}")


def test_simple_app():
    """Create a simple app with same setup"""
    from fastapi import FastAPI, Depends
    from fastapi.security import OAuth2PasswordRequestForm
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from app.core.security_middleware import (
        SecurityHeadersMiddleware,
        RequestValidationMiddleware,
        TrustedProxyMiddleware,
    )

    app = FastAPI()

    # Add same middleware in same order
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "*.edu", "*"],
    )

    app.add_middleware(
        RequestValidationMiddleware,
        max_request_size=10 * 1024 * 1024,
        require_user_agent=False,
    )

    app.add_middleware(SecurityHeadersMiddleware)

    app.add_middleware(TrustedProxyMiddleware, trusted_proxies=["127.0.0.1", "::1"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/test")
    async def test_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
        return {"username": form_data.username}

    print("\n4. Testing simple app with all middleware:")
    client = TestClient(app)
    response = client.post("/test", data={"username": "test", "password": "pass"})
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Response: {response.text}")


if __name__ == "__main__":
    test_app_initialization()
    test_simple_app()
