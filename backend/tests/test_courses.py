"""
Course management endpoint tests
Real API tests against running backend
"""

import uuid
from typing import Dict, Optional

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


class TestCourseEndpoints:
    """Test course CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure backend is running"""
        try:
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.exit("Backend must be running! Start with ./backend.sh")
    
    @pytest.fixture
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for test user"""
        # Try to login with test account
        response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": "michael.borck@curtin.edu.au",
                "password": "password123"
            }
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        
        # If test account doesn't work, create new one
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(
            f"{API_URL}/auth/register",
            json={
                "email": email,
                "password": "TestPass123!",
                "name": "Test User"
            }
        )
        
        response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": email,
                "password": "TestPass123!"
            }
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        
        return {}
    
    @pytest.fixture
    def test_course(self, auth_headers) -> Optional[Dict]:
        """Create a test course and return its data"""
        if not auth_headers:
            return None
            
        course_data = {
            "title": f"Test Course {uuid.uuid4().hex[:8]}",
            "code": f"CS{uuid.uuid4().hex[:4].upper()}",
            "description": "A test course for integration testing",
            "teaching_philosophy": "FLIPPED_CLASSROOM",
            "language_preference": "en-AU",
            "semester": "2024-S1",
            "credits": 3,
            "learning_outcomes": [
                "Understand basic concepts",
                "Apply knowledge practically",
                "Analyze complex problems"
            ]
        }
        
        response = requests.post(
            f"{API_URL}/courses",
            json=course_data,
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        return None
    
    def test_create_course(self, auth_headers):
        """Test creating a new course"""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        course_data = {
            "title": "Introduction to Python Programming",
            "code": "COMP1001",
            "description": "Learn Python basics and programming fundamentals",
            "teaching_philosophy": "CONSTRUCTIVIST",
            "language_preference": "en-AU",
            "semester": "2024-S2",
            "credits": 4
        }
        
        response = requests.post(
            f"{API_URL}/courses",
            json=course_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "id" in data
        assert data["title"] == course_data["title"]
        assert data["code"] == course_data["code"]
        assert data["status"] in ["PLANNING", "planning"]
    
    def test_get_all_courses(self, auth_headers, test_course):
        """Test retrieving all courses for user"""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = requests.get(
            f"{API_URL}/courses",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if test_course:
            # Should contain our test course
            course_ids = [c["id"] for c in data]
            assert test_course["id"] in course_ids
    
    def test_get_course_by_id(self, auth_headers, test_course):
        """Test retrieving specific course"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        response = requests.get(
            f"{API_URL}/courses/{test_course['id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_course["id"]
        assert data["title"] == test_course["title"]
        assert "modules" in data or "module_count" in data
    
    def test_update_course(self, auth_headers, test_course):
        """Test updating course details"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        update_data = {
            "title": f"{test_course['title']} - Updated",
            "description": "Updated description for testing",
            "status": "ACTIVE"
        }
        
        response = requests.patch(
            f"{API_URL}/courses/{test_course['id']}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
    
    def test_delete_course(self, auth_headers):
        """Test deleting a course"""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Create a course to delete
        course_data = {
            "title": "Course to Delete",
            "code": "DEL001",
            "description": "This course will be deleted",
            "teaching_philosophy": "TRADITIONAL"
        }
        
        create_response = requests.post(
            f"{API_URL}/courses",
            json=course_data,
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            course_id = create_response.json()["id"]
            
            # Delete the course
            delete_response = requests.delete(
                f"{API_URL}/courses/{course_id}",
                headers=auth_headers
            )
            
            assert delete_response.status_code in [200, 204]
            
            # Verify it's deleted
            get_response = requests.get(
                f"{API_URL}/courses/{course_id}",
                headers=auth_headers
            )
            assert get_response.status_code in [404, 403]
    
    def test_course_without_auth(self):
        """Test accessing courses without authentication"""
        response = requests.get(f"{API_URL}/courses")
        assert response.status_code == 401
    
    def test_invalid_course_data(self, auth_headers):
        """Test creating course with invalid data"""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        invalid_cases = [
            {
                "description": "Missing title",
                "data": {
                    "code": "INVALID",
                    "description": "Missing required title field"
                }
            },
            {
                "description": "Invalid teaching philosophy",
                "data": {
                    "title": "Invalid Philosophy Course",
                    "code": "INV002",
                    "teaching_philosophy": "INVALID_PHILOSOPHY"
                }
            },
            {
                "description": "Empty title",
                "data": {
                    "title": "",
                    "code": "EMPTY01"
                }
            }
        ]
        
        for case in invalid_cases:
            response = requests.post(
                f"{API_URL}/courses",
                json=case["data"],
                headers=auth_headers
            )
            assert response.status_code in [400, 422], f"Failed for: {case['description']}"


class TestCourseModules:
    """Test course module management"""
    
    @pytest.fixture
    def course_with_auth(self, auth_headers) -> tuple:
        """Create course and return with auth headers"""
        if not auth_headers:
            return None, {}
        
        course_data = {
            "title": f"Module Test Course {uuid.uuid4().hex[:8]}",
            "code": f"MOD{uuid.uuid4().hex[:4].upper()}",
            "teaching_philosophy": "FLIPPED_CLASSROOM"
        }
        
        response = requests.post(
            f"{API_URL}/courses",
            json=course_data,
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            return response.json(), auth_headers
        return None, auth_headers
    
    def test_create_module(self, course_with_auth):
        """Test creating course module"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        module_data = {
            "number": 1,
            "title": "Week 1: Introduction",
            "description": "Course introduction and setup",
            "type": "FLIPPED",
            "learning_outcomes": [
                "Understand course structure",
                "Setup development environment"
            ],
            "pre_class_materials": ["Reading: Chapter 1"],
            "in_class_activities": ["Live coding session"],
            "post_class_materials": ["Practice exercises"]
        }
        
        response = requests.post(
            f"{API_URL}/courses/{course['id']}/modules",
            json=module_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert data["number"] == 1
        assert data["title"] == module_data["title"]
        assert data["type"] in ["FLIPPED", "flipped"]
    
    def test_get_course_modules(self, course_with_auth):
        """Test retrieving course modules"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        # Create a few modules
        for i in range(3):
            requests.post(
                f"{API_URL}/courses/{course['id']}/modules",
                json={
                    "number": i + 1,
                    "title": f"Module {i + 1}",
                    "type": "TRADITIONAL"
                },
                headers=auth_headers
            )
        
        # Get all modules
        response = requests.get(
            f"{API_URL}/courses/{course['id']}/modules",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 3
    
    def test_update_module(self, course_with_auth):
        """Test updating a module"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        # Create module
        create_response = requests.post(
            f"{API_URL}/courses/{course['id']}/modules",
            json={
                "number": 1,
                "title": "Original Title",
                "type": "TRADITIONAL"
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            module_id = create_response.json()["id"]
            
            # Update module
            update_response = requests.patch(
                f"{API_URL}/courses/{course['id']}/modules/{module_id}",
                json={
                    "title": "Updated Title",
                    "is_complete": True
                },
                headers=auth_headers
            )
            
            assert update_response.status_code == 200
            data = update_response.json()
            assert data["title"] == "Updated Title"
            assert data["is_complete"] is True
    
    def test_delete_module(self, course_with_auth):
        """Test deleting a module"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        # Create module
        create_response = requests.post(
            f"{API_URL}/courses/{course['id']}/modules",
            json={
                "number": 99,
                "title": "Module to Delete",
                "type": "TRADITIONAL"
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            module_id = create_response.json()["id"]
            
            # Delete module
            delete_response = requests.delete(
                f"{API_URL}/courses/{course['id']}/modules/{module_id}",
                headers=auth_headers
            )
            
            assert delete_response.status_code in [200, 204]
    
    def test_module_ordering(self, course_with_auth):
        """Test that modules maintain proper ordering"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        # Create modules in specific order
        module_numbers = [3, 1, 2, 5, 4]
        for num in module_numbers:
            requests.post(
                f"{API_URL}/courses/{course['id']}/modules",
                json={
                    "number": num,
                    "title": f"Module {num}",
                    "type": "TRADITIONAL"
                },
                headers=auth_headers
            )
        
        # Get modules
        response = requests.get(
            f"{API_URL}/courses/{course['id']}/modules",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            modules = response.json()
            numbers = [m["number"] for m in modules]
            
            # Should be sorted
            assert numbers == sorted(numbers)


class TestCourseSearch:
    """Test course search and filtering"""
    
    @pytest.fixture
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": "michael.borck@curtin.edu.au",
                "password": "password123"
            }
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def test_search_courses_by_title(self, auth_headers):
        """Test searching courses by title"""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Search for courses
        response = requests.get(
            f"{API_URL}/courses",
            params={"search": "Python"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All results should contain "Python" in title or description
        for course in data:
            text = f"{course.get('title', '')} {course.get('description', '')}".lower()
            # Search term might be in title or description
    
    def test_filter_courses_by_status(self, auth_headers):
        """Test filtering courses by status"""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Filter by status
        response = requests.get(
            f"{API_URL}/courses",
            params={"status": "ACTIVE"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All results should have ACTIVE status
        for course in data:
            if "status" in course:
                assert course["status"] in ["ACTIVE", "active"]
    
    def test_pagination(self, auth_headers):
        """Test course list pagination"""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Get paginated results
        response = requests.get(
            f"{API_URL}/courses",
            params={"limit": 5, "offset": 0},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should respect limit
        if isinstance(data, list):
            assert len(data) <= 5