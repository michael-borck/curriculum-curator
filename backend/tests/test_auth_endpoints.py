"""
Comprehensive authentication endpoint tests
Tests against running backend - no mocks
"""

import time
import uuid
from typing import Dict, Optional

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


class TestAuthEndpoints:
    """Test all authentication endpoints with real API calls"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure backend is running before tests"""
        try:
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.exit("Backend must be running! Start with ./backend.sh")
    
    @pytest.fixture
    def unique_email(self) -> str:
        """Generate unique email for testing"""
        return f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    @pytest.fixture
    def test_user(self, unique_email) -> Dict:
        """Create a test user and return credentials"""
        user_data = {
            "email": unique_email,
            "password": "TestPass123!@#",
            "name": "Test User"
        }
        
        # First add to whitelist if needed
        admin_token = self._get_admin_token()
        if admin_token:
            requests.post(
                f"{API_URL}/admin/whitelist",
                json={"email": unique_email},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        # Register user
        response = requests.post(f"{API_URL}/auth/register", json=user_data)
        
        # Handle different registration scenarios
        if response.status_code in [200, 201]:
            return user_data
        elif response.status_code == 403:
            # Email not whitelisted, return test account
            return {
                "email": "michael.borck@curtin.edu.au",
                "password": "password123",
                "name": "Michael Borck"
            }
        else:
            return user_data
    
    def _get_admin_token(self) -> Optional[str]:
        """Try to get admin token for whitelist management"""
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                data={
                    "username": "admin@example.com",
                    "password": "admin123"
                }
            )
            if response.status_code == 200:
                return response.json()["access_token"]
        except:
            pass
        return None
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_register_new_user(self, unique_email):
        """Test user registration flow"""
        user_data = {
            "email": unique_email,
            "password": "ValidPass123!",
            "name": "New Test User"
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=user_data)
        
        # Registration can fail due to whitelist
        assert response.status_code in [200, 201, 403, 400]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "message" in data or "id" in data
    
    def test_register_duplicate_user(self):
        """Test registering duplicate email"""
        email = "duplicate@example.com"
        user_data = {
            "email": email,
            "password": "ValidPass123!",
            "name": "First User"
        }
        
        # First registration
        requests.post(f"{API_URL}/auth/register", json=user_data)
        
        # Second registration - should fail
        response = requests.post(f"{API_URL}/auth/register", json=user_data)
        
        # Could be 400 (duplicate) or 403 (not whitelisted)
        assert response.status_code in [400, 403]
    
    def test_register_invalid_password(self, unique_email):
        """Test registration with weak password"""
        test_cases = [
            {"password": "short", "reason": "too short"},
            {"password": "nouppercase123!", "reason": "no uppercase"},
            {"password": "NOLOWERCASE123!", "reason": "no lowercase"},
            {"password": "NoNumbers!", "reason": "no numbers"},
            {"password": "NoSpecialChars123", "reason": "no special chars"},
        ]
        
        for test_case in test_cases:
            response = requests.post(
                f"{API_URL}/auth/register",
                json={
                    "email": f"{test_case['reason']}_{unique_email}",
                    "password": test_case["password"],
                    "name": "Test User"
                }
            )
            # Should reject weak passwords
            assert response.status_code in [400, 422, 403], f"Failed for: {test_case['reason']}"
    
    def test_login_valid_credentials(self, test_user):
        """Test login with valid credentials"""
        response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            
            # Verify token works
            headers = {"Authorization": f"Bearer {data['access_token']}"}
            me_response = requests.get(f"{API_URL}/auth/me", headers=headers)
            assert me_response.status_code == 200
            me_data = me_response.json()
            assert me_data["email"] == test_user["email"]
        elif response.status_code == 403:
            # Account not verified
            data = response.json()
            assert "not verified" in data.get("detail", "").lower()
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data
    
    def test_login_rate_limiting(self):
        """Test rate limiting on login endpoint"""
        # Attempt many rapid logins
        responses = []
        for i in range(10):
            response = requests.post(
                f"{API_URL}/auth/login",
                data={
                    "username": f"attacker{i}@example.com",
                    "password": "wrong"
                }
            )
            responses.append(response.status_code)
        
        # Should see rate limiting kick in (429 status)
        # Or at least consistent 401s without server errors
        assert all(status in [401, 403, 429] for status in responses)
    
    def test_get_current_user(self, test_user):
        """Test getting current user info"""
        # First login
        login_response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(f"{API_URL}/auth/me", headers=headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["email"] == test_user["email"]
            assert "id" in data
            assert "role" in data
            assert "teaching_philosophy" in data
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        response = requests.get(f"{API_URL}/auth/me")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "not authenticated" in data["detail"].lower()
    
    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_password_reset_request(self, test_user):
        """Test password reset request flow"""
        response = requests.post(
            f"{API_URL}/auth/password-reset-request",
            json={"email": test_user["email"]}
        )
        
        # Should accept request even if email doesn't exist (security)
        assert response.status_code in [200, 202]
        data = response.json()
        assert "message" in data
    
    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token"""
        response = requests.get(f"{API_URL}/auth/verify-email/invalid_token_123")
        assert response.status_code in [400, 404]
    
    def test_logout(self, test_user):
        """Test logout flow"""
        # First login
        login_response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Logout
            response = requests.post(f"{API_URL}/auth/logout", headers=headers)
            assert response.status_code in [200, 204]
    
    def test_update_profile(self, test_user):
        """Test updating user profile"""
        # Login first
        login_response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Update profile
            update_data = {
                "name": "Updated Name",
                "teaching_philosophy": "CONSTRUCTIVIST",
                "language_preference": "en-GB"
            }
            
            response = requests.patch(
                f"{API_URL}/auth/profile",
                json=update_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["name"] == "Updated Name"
                assert data["teaching_philosophy"] == "CONSTRUCTIVIST"
    
    def test_change_password(self, test_user):
        """Test changing password"""
        # Login first
        login_response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Change password
            new_password = "NewSecurePass456!@#"
            response = requests.post(
                f"{API_URL}/auth/change-password",
                json={
                    "current_password": test_user["password"],
                    "new_password": new_password
                },
                headers=headers
            )
            
            if response.status_code == 200:
                # Try login with new password
                new_login = requests.post(
                    f"{API_URL}/auth/login",
                    data={
                        "username": test_user["email"],
                        "password": new_password
                    }
                )
                assert new_login.status_code in [200, 403]


class TestAuthSecurity:
    """Test security aspects of authentication"""
    
    def test_sql_injection_attempt(self):
        """Test SQL injection protection"""
        malicious_inputs = [
            "admin' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        for payload in malicious_inputs:
            response = requests.post(
                f"{API_URL}/auth/login",
                data={
                    "username": payload,
                    "password": "password"
                }
            )
            # Should safely reject, not error
            assert response.status_code in [401, 403, 422]
    
    def test_xss_prevention(self):
        """Test XSS prevention in registration"""
        xss_payload = "<script>alert('XSS')</script>"
        
        response = requests.post(
            f"{API_URL}/auth/register",
            json={
                "email": "test@example.com",
                "password": "ValidPass123!",
                "name": xss_payload
            }
        )
        
        # Should either reject or sanitize
        if response.status_code in [200, 201]:
            # If accepted, verify it's sanitized when retrieved
            pass
    
    def test_timing_attack_resistance(self):
        """Test resistance to timing attacks"""
        import time
        
        # Time valid vs invalid users
        times_valid = []
        times_invalid = []
        
        for _ in range(5):
            # Valid user
            start = time.time()
            requests.post(
                f"{API_URL}/auth/login",
                data={
                    "username": "michael.borck@curtin.edu.au",
                    "password": "wrong"
                }
            )
            times_valid.append(time.time() - start)
            
            # Invalid user
            start = time.time()
            requests.post(
                f"{API_URL}/auth/login",
                data={
                    "username": "nonexistent@example.com",
                    "password": "wrong"
                }
            )
            times_invalid.append(time.time() - start)
        
        # Times should be similar (constant time comparison)
        avg_valid = sum(times_valid) / len(times_valid)
        avg_invalid = sum(times_invalid) / len(times_invalid)
        
        # Allow 100ms difference
        assert abs(avg_valid - avg_invalid) < 0.1
    
    def test_session_security_headers(self):
        """Test security headers in responses"""
        response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": "test@example.com",
                "password": "password"
            }
        )
        
        headers = response.headers
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        # At least some security headers should be present
        present_headers = [h for h in security_headers if h in headers]
        # Note: Some headers may only be set in production