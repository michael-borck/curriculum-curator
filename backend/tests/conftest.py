"""
Pytest configuration for backend tests

Supports three test modes:
1. Unit tests with in-memory DB - service tests (test_*_service.py)
2. Unit tests without backend - mock-based (test_services_unit.py)
3. Integration tests - require running backend (test_auth*.py, test_basic.py)
"""

import os
import time
import uuid

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set environment variables before importing app modules
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///")

from app.core.database import Base  # noqa: E402
from app.models import (  # noqa: E402
    Assessment,
    AssessmentCategory,
    AssessmentStatus,
    Unit,
    UnitOutline,
    UnitStructureStatus,
    User,
    UserRole,
)

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


def is_backend_running() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


# ──────────────────────────────────────────────────────────────
# Integration test fixtures (unchanged)
# ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the API"""
    return BASE_URL


@pytest.fixture(scope="session")
def api_url():
    """API URL for the backend"""
    return API_URL


@pytest.fixture(scope="session")
def backend_available():
    """Check if backend is available, skip integration tests if not"""
    if not is_backend_running():
        pytest.skip("Backend is not running - skipping integration tests")
    return True


@pytest.fixture
def unique_email():
    """Generate a unique test email"""
    timestamp = int(time.time() * 1000)
    return f"test{timestamp}@example.com"


# ──────────────────────────────────────────────────────────────
# In-memory SQLite fixtures for service tests
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database with all tables for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Import all models to register them, then create tables
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db: Session) -> User:
    """Insert a real User row into the test database."""
    user = User(
        id=str(uuid.uuid4()),
        email="testuser@example.com",
        password_hash="hashed_password_placeholder",
        name="Test User",
        role=UserRole.LECTURER.value,
        is_verified=True,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_unit(test_db: Session, test_user: User) -> Unit:
    """Insert a real Unit row into the test database."""
    unit = Unit(
        id=str(uuid.uuid4()),
        title="Test Unit: Introduction to Testing",
        code="TEST1001",
        description="A unit for testing purposes",
        year=2026,
        semester="semester_1",
        pedagogy_type="inquiry-based",
        difficulty_level="intermediate",
        duration_weeks=12,
        owner_id=test_user.id,
        created_by_id=test_user.id,
        credit_points=6,
    )
    test_db.add(unit)
    test_db.commit()
    test_db.refresh(unit)
    return unit


@pytest.fixture
def test_unit_outline(test_db: Session, test_unit: Unit, test_user: User) -> UnitOutline:
    """Insert a real UnitOutline row into the test database."""
    outline = UnitOutline(
        id=str(uuid.uuid4()),
        unit_id=test_unit.id,
        title=test_unit.title,
        description="Test unit outline",
        duration_weeks=12,
        credit_points=6,
        status=UnitStructureStatus.PLANNING.value,
        created_by_id=test_user.id,
    )
    test_db.add(outline)
    test_db.commit()
    test_db.refresh(outline)
    return outline
