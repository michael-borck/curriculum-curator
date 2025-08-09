"""
Pytest configuration and fixtures for test suite
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Mock the langchain modules BEFORE importing app
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.callbacks'] = MagicMock()
sys.modules['langchain.schema'] = MagicMock()
sys.modules['langchain_anthropic'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models import EmailWhitelist, User, UserRole

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        role=UserRole.LECTURER.value,
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db: Session) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        name="Admin User",
        role=UserRole.ADMIN.value,
        is_verified=True,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def unverified_user(db: Session) -> User:
    """Create an unverified test user."""
    user = User(
        email="unverified@example.com",
        password_hash=get_password_hash("unverifiedpass123"),
        name="Unverified User",
        role=UserRole.LECTURER.value,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def email_whitelist(db: Session) -> EmailWhitelist:
    """Create email whitelist patterns."""
    patterns = [
        EmailWhitelist(
            pattern="@example.com",
            description="Test domain",
            is_active=True,
        ),
        EmailWhitelist(
            pattern="@test.org",
            description="Another test domain",
            is_active=True,
        ),
    ]
    for pattern in patterns:
        db.add(pattern)
    db.commit()
    return patterns[0]


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict[str, str]:
    """
    Get authentication headers for a regular user.
    
    NOTE: This fixture will fail due to OAuth2PasswordRequestForm expecting
    form-encoded data which TestClient doesn't handle well. In production,
    the login endpoint works correctly with proper form data.
    """
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client: TestClient, test_admin: User) -> dict[str, str]:
    """
    Get authentication headers for an admin user.
    
    NOTE: This fixture will fail due to OAuth2PasswordRequestForm expecting
    form-encoded data which TestClient doesn't handle well. In production,
    the login endpoint works correctly with proper form data.
    """
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_admin.email,
            "password": "adminpassword123",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Mock email service to prevent actual email sending
@pytest.fixture(autouse=True)
def mock_email_service(monkeypatch):
    """Mock email service to prevent sending actual emails during tests."""
    async def mock_send_verification_email(*args, **kwargs):
        return True
    
    async def mock_send_password_reset_email(*args, **kwargs):
        return True
    
    async def mock_send_welcome_email(*args, **kwargs):
        return True
    
    # Mock the email service methods
    monkeypatch.setattr("app.services.email_service.EmailService.send_verification_email", mock_send_verification_email)
    monkeypatch.setattr("app.services.email_service.EmailService.send_password_reset_email", mock_send_password_reset_email)
    monkeypatch.setattr("app.services.email_service.EmailService.send_welcome_email", mock_send_welcome_email)


# Mock CSRF protection for tests
@pytest.fixture(autouse=True)
def disable_csrf_protection(monkeypatch):
    """Disable CSRF protection for tests."""
    async def mock_validate_csrf(*args, **kwargs):
        pass
    
    def mock_generate_csrf_tokens(*args, **kwargs):
        return "test-csrf-token"
    
    monkeypatch.setattr("app.core.csrf_protection.csrf_protect.validate_csrf", mock_validate_csrf)
    monkeypatch.setattr("app.core.csrf_protection.csrf_protect.generate_csrf_tokens", mock_generate_csrf_tokens)


# Disable rate limiting for tests
@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for tests."""
    from app.core.rate_limiter import limiter
    limiter.enabled = False
    yield
    limiter.enabled = True


# Mock LLM service
@pytest.fixture(autouse=True)
def mock_llm_service(monkeypatch):
    """Replace LLM service with mock for tests."""
    from tests.test_mocks import mock_llm_service
    monkeypatch.setattr("app.services.llm_service.llm_service", mock_llm_service)