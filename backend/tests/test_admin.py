"""
Tests for admin endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import EmailWhitelist, User


class TestAdminUserManagement:
    """Test admin user management endpoints"""

    def test_list_users_as_admin(self, client: TestClient, admin_auth_headers, test_user):
        """Test listing users as admin"""
        response = client.get("/api/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2  # At least admin and test user
        assert len(data["users"]) >= 2
        assert any(u["email"] == test_user.email for u in data["users"])

    def test_list_users_with_filters(self, client: TestClient, admin_auth_headers):
        """Test listing users with search and filters"""
        response = client.get(
            "/api/admin/users?search=admin&is_verified=true",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all("admin" in u["email"].lower() or "admin" in u["name"].lower() for u in data["users"])
        assert all(u["is_verified"] for u in data["users"])

    def test_list_users_pagination(self, client: TestClient, admin_auth_headers):
        """Test user list pagination"""
        response = client.get(
            "/api/admin/users?skip=0&limit=1",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) <= 1
        assert data["skip"] == 0
        assert data["limit"] == 1

    def test_list_users_as_non_admin(self, client: TestClient, auth_headers):
        """Test listing users without admin privileges"""
        response = client.get("/api/admin/users", headers=auth_headers)
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]

    def test_toggle_user_status(self, client: TestClient, admin_auth_headers, test_user):
        """Test toggling user active status"""
        response = client.post(
            f"/api/admin/users/{test_user.id}/toggle-status",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False  # Should be toggled to inactive
        assert "disabled" in data["message"]

    def test_toggle_own_status(self, client: TestClient, admin_auth_headers, test_admin):
        """Test admin cannot disable themselves"""
        response = client.post(
            f"/api/admin/users/{test_admin.id}/toggle-status",
            headers=admin_auth_headers
        )
        assert response.status_code == 400
        assert "Cannot disable your own account" in response.json()["detail"]

    def test_delete_user(self, client: TestClient, admin_auth_headers, test_user, db: Session):
        """Test deleting a user (soft delete)"""
        response = client.delete(
            f"/api/admin/users/{test_user.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]
        
        # Check user is soft deleted (inactive)
        db.refresh(test_user)
        assert test_user.is_active is False

    def test_delete_nonexistent_user(self, client: TestClient, admin_auth_headers):
        """Test deleting non-existent user"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(
            f"/api/admin/users/{fake_id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_user_statistics(self, client: TestClient, admin_auth_headers, test_user, unverified_user):
        """Test getting user statistics"""
        response = client.get("/api/admin/users/stats", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] >= 3  # Admin, test user, unverified user
        assert data["verified_users"] >= 2  # Admin and test user
        assert data["active_users"] >= 3
        assert data["admin_users"] >= 1
        assert isinstance(data["users_by_role"], dict)
        assert data["recent_registrations"] >= 0


class TestAdminEmailWhitelist:
    """Test admin email whitelist management"""

    def test_list_whitelist_patterns(self, client: TestClient, admin_auth_headers, email_whitelist):
        """Test listing email whitelist patterns"""
        response = client.get("/api/admin/whitelist", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # At least the patterns from fixture
        assert any(p["pattern"] == "@example.com" for p in data)

    def test_create_whitelist_pattern(self, client: TestClient, admin_auth_headers, db: Session):
        """Test creating a new whitelist pattern"""
        response = client.post(
            "/api/admin/whitelist",
            headers=admin_auth_headers,
            json={
                "pattern": "@newdomain.com",
                "description": "New test domain",
                "is_active": True,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pattern"] == "@newdomain.com"
        assert data["description"] == "New test domain"
        assert data["is_active"] is True
        
        # Verify in database
        pattern = db.query(EmailWhitelist).filter(
            EmailWhitelist.pattern == "@newdomain.com"
        ).first()
        assert pattern is not None

    def test_create_duplicate_pattern(self, client: TestClient, admin_auth_headers, email_whitelist):
        """Test creating duplicate whitelist pattern"""
        response = client.post(
            "/api/admin/whitelist",
            headers=admin_auth_headers,
            json={
                "pattern": email_whitelist.pattern,
                "description": "Duplicate",
                "is_active": True,
            }
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_update_whitelist_pattern(self, client: TestClient, admin_auth_headers, email_whitelist):
        """Test updating a whitelist pattern"""
        response = client.put(
            f"/api/admin/whitelist/{email_whitelist.id}",
            headers=admin_auth_headers,
            json={
                "description": "Updated description",
                "is_active": False,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["is_active"] is False
        assert data["pattern"] == email_whitelist.pattern  # Pattern unchanged

    def test_delete_whitelist_pattern(self, client: TestClient, admin_auth_headers, email_whitelist, db: Session):
        """Test deleting a whitelist pattern"""
        pattern_id = str(email_whitelist.id)
        response = client.delete(
            f"/api/admin/whitelist/{pattern_id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]
        
        # Verify deleted from database
        pattern = db.query(EmailWhitelist).filter(
            EmailWhitelist.id == pattern_id
        ).first()
        assert pattern is None


class TestAdminSystemSettings:
    """Test admin system settings management"""

    def test_get_system_settings(self, client: TestClient, admin_auth_headers):
        """Test getting system settings"""
        response = client.get("/api/admin/settings", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["password_min_length"] == 8
        assert data["password_require_uppercase"] is True
        assert data["max_login_attempts"] == 5
        assert data["lockout_duration_minutes"] == 15

    def test_update_system_settings(self, client: TestClient, admin_auth_headers):
        """Test updating system settings"""
        response = client.put(
            "/api/admin/settings",
            headers=admin_auth_headers,
            json={
                "password_min_length": 10,
                "max_login_attempts": 3,
                "enable_user_registration": False,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["password_min_length"] == 10
        assert data["max_login_attempts"] == 3
        assert data["enable_user_registration"] is False

    def test_update_settings_as_non_admin(self, client: TestClient, auth_headers):
        """Test updating settings without admin privileges"""
        response = client.put(
            "/api/admin/settings",
            headers=auth_headers,
            json={"password_min_length": 10}
        )
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]


class TestAdminAuthorization:
    """Test admin authorization across all endpoints"""

    def test_all_admin_endpoints_require_auth(self, client: TestClient):
        """Test that all admin endpoints require authentication"""
        endpoints = [
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/users/stats"),
            ("POST", "/api/admin/users/123/toggle-status"),
            ("DELETE", "/api/admin/users/123"),
            ("GET", "/api/admin/whitelist"),
            ("POST", "/api/admin/whitelist"),
            ("PUT", "/api/admin/whitelist/123"),
            ("DELETE", "/api/admin/whitelist/123"),
            ("GET", "/api/admin/settings"),
            ("PUT", "/api/admin/settings"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 401, f"{method} {endpoint} should require auth"

    def test_all_admin_endpoints_require_admin_role(self, client: TestClient, auth_headers):
        """Test that all admin endpoints require admin role"""
        endpoints = [
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/users/stats"),
            ("GET", "/api/admin/whitelist"),
            ("GET", "/api/admin/settings"),
        ]
        
        for method, endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403, f"{method} {endpoint} should require admin role"
            assert "Admin privileges required" in response.json()["detail"]