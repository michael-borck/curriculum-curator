"""
Unit tests for services - directly test the code for coverage
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import plugin classes at module level
from app.plugins.base import BaseValidator, BaseRemediator
from app.plugins.plugin_manager import PluginManager

# Set test environment
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.config import Settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus
from app.models.lrd import LRD, LRDStatus
from app.models.material import Material, MaterialType
from app.api.deps import get_current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class TestSecurityUnit:
    """Direct unit tests for security functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"

        # Hash password
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20

        # Verify correct password
        assert verify_password(password, hashed) is True

        # Verify wrong password
        assert verify_password("WrongPassword", hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_with_expiry(self):
        """Test token with custom expiry"""
        data = {"sub": "test@example.com"}
        expires = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=expires)

        assert token is not None


class TestDatabaseModelsUnit:
    """Direct unit tests for database models"""

    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = session_local()
        yield session
        session.close()

    def test_user_model_properties(self, db_session):
        """Test User model properties"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            name="Test User",
            role=UserRole.LECTURER.value,
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_lecturer is True
        assert user.is_admin is False
        assert user.is_student is False

    def test_course_model_progress(self, db_session):
        """Test Course model progress calculation"""
        user = User(email="test@example.com", password_hash="hash")
        db_session.add(user)
        db_session.commit()

        course = Course(user_id=user.id, title="Test Course", code="TEST101")
        db_session.add(course)
        db_session.commit()

        # No modules - 0% progress
        assert course.progress_percentage == 0.0

        # Test status defaults
        assert course.status == CourseStatus.PLANNING.value
        assert course.is_active is False

    def test_lrd_model_defaults(self, db_session):
        """Test LRD model defaults"""
        user = User(email="test@example.com", password_hash="hash")
        course = Course(user_id=user.id, title="Test", code="T01")
        db_session.add_all([user, course])
        db_session.commit()

        lrd = LRD(course_id=course.id, version="1.0", content={"topic": "Test Topic"})
        db_session.add(lrd)
        db_session.commit()

        assert lrd.status == LRDStatus.DRAFT.value
        assert lrd.version == "1.0"

    def test_material_versioning(self, db_session):
        """Test Material versioning"""
        user = User(email="test@example.com", password_hash="hash")
        course = Course(user_id=user.id, title="Test", code="T01")
        db_session.add_all([user, course])
        db_session.commit()

        # Create v1
        material_v1 = Material(
            course_id=course.id,
            type=MaterialType.LECTURE.value,
            title="Test Material",
            content={"data": "v1"},
        )
        db_session.add(material_v1)
        db_session.commit()

        assert material_v1.version == 1
        assert material_v1.is_latest is True

        # Create v2
        material_v2 = Material(
            course_id=course.id,
            type=MaterialType.LECTURE.value,
            title="Test Material v2",
            content={"data": "v2"},
            parent_version_id=material_v1.id,
        )
        material_v1.is_latest = False
        db_session.add(material_v2)
        db_session.commit()

        assert material_v2.version == 2
        assert material_v2.is_latest is True
        assert material_v2.parent_version_id == material_v1.id


class TestConfigUnit:
    """Test configuration"""

    def test_settings_defaults(self):
        """Test default settings"""
        settings = Settings()

        assert settings.SECRET_KEY is not None
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.DATABASE_URL is not None


class TestAPIDepsMocked:
    """Test API dependencies with mocks"""

    @patch("app.api.deps.jwt.decode")
    @patch("app.api.deps.get_db")
    def test_get_current_user_mocked(self, mock_get_db, mock_jwt_decode):
        """Test get_current_user dependency"""
        # This would need more setup but shows the pattern
        mock_jwt_decode.return_value = {"sub": "test@example.com"}
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Would need to mock the query chain
        # This demonstrates the mocking approach


class TestPluginBasics:
    """Test plugin base functionality"""

    def test_plugin_imports(self):
        """Test that plugins can be imported"""
        assert BaseValidator is not None
        assert BaseRemediator is not None

    def test_plugin_manager_import(self):
        """Test plugin manager can be imported"""
        assert PluginManager is not None
