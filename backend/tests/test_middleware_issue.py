"""
Test to identify which middleware is causing the issue
"""

import sys
from unittest.mock import MagicMock

# Mock langchain modules
sys.modules["langchain"] = MagicMock()
sys.modules["langchain.callbacks"] = MagicMock()
sys.modules["langchain.schema"] = MagicMock()
sys.modules["langchain_anthropic"] = MagicMock()
sys.modules["langchain_openai"] = MagicMock()

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

# Import our middlewares one by one
from app.core.security_middleware import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
)


def test_with_no_middleware():
    """Test with no middleware"""
    app = FastAPI()

    @app.post("/test")
    async def test_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
        return {"username": form_data.username}

    client = TestClient(app)
    response = client.post("/test", data={"username": "test", "password": "pass"})
    print(f"No middleware - Status: {response.status_code}")
    assert response.status_code == 200


def test_with_cors_middleware():
    """Test with CORS middleware only"""
    app = FastAPI()

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

    client = TestClient(app)
    response = client.post("/test", data={"username": "test", "password": "pass"})
    print(f"With CORS middleware - Status: {response.status_code}")
    assert response.status_code == 200


def test_with_security_headers_middleware():
    """Test with SecurityHeadersMiddleware"""
    app = FastAPI()

    app.add_middleware(SecurityHeadersMiddleware)

    @app.post("/test")
    async def test_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
        return {"username": form_data.username}

    client = TestClient(app)
    response = client.post("/test", data={"username": "test", "password": "pass"})
    print(f"With SecurityHeadersMiddleware - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"  Response: {response.json()}")
    return response.status_code == 200


def test_with_security_validation_middleware():
    """Test with RequestValidationMiddleware"""
    app = FastAPI()

    app.add_middleware(RequestValidationMiddleware)

    @app.post("/test")
    async def test_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
        return {"username": form_data.username}

    client = TestClient(app)
    response = client.post("/test", data={"username": "test", "password": "pass"})
    print(f"With SecurityRequestValidationMiddleware - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"  Response: {response.json()}")
    return response.status_code == 200


if __name__ == "__main__":
    test_with_no_middleware()
    test_with_cors_middleware()

    # Test our custom middleware
    headers_ok = test_with_security_headers_middleware()
    validation_ok = test_with_security_validation_middleware()

    if not headers_ok:
        print("\n❌ SecurityHeadersMiddleware is causing the issue!")
    if not validation_ok:
        print("\n❌ RequestValidationMiddleware is causing the issue!")
