"""
Workaround for form data issues
"""

from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import User, UserRole


def create_access_token(data: dict[str, Any]) -> str:
    """Create JWT token directly"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def test_auth_workaround(client: TestClient, db: Session):
    """Test authentication with workaround"""
    # Create user directly
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        role=UserRole.LECTURER.value,
        is_verified=True,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Verify password works
    assert verify_password("testpassword123", user.password_hash)
    
    # Create token directly
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test authenticated endpoint
    response = client.get("/api/auth/me", headers=headers)
    print(f"Get profile status: {response.status_code}")
    if response.status_code == 200:
        print(f"Profile data: {response.json()}")
    else:
        print(f"Error: {response.json()}")
        
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_admin_endpoint_workaround(client: TestClient, db: Session):
    """Test admin endpoints with workaround"""
    # Create admin user
    admin = User(
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        name="Admin User",
        role=UserRole.ADMIN.value,
        is_verified=True,
        is_active=True
    )
    db.add(admin)
    db.commit()
    
    # Create token
    access_token = create_access_token(data={"sub": admin.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test admin endpoint
    response = client.get("/api/admin/users", headers=headers)
    print(f"\nAdmin users list status: {response.status_code}")
    if response.status_code == 200:
        print(f"Users count: {len(response.json()['users'])}")
    else:
        print(f"Error: {response.json()}")
        
    assert response.status_code == 200