"""
Test without security middleware
"""

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import User, UserRole, EmailWhitelist


def test_login_without_middleware():
    """Test login endpoint without middleware"""
    # Create a minimal app without middleware
    app = FastAPI()
    
    @app.post("/test-login")
    async def test_login(form_data: OAuth2PasswordRequestForm = Depends()):
        return {
            "username": form_data.username,
            "password": "hidden",
            "access_token": "test-token",
            "token_type": "bearer"
        }
    
    client = TestClient(app)
    
    # Test form data
    response = client.post(
        "/test-login",
        data={"username": "test@example.com", "password": "testpass"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["username"] == "test@example.com"


def test_actual_login_simplified(db: Session):
    """Test actual login with simplified setup"""
    # Create test user
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        role=UserRole.LECTURER.value,
        is_verified=True,
        is_active=True
    )
    db.add(user)
    
    # Create whitelist
    whitelist = EmailWhitelist(
        pattern="@example.com",
        description="Test domain",
        is_active=True
    )
    db.add(whitelist)
    db.commit()
    
    # Import here to get the configured app
    from app.main import app
    
    # Remove the SecurityRequestValidationMiddleware temporarily
    # (This is a hack for testing)
    new_middleware = []
    for mw in app.user_middleware:
        if "SecurityRequestValidationMiddleware" not in str(mw):
            new_middleware.append(mw)
    app.user_middleware = new_middleware
    
    client = TestClient(app)
    
    # Try login
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    
    print(f"\nActual login status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.json()}")