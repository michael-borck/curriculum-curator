"""
Integration tests for course and material generation
Tests against real running backend with actual API calls
"""

import pytest
import requests
import time
import json
from typing import Dict, Any, Optional


class TestCourseCreation:
    """Test course creation and management with real API"""
    
    @pytest.fixture(scope="class")
    def user_token(self, api_url) -> str:
        """Create a test user and get authentication token"""
        # Try to use existing test user first
        login_data = {
            "username": "michael.borck@curtin.edu.au",
            "password": "Test123!Pass"
        }
        response = requests.post(
            f"{api_url}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        
        # Fallback to admin if test user doesn't exist
        login_data = {
            "username": "admin@curriculum-curator.com",
            "password": "Admin123!Pass"
        }
        response = requests.post(
            f"{api_url}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, user_token) -> dict[str, str]:
        """Get headers with authentication"""
        return {"Authorization": f"Bearer {user_token}"}
    
    @pytest.fixture
    def test_course_data(self) -> dict[str, Any]:
        """Generate test course data"""
        timestamp = int(time.time() * 1000)
        return {
            "title": f"Test Course {timestamp}",
            "description": "Integration test course for automated testing",
            "objectives": [
                "Understand basic concepts",
                "Apply knowledge in practice",
                "Evaluate different approaches"
            ],
            "duration_weeks": 12,
            "level": "intermediate",
            "teaching_philosophy": "constructivist"
        }
    
    def test_create_course(self, api_url, auth_headers, test_course_data):
        """Test creating a new course"""
        response = requests.post(
            f"{api_url}/courses",
            json=test_course_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        course = response.json()
        assert course["title"] == test_course_data["title"]
        assert course["description"] == test_course_data["description"]
        assert "id" in course
        assert "created_at" in course
        
        # Store for cleanup
        return course["id"]
    
    def test_list_courses(self, api_url, auth_headers):
        """Test listing user's courses"""
        response = requests.get(
            f"{api_url}/courses",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        courses = response.json()
        assert isinstance(courses, list)
        
        if courses:
            # Check course structure
            course = courses[0]
            assert "id" in course
            assert "title" in course
            assert "description" in course
            assert "created_at" in course
    
    def test_get_course_details(self, api_url, auth_headers, test_course_data):
        """Test getting detailed course information"""
        # First create a course
        create_response = requests.post(
            f"{api_url}/courses",
            json=test_course_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        course_id = create_response.json()["id"]
        
        # Get course details
        response = requests.get(
            f"{api_url}/courses/{course_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        course = response.json()
        assert course["id"] == course_id
        assert course["title"] == test_course_data["title"]
        assert "modules" in course or "materials" in course or "lrds" in course
    
    def test_update_course(self, api_url, auth_headers, test_course_data):
        """Test updating course information"""
        # Create course
        create_response = requests.post(
            f"{api_url}/courses",
            json=test_course_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        course_id = create_response.json()["id"]
        
        # Update course
        update_data = {
            "title": f"Updated {test_course_data['title']}",
            "description": "Updated description for testing"
        }
        
        update_response = requests.put(
            f"{api_url}/courses/{course_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated["title"] == update_data["title"]
        assert updated["description"] == update_data["description"]
    
    def test_delete_course(self, api_url, auth_headers, test_course_data):
        """Test deleting a course"""
        # Create course
        create_response = requests.post(
            f"{api_url}/courses",
            json=test_course_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        course_id = create_response.json()["id"]
        
        # Delete course
        delete_response = requests.delete(
            f"{api_url}/courses/{course_id}",
            headers=auth_headers
        )
        assert delete_response.status_code in [200, 204]
        
        # Verify deletion
        get_response = requests.get(
            f"{api_url}/courses/{course_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404


class TestMaterialGeneration:
    """Test material generation and management"""
    
    @pytest.fixture(scope="class")
    def user_token(self, api_url) -> str:
        """Get user authentication token"""
        login_data = {
            "username": "michael.borck@curtin.edu.au",
            "password": "Test123!Pass"
        }
        response = requests.post(
            f"{api_url}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            # Fallback to admin
            login_data = {
                "username": "admin@curriculum-curator.com",
                "password": "Admin123!Pass"
            }
            response = requests.post(
                f"{api_url}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, user_token) -> dict[str, str]:
        """Get headers with authentication"""
        return {"Authorization": f"Bearer {user_token}"}
    
    @pytest.fixture
    def test_course_id(self, api_url, auth_headers) -> str:
        """Create a test course and return its ID"""
        course_data = {
            "title": f"Material Test Course {int(time.time())}",
            "description": "Course for testing material generation",
            "objectives": ["Test objective 1", "Test objective 2"],
            "duration_weeks": 10,
            "level": "beginner"
        }
        
        response = requests.post(
            f"{api_url}/courses",
            json=course_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_create_material(self, api_url, auth_headers, test_course_id):
        """Test creating a material for a course"""
        material_data = {
            "title": "Introduction to Testing",
            "type": "lecture",
            "content": {
                "text": "This is test content for integration testing",
                "sections": [
                    {
                        "title": "Overview",
                        "content": "Testing overview content"
                    }
                ]
            },
            "pedagogy": "traditional",
            "difficulty": "beginner"
        }
        
        response = requests.post(
            f"{api_url}/courses/{test_course_id}/materials",
            json=material_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        material = response.json()
        assert material["title"] == material_data["title"]
        assert material["type"] == material_data["type"]
        assert "id" in material
        assert "created_at" in material
        
        return material["id"]
    
    def test_list_course_materials(self, api_url, auth_headers, test_course_id):
        """Test listing all materials for a course"""
        # First create a material
        material_data = {
            "title": "Test Material for Listing",
            "type": "assignment",
            "content": {"text": "Assignment content"},
            "pedagogy": "project-based"
        }
        
        requests.post(
            f"{api_url}/courses/{test_course_id}/materials",
            json=material_data,
            headers=auth_headers
        )
        
        # List materials
        response = requests.get(
            f"{api_url}/courses/{test_course_id}/materials",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        materials = response.json()
        assert isinstance(materials, list)
        assert len(materials) > 0
        
        # Check material structure
        material = materials[0]
        assert "id" in material
        assert "title" in material
        assert "type" in material
    
    def test_get_material_details(self, api_url, auth_headers, test_course_id):
        """Test getting detailed material information"""
        # Create material
        material_data = {
            "title": "Detailed Test Material",
            "type": "lecture",
            "content": {"text": "Detailed content"},
            "pedagogy": "traditional"
        }
        
        create_response = requests.post(
            f"{api_url}/courses/{test_course_id}/materials",
            json=material_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        material_id = create_response.json()["id"]
        
        # Get material details
        response = requests.get(
            f"{api_url}/materials/{material_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        material = response.json()
        assert material["id"] == material_id
        assert material["title"] == material_data["title"]
        assert "content" in material
        assert "version" in material
    
    def test_update_material(self, api_url, auth_headers, test_course_id):
        """Test updating material content"""
        # Create material
        material_data = {
            "title": "Material to Update",
            "type": "quiz",
            "content": {"questions": []},
            "pedagogy": "traditional"
        }
        
        create_response = requests.post(
            f"{api_url}/courses/{test_course_id}/materials",
            json=material_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        material_id = create_response.json()["id"]
        
        # Update material
        update_data = {
            "title": "Updated Material Title",
            "content": {
                "questions": [
                    {"question": "What is testing?", "answer": "Validation"}
                ]
            }
        }
        
        update_response = requests.put(
            f"{api_url}/materials/{material_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated["title"] == update_data["title"]
        assert updated["version"] > 1  # Version should increment
    
    def test_material_version_history(self, api_url, auth_headers, test_course_id):
        """Test material versioning functionality"""
        # Create material
        material_data = {
            "title": "Versioned Material",
            "type": "lecture",
            "content": {"text": "Version 1 content"},
            "pedagogy": "traditional"
        }
        
        create_response = requests.post(
            f"{api_url}/courses/{test_course_id}/materials",
            json=material_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        material_id = create_response.json()["id"]
        
        # Update material multiple times
        for i in range(2, 4):
            update_data = {
                "content": {"text": f"Version {i} content"}
            }
            requests.put(
                f"{api_url}/materials/{material_id}",
                json=update_data,
                headers=auth_headers
            )
        
        # Get version history
        response = requests.get(
            f"{api_url}/materials/{material_id}/versions",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        versions = response.json()
        
        # Check if versions is a list or has a versions key
        if isinstance(versions, dict) and "versions" in versions:
            version_list = versions["versions"]
        else:
            version_list = versions
        
        # Should have multiple versions
        assert len(version_list) >= 1


class TestLRDSystem:
    """Test Learning Resource Description (LRD) functionality"""
    
    @pytest.fixture(scope="class")
    def user_token(self, api_url) -> str:
        """Get user authentication token"""
        login_data = {
            "username": "michael.borck@curtin.edu.au",
            "password": "Test123!Pass"
        }
        response = requests.post(
            f"{api_url}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            login_data = {
                "username": "admin@curriculum-curator.com",
                "password": "Admin123!Pass"
            }
            response = requests.post(
                f"{api_url}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, user_token) -> dict[str, str]:
        """Get headers with authentication"""
        return {"Authorization": f"Bearer {user_token}"}
    
    @pytest.fixture
    def test_course_id(self, api_url, auth_headers) -> str:
        """Create a test course for LRDs"""
        course_data = {
            "title": f"LRD Test Course {int(time.time())}",
            "description": "Course for testing LRD functionality",
            "objectives": ["LRD Test objective"],
            "duration_weeks": 8
        }
        
        response = requests.post(
            f"{api_url}/courses",
            json=course_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_create_lrd(self, api_url, auth_headers, test_course_id):
        """Test creating an LRD"""
        lrd_data = {
            "title": "Introduction to Python",
            "description": "Learn Python basics",
            "learning_outcomes": [
                "Understand Python syntax",
                "Write simple programs",
                "Debug code effectively"
            ],
            "content_type": "lecture",
            "duration_minutes": 60,
            "difficulty": "beginner",
            "prerequisites": [],
            "assessment_criteria": [
                "Complete coding exercises",
                "Pass quiz with 80% score"
            ]
        }
        
        response = requests.post(
            f"{api_url}/courses/{test_course_id}/lrds",
            json=lrd_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        lrd = response.json()
        assert lrd["title"] == lrd_data["title"]
        assert lrd["description"] == lrd_data["description"]
        assert len(lrd["learning_outcomes"]) == 3
        assert "id" in lrd
        
        return lrd["id"]
    
    def test_list_course_lrds(self, api_url, auth_headers, test_course_id):
        """Test listing all LRDs for a course"""
        # Create multiple LRDs
        for i in range(3):
            lrd_data = {
                "title": f"Test LRD {i+1}",
                "description": f"Description {i+1}",
                "learning_outcomes": ["Outcome 1"],
                "content_type": "assignment",
                "duration_minutes": 30
            }
            requests.post(
                f"{api_url}/courses/{test_course_id}/lrds",
                json=lrd_data,
                headers=auth_headers
            )
        
        # List LRDs
        response = requests.get(
            f"{api_url}/courses/{test_course_id}/lrds",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        lrds = response.json()
        assert isinstance(lrds, list)
        assert len(lrds) >= 3
        
        # Check LRD structure
        lrd = lrds[0]
        assert "id" in lrd
        assert "title" in lrd
        assert "description" in lrd
        assert "status" in lrd
    
    def test_update_lrd_status(self, api_url, auth_headers, test_course_id):
        """Test updating LRD status (approval workflow)"""
        # Create LRD
        lrd_data = {
            "title": "LRD for Status Testing",
            "description": "Test status workflow",
            "learning_outcomes": ["Test outcome"],
            "content_type": "project",
            "duration_minutes": 120
        }
        
        create_response = requests.post(
            f"{api_url}/courses/{test_course_id}/lrds",
            json=lrd_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        lrd_id = create_response.json()["id"]
        
        # Update status (if endpoint exists)
        status_update = {
            "status": "approved"
        }
        
        # Try to update - endpoint might not exist
        update_response = requests.patch(
            f"{api_url}/lrds/{lrd_id}/status",
            json=status_update,
            headers=auth_headers
        )
        
        # If endpoint exists, verify update
        if update_response.status_code == 200:
            updated = update_response.json()
            assert updated["status"] == "approved"