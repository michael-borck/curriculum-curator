"""
Unit tests for core services - directly test the code for coverage
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import Mock

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest

# Set test environment before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.config import Settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.plugins.base import ValidatorPlugin, RemediatorPlugin
from app.plugins.plugin_manager import PluginManager


class TestSecurityUnit:
    """Direct unit tests for security functions"""

    def test_password_hashing(self) -> None:
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

    def test_create_access_token(self) -> None:
        """Test JWT token creation"""
        data = {"sub": "test@example.com"}

        # Create token
        token = create_access_token(data)
        assert token is not None
        assert len(token) > 20

    def test_create_access_token_with_expiry(self) -> None:
        """Test JWT token with custom expiry"""
        data = {"sub": "test@example.com"}
        expires = timedelta(hours=1)

        token = create_access_token(data, expires)
        assert token is not None


class TestConfigUnit:
    """Test configuration"""

    def test_settings_defaults(self) -> None:
        """Test default settings are populated (env may override specific values)"""
        settings = Settings()

        assert settings.SECRET_KEY is not None
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.DATABASE_URL is not None


class TestPluginBasics:
    """Test plugin base functionality"""

    def test_plugin_imports(self) -> None:
        """Test that plugins can be imported"""
        assert ValidatorPlugin is not None
        assert RemediatorPlugin is not None

    def test_plugin_manager_import(self) -> None:
        """Test plugin manager can be imported"""
        assert PluginManager is not None

    def test_create_plugin_manager(self) -> None:
        """Test creating plugin manager instance"""
        pm = PluginManager()
        assert pm is not None
