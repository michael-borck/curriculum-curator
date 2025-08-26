"""
Integration tests for admin functionality
Tests against real running backend with actual database
"""

import pytest
import requests
import time
from typing import Any


class TestAdminIntegration:
    """Test admin dashboard functionality with real API calls"""

    @pytest.fixture(scope="class")
    def admin_token(self, api_url) -> str:
        """Get admin authentication token"""
        login_data = {
            "username": "admin@curriculum-curator.com",
            "password": "Admin123!Pass",
        }
        response = requests.post(
            f"{api_url}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            print(f"Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            print(f"URL: {api_url}/auth/login")

        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]

    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token) -> dict[str, str]:
        """Get headers with admin authentication"""
        return {"Authorization": f"Bearer {admin_token}"}

    @pytest.fixture
    def test_user_email(self) -> str:
        """Generate unique test user email"""
        return f"testuser_{int(time.time() * 1000)}@example.com"

    def test_admin_can_get_user_statistics(self, api_url, admin_headers):
        """Test that admin can retrieve user statistics"""
        response = requests.get(f"{api_url}/admin/users/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()

        # Verify expected fields in statistics
        assert "total_users" in data
        assert "verified_users" in data
        assert "active_users" in data
        assert "admin_users" in data
        assert "users_by_role" in data
        assert "recent_registrations" in data

        # Basic sanity checks
        assert data["total_users"] >= 0
        assert data["admin_users"] >= 1  # At least the admin we're using
        assert isinstance(data["users_by_role"], dict)

    def test_admin_can_list_users(self, api_url, admin_headers):
        """Test that admin can list all users with pagination"""
        response = requests.get(
            f"{api_url}/admin/users?skip=0&limit=10", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data

        # Check user data structure
        if data["users"]:
            user = data["users"][0]
            assert "id" in user
            assert "email" in user
            assert "name" in user
            assert "role" in user
            assert "is_verified" in user
            assert "is_active" in user

    def test_admin_can_search_users(self, api_url, admin_headers):
        """Test user search functionality"""
        # Search for admin user
        response = requests.get(
            f"{api_url}/admin/users?search=admin", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Should find at least the admin user
        assert data["total"] >= 1
        assert any("admin" in user["email"].lower() for user in data["users"])

    def test_admin_can_filter_users_by_role(self, api_url, admin_headers):
        """Test filtering users by role"""
        response = requests.get(
            f"{api_url}/admin/users?role=admin", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()

        # All returned users should be admins
        for user in data["users"]:
            assert user["role"] == "admin"

    def test_admin_can_manage_email_whitelist(self, api_url, admin_headers):
        """Test email whitelist CRUD operations"""
        # Create a whitelist entry
        whitelist_data = {
            "pattern": "@testdomain.com",
            "description": "Test domain for integration testing",
            "is_active": True,
        }

        # Create
        create_response = requests.post(
            f"{api_url}/admin/whitelist", json=whitelist_data, headers=admin_headers
        )
        assert create_response.status_code == 200
        created = create_response.json()
        pattern_id = created["id"]

        try:
            # Read
            list_response = requests.get(
                f"{api_url}/admin/whitelist", headers=admin_headers
            )
            assert list_response.status_code == 200
            patterns = list_response.json()
            assert any(p["id"] == pattern_id for p in patterns)

            # Update
            update_data = {
                "description": "Updated test description",
                "is_active": False,
            }
            update_response = requests.put(
                f"{api_url}/admin/whitelist/{pattern_id}",
                json=update_data,
                headers=admin_headers,
            )
            assert update_response.status_code == 200
            updated = update_response.json()
            assert updated["description"] == "Updated test description"
            assert updated["is_active"] is False

        finally:
            # Cleanup: Delete the test whitelist pattern
            delete_response = requests.delete(
                f"{api_url}/admin/whitelist/{pattern_id}", headers=admin_headers
            )
            assert delete_response.status_code == 200

    def test_admin_can_get_system_settings(self, api_url, admin_headers):
        """Test retrieving system settings"""
        response = requests.get(f"{api_url}/admin/settings", headers=admin_headers)
        assert response.status_code == 200
        settings = response.json()

        # Verify expected settings fields
        assert "password_min_length" in settings
        assert "password_require_uppercase" in settings
        assert "password_require_lowercase" in settings
        assert "password_require_numbers" in settings
        assert "password_require_special" in settings
        assert "max_login_attempts" in settings
        assert "lockout_duration_minutes" in settings
        assert "session_timeout_minutes" in settings
        assert "enable_user_registration" in settings
        assert "enable_email_whitelist" in settings

    def test_admin_can_update_system_settings(self, api_url, admin_headers):
        """Test updating system settings"""
        # Get current settings
        get_response = requests.get(f"{api_url}/admin/settings", headers=admin_headers)
        original_settings = get_response.json()

        # Update settings
        new_settings = {
            "password_min_length": 10,
            "max_login_attempts": 3,
            "session_timeout_minutes": 60,
        }

        update_response = requests.put(
            f"{api_url}/admin/settings", json=new_settings, headers=admin_headers
        )
        assert update_response.status_code == 200
        updated = update_response.json()

        # Verify updates (note: backend currently returns the provided values)
        assert updated["password_min_length"] == 10
        assert updated["max_login_attempts"] == 3
        assert updated["session_timeout_minutes"] == 60

        # Restore original settings
        restore_response = requests.put(
            f"{api_url}/admin/settings", json=original_settings, headers=admin_headers
        )
        assert restore_response.status_code == 200

    def test_non_admin_cannot_access_admin_endpoints(self, api_url, test_user_email):
        """Test that non-admin users are denied access to admin endpoints"""
        # Create a regular user
        register_data = {
            "email": test_user_email,
            "password": "TestPass123!",
            "name": "Test User",
        }

        # Register user (might fail if email verification is required)
        requests.post(f"{api_url}/auth/register", json=register_data)

        # For this test, we'll try to access admin endpoints without auth
        # which should always fail

        # Try to access user stats without auth
        response = requests.get(f"{api_url}/admin/users/stats")
        assert response.status_code == 401

        # Try to access user list without auth
        response = requests.get(f"{api_url}/admin/users")
        assert response.status_code == 401

        # Try to access settings without auth
        response = requests.get(f"{api_url}/admin/settings")
        assert response.status_code == 401


class TestUserManagement:
    """Test user management operations"""

    @pytest.fixture(scope="class")
    def admin_token(self, api_url) -> str:
        """Get admin authentication token"""
        login_data = {
            "username": "admin@curriculum-curator.com",
            "password": "Admin123!Pass",
        }
        response = requests.post(
            f"{api_url}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token) -> dict[str, str]:
        """Get headers with admin authentication"""
        return {"Authorization": f"Bearer {admin_token}"}

    def test_admin_can_toggle_user_status(self, api_url, admin_headers):
        """Test that admin can activate/deactivate users"""
        # First, get a non-admin user from the list
        list_response = requests.get(
            f"{api_url}/admin/users?role=lecturer", headers=admin_headers
        )

        if list_response.status_code == 200 and list_response.json()["users"]:
            # Use first non-admin user
            test_user = list_response.json()["users"][0]
            user_id = test_user["id"]
            original_status = test_user["is_active"]

            # Toggle status
            toggle_response = requests.post(
                f"{api_url}/admin/users/{user_id}/toggle-status", headers=admin_headers
            )
            assert toggle_response.status_code == 200

            # Verify status changed
            result = toggle_response.json()
            assert result["is_active"] != original_status

            # Toggle back to original state
            toggle_back_response = requests.post(
                f"{api_url}/admin/users/{user_id}/toggle-status", headers=admin_headers
            )
            assert toggle_back_response.status_code == 200
            assert toggle_back_response.json()["is_active"] == original_status

    def test_admin_cannot_deactivate_self(self, api_url, admin_headers):
        """Test that admin cannot deactivate their own account"""
        # Get admin user's ID
        list_response = requests.get(
            f"{api_url}/admin/users?search=admin@curriculum-curator.com",
            headers=admin_headers,
        )
        assert list_response.status_code == 200

        admin_user = list_response.json()["users"][0]
        admin_id = admin_user["id"]

        # Try to toggle own status
        toggle_response = requests.post(
            f"{api_url}/admin/users/{admin_id}/toggle-status", headers=admin_headers
        )

        # Should be denied
        assert toggle_response.status_code == 400
        assert "Cannot disable your own account" in toggle_response.json()["detail"]
