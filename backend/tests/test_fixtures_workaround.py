"""
Workaround fixtures for tests that need authentication
"""

import pytest
from datetime import datetime, timedelta
from typing import Any
from jose import jwt

from app.core.config import settings


def create_test_token(user_id: str, email: str, role: str = "LECTURER") -> str:
    """
    Create a JWT token directly without going through login endpoint.
    This bypasses the OAuth2PasswordRequestForm issue.
    """
    data = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow(),
        "role": role,
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
def auth_headers_workaround(test_user) -> dict[str, str]:
    """Authentication headers that bypass login endpoint"""
    token = create_test_token(
        user_id=str(test_user.id), email=test_user.email, role=test_user.role
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers_workaround(test_admin) -> dict[str, str]:
    """Admin authentication headers that bypass login endpoint"""
    token = create_test_token(
        user_id=str(test_admin.id), email=test_admin.email, role=test_admin.role
    )
    return {"Authorization": f"Bearer {token}"}
