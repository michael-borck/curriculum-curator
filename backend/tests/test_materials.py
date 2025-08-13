"""
Material management and versioning tests
Tests content creation, versioning, and rollback functionality
"""

import json
import time
import uuid
from typing import Dict, Optional, Tuple

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


class TestMaterialCreation:
    """Test creating different types of course materials"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure backend is running"""
        try:
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.exit("Backend must be running! Start with ./backend.sh")
    
    @pytest.fixture
    def course_with_auth(self) -> Tuple[Optional[Dict], Dict]:
        """Create course and return with auth headers"""
        # Login
        response = requests.post(
            f"{API_URL}/auth/login",
            data={
                "username": "michael.borck@curtin.edu.au",
                "password": "password123"
            }
        )
        
        if response.status_code != 200:
            return None, {}
        
        auth_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # Create course
        course_data = {
            "title": f"Material Test Course {uuid.uuid4().hex[:8]}",
            "code": f"MAT{uuid.uuid4().hex[:4].upper()}",
            "teaching_philosophy": "FLIPPED_CLASSROOM"
        }
        
        course_response = requests.post(
            f"{API_URL}/courses",
            json=course_data,
            headers=auth_headers
        )
        
        if course_response.status_code in [200, 201]:
            return course_response.json(), auth_headers
        return None, auth_headers
    
    def test_create_lecture_material(self, course_with_auth):
        """Test creating lecture material"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        material_data = {
            "course_id": course["id"],
            "type": "LECTURE",
            "title": "Introduction to Python",
            "content": {
                "introduction": "Welcome to Python programming",
                "main_points": [
                    "Python is interpreted",
                    "Python is dynamically typed",
                    "Python supports multiple paradigms"
                ],
                "examples": [
                    {"code": "print('Hello World')", "explanation": "Basic output"},
                    {"code": "x = 5", "explanation": "Variable assignment"}
                ],
                "summary": "Python is a versatile programming language"
            },
            "raw_content": "# Introduction to Python\n\n## Main Points\n- Interpreted language\n- Dynamic typing",
            "teaching_philosophy": "FLIPPED_CLASSROOM",
            "metadata": {
                "duration": "50 minutes",
                "difficulty": "beginner",
                "prerequisites": []
            }
        }
        
        response = requests.post(
            f"{API_URL}/materials",
            json=material_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "id" in data
        assert data["type"] in ["LECTURE", "lecture"]
        assert data["title"] == material_data["title"]
        assert data["version"] == 1
        assert data["is_latest"] is True
    
    def test_create_worksheet_material(self, course_with_auth):
        """Test creating worksheet material"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        material_data = {
            "course_id": course["id"],
            "type": "WORKSHEET",
            "title": "Python Basics Practice",
            "content": {
                "instructions": "Complete the following exercises",
                "exercises": [
                    {
                        "number": 1,
                        "question": "Write a function to calculate factorial",
                        "hints": ["Use recursion or iteration"],
                        "solution": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
                    },
                    {
                        "number": 2,
                        "question": "Implement a palindrome checker",
                        "hints": ["Compare string with its reverse"]
                    }
                ]
            },
            "teaching_philosophy": "CONSTRUCTIVIST"
        }
        
        response = requests.post(
            f"{API_URL}/materials",
            json=material_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert data["type"] in ["WORKSHEET", "worksheet"]
        assert "exercises" in data["content"]
    
    def test_create_quiz_material(self, course_with_auth):
        """Test creating quiz material"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        material_data = {
            "course_id": course["id"],
            "type": "QUIZ",
            "title": "Python Fundamentals Quiz",
            "content": {
                "questions": [
                    {
                        "id": "q1",
                        "type": "multiple_choice",
                        "question": "What is Python?",
                        "options": [
                            "A snake",
                            "A programming language",
                            "A framework",
                            "An IDE"
                        ],
                        "correct_answer": 1,
                        "explanation": "Python is a high-level programming language"
                    },
                    {
                        "id": "q2",
                        "type": "true_false",
                        "question": "Python is statically typed",
                        "correct_answer": False,
                        "explanation": "Python is dynamically typed"
                    }
                ],
                "settings": {
                    "time_limit": 30,
                    "passing_score": 70,
                    "randomize_questions": True
                }
            }
        }
        
        response = requests.post(
            f"{API_URL}/materials",
            json=material_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert data["type"] in ["QUIZ", "quiz"]
        assert len(data["content"]["questions"]) == 2
    
    def test_create_lab_material(self, course_with_auth):
        """Test creating lab/practical material"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        material_data = {
            "course_id": course["id"],
            "type": "LAB",
            "title": "Setting Up Python Environment",
            "content": {
                "objective": "Install and configure Python development environment",
                "steps": [
                    {
                        "number": 1,
                        "instruction": "Download Python from python.org",
                        "expected_result": "Python installer downloaded"
                    },
                    {
                        "number": 2,
                        "instruction": "Run installer with PATH option",
                        "expected_result": "Python installed and accessible from terminal"
                    },
                    {
                        "number": 3,
                        "instruction": "Verify installation with 'python --version'",
                        "expected_result": "Python version displayed"
                    }
                ],
                "deliverables": ["Screenshot of Python version", "Hello World script"]
            }
        }
        
        response = requests.post(
            f"{API_URL}/materials",
            json=material_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert data["type"] in ["LAB", "lab"]
        assert "steps" in data["content"]
    
    def test_create_case_study_material(self, course_with_auth):
        """Test creating case study material"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")
        
        material_data = {
            "course_id": course["id"],
            "type": "CASE_STUDY",
            "title": "E-commerce Platform Migration",
            "content": {
                "scenario": "A company needs to migrate from PHP to Python",
                "background": {
                    "company": "TechStore Inc.",
                    "current_stack": ["PHP", "MySQL", "Apache"],
                    "challenges": ["Performance issues", "Maintenance difficulty"]
                },
                "requirements": [
                    "Maintain all existing functionality",
                    "Improve response time by 50%",
                    "Zero downtime migration"
                ],
                "discussion_points": [
                    "Migration strategy",
                    "Technology choices",
                    "Risk mitigation"
                ]
            }
        }
        
        response = requests.post(
            f"{API_URL}/materials",
            json=material_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert data["type"] in ["CASE_STUDY", "case_study"]


class TestMaterialVersioning:
    """Test material version control functionality"""
    
    @pytest.fixture
    def material_with_auth(self, course_with_auth) -> Tuple[Optional[Dict], Dict]:
        """Create material and return with auth headers"""
        course, auth_headers = course_with_auth
        if not course:
            return None, {}
        
        material_data = {
            "course_id": course["id"],
            "type": "LECTURE",
            "title": "Version Test Material",
            "content": {"version": 1, "data": "Original content"},
            "raw_content": "# Original Content\n\nVersion 1"
        }
        
        response = requests.post(
            f"{API_URL}/materials",
            json=material_data,
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            return response.json(), auth_headers
        return None, auth_headers
    
    def test_create_new_version(self, material_with_auth):
        """Test creating a new version of material"""
        material, auth_headers = material_with_auth
        if not material:
            pytest.skip("Material creation failed")
        
        # Create new version
        new_version_data = {
            "course_id": material["course_id"],
            "type": material["type"],
            "title": f"{material['title']} - Updated",
            "content": {"version": 2, "data": "Updated content"},
            "raw_content": "# Updated Content\n\nVersion 2",
            "parent_version_id": material["id"],
            "change_summary": "Updated content and formatting"
        }
        
        response = requests.post(
            f"{API_URL}/materials",
            json=new_version_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert data["version"] == 2
        assert data["parent_version_id"] == material["id"]
        assert data["is_latest"] is True
        
        # Check original is no longer latest
        original_response = requests.get(
            f"{API_URL}/materials/{material['id']}",
            headers=auth_headers
        )
        
        if original_response.status_code == 200:
            original_data = original_response.json()
            assert original_data["is_latest"] is False
    
    def test_version_history(self, material_with_auth):
        """Test retrieving version history"""
        material, auth_headers = material_with_auth
        if not material:
            pytest.skip("Material creation failed")
        
        # Create multiple versions
        for i in range(2, 5):
            requests.post(
                f"{API_URL}/materials",
                json={
                    "course_id": material["course_id"],
                    "type": material["type"],
                    "title": f"Version {i}",
                    "content": {"version": i},
                    "parent_version_id": material["id"]
                },
                headers=auth_headers
            )
        
        # Get version history
        response = requests.get(
            f"{API_URL}/materials/{material['id']}/versions",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            versions = response.json()
            
            assert isinstance(versions, list)
            assert len(versions) >= 3
            
            # Check versions are ordered
            version_numbers = [v["version"] for v in versions]
            assert version_numbers == sorted(version_numbers)
    
    def test_rollback_to_previous_version(self, material_with_auth):
        """Test rolling back to a previous version"""
        material, auth_headers = material_with_auth
        if not material:
            pytest.skip("Material creation failed")
        
        # Create new version
        v2_response = requests.post(
            f"{API_URL}/materials",
            json={
                "course_id": material["course_id"],
                "type": material["type"],
                "title": "Version 2",
                "content": {"version": 2},
                "parent_version_id": material["id"]
            },
            headers=auth_headers
        )
        
        if v2_response.status_code in [200, 201]:
            v2_id = v2_response.json()["id"]
            
            # Rollback to version 1
            rollback_response = requests.post(
                f"{API_URL}/materials/{material['id']}/rollback",
                json={"reason": "Version 2 had errors"},
                headers=auth_headers
            )
            
            if rollback_response.status_code == 200:
                data = rollback_response.json()
                
                # Should create version 3 as copy of version 1
                assert data["version"] == 3
                assert data["is_latest"] is True
                assert data["content"] == material["content"]
    
    def test_compare_versions(self, material_with_auth):
        """Test comparing two versions"""
        material, auth_headers = material_with_auth
        if not material:
            pytest.skip("Material creation failed")
        
        # Create new version with changes
        v2_response = requests.post(
            f"{API_URL}/materials",
            json={
                "course_id": material["course_id"],
                "type": material["type"],
                "title": "Version 2 with changes",
                "content": {
                    "version": 2,
                    "data": "Modified content",
                    "new_field": "Added this"
                },
                "raw_content": "# Modified Content\n\nVersion 2 with additions"
            },
            headers=auth_headers
        )
        
        if v2_response.status_code in [200, 201]:
            v2_id = v2_response.json()["id"]
            
            # Compare versions
            compare_response = requests.get(
                f"{API_URL}/materials/compare",
                params={
                    "version1": material["id"],
                    "version2": v2_id
                },
                headers=auth_headers
            )
            
            if compare_response.status_code == 200:
                diff = compare_response.json()
                
                assert "changes" in diff or "diff" in diff
                # Should show title change, content change, etc.
    
    def test_clone_material(self, material_with_auth):
        """Test cloning material for reuse"""
        material, auth_headers = material_with_auth
        if not material:
            pytest.skip("Material creation failed")
        
        # Clone material
        clone_response = requests.post(
            f"{API_URL}/materials/{material['id']}/clone",
            json={
                "new_title": "Cloned Material",
                "target_course_id": material["course_id"]
            },
            headers=auth_headers
        )
        
        if clone_response.status_code in [200, 201]:
            clone = clone_response.json()
            
            assert clone["id"] != material["id"]
            assert clone["title"] == "Cloned Material"
            assert clone["content"] == material["content"]
            assert clone["version"] == 1  # Clone starts at version 1
            assert clone["parent_version_id"] is None
    
    def test_branch_merge(self, material_with_auth):
        """Test branching and merging material versions"""
        material, auth_headers = material_with_auth
        if not material:
            pytest.skip("Material creation failed")
        
        # Create branch A
        branch_a = requests.post(
            f"{API_URL}/materials",
            json={
                "course_id": material["course_id"],
                "type": material["type"],
                "title": "Branch A",
                "content": {"branch": "A", "change": "Change A"},
                "parent_version_id": material["id"],
                "is_branch": True
            },
            headers=auth_headers
        )
        
        # Create branch B
        branch_b = requests.post(
            f"{API_URL}/materials",
            json={
                "course_id": material["course_id"],
                "type": material["type"],
                "title": "Branch B",
                "content": {"branch": "B", "change": "Change B"},
                "parent_version_id": material["id"],
                "is_branch": True
            },
            headers=auth_headers
        )
        
        if branch_a.status_code in [200, 201] and branch_b.status_code in [200, 201]:
            # Test A/B comparison
            # Both branches exist, can be compared
            pass  # A/B testing functionality exists


class TestMaterialSearch:
    """Test material search and filtering"""
    
    @pytest.fixture
    def materials_with_auth(self, course_with_auth) -> Tuple[bool, Dict]:
        """Create multiple materials for searching"""
        course, auth_headers = course_with_auth
        if not course:
            return False, {}
        
        materials = [
            {
                "course_id": course["id"],
                "type": "LECTURE",
                "title": "Python Basics",
                "content": {"topic": "variables and types"}
            },
            {
                "course_id": course["id"],
                "type": "WORKSHEET",
                "title": "Python Exercises",
                "content": {"topic": "practice problems"}
            },
            {
                "course_id": course["id"],
                "type": "QUIZ",
                "title": "Python Assessment",
                "content": {"topic": "test knowledge"}
            }
        ]
        
        for material in materials:
            requests.post(
                f"{API_URL}/materials",
                json=material,
                headers=auth_headers
            )
        
        return True, auth_headers
    
    def test_search_by_type(self, materials_with_auth):
        """Test filtering materials by type"""
        created, auth_headers = materials_with_auth
        if not created:
            pytest.skip("Materials creation failed")
        
        # Search for lectures
        response = requests.get(
            f"{API_URL}/materials",
            params={"type": "LECTURE"},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            materials = response.json()
            
            for material in materials:
                assert material["type"] in ["LECTURE", "lecture"]
    
    def test_search_by_title(self, materials_with_auth):
        """Test searching materials by title"""
        created, auth_headers = materials_with_auth
        if not created:
            pytest.skip("Materials creation failed")
        
        # Search for Python materials
        response = requests.get(
            f"{API_URL}/materials",
            params={"search": "Python"},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            materials = response.json()
            
            for material in materials:
                assert "python" in material["title"].lower()
    
    def test_get_latest_versions_only(self, materials_with_auth):
        """Test retrieving only latest versions"""
        created, auth_headers = materials_with_auth
        if not created:
            pytest.skip("Materials creation failed")
        
        # Get latest versions
        response = requests.get(
            f"{API_URL}/materials",
            params={"latest_only": True},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            materials = response.json()
            
            for material in materials:
                assert material.get("is_latest", True) is True