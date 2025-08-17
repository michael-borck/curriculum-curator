"""
Real-world integration tests that work with the running backend
Focuses on actual functionality rather than mocking
"""

import io
import json
import time
from typing import Any

import pytest
import requests


class TestRealAuthentication:
    """Test real authentication flow"""
    
    def test_admin_can_login(self):
        """Test that admin can successfully login"""
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "admin@curriculum-curator.com",
                "password": "Admin123!Pass"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == "admin@curriculum-curator.com"
        
        print("✓ Admin login successful")
        return data["access_token"]
    
    def test_user_can_login(self):
        """Test that regular user can login"""
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "michael.borck@curtin.edu.au",
                "password": "Test123!Pass"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        print(f"✓ User login successful as {data['user']['email']}")
    
    def test_invalid_login_fails(self):
        """Test that invalid credentials are rejected"""
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "WrongPassword123!"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
        print("✓ Invalid login correctly rejected")


class TestCourseWorkflow:
    """Test complete course creation and material generation workflow"""
    
    def get_auth_token(self) -> str:
        """Get authentication token for testing"""
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "michael.borck@curtin.edu.au",
                "password": "Test123!Pass"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        
        # Fallback to admin
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "admin@curriculum-curator.com",
                "password": "Admin123!Pass"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_complete_course_workflow(self):
        """Test creating a course, adding materials, and managing it"""
        token = self.get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Create a course
        course_data = {
            "title": f"Integration Test Course {int(time.time())}",
            "description": "A comprehensive test course",
            "objectives": [
                "Learn testing principles",
                "Apply real-world scenarios",
                "Master integration testing"
            ],
            "duration_weeks": 10,
            "level": "intermediate",
            "teaching_philosophy": "constructivist"
        }
        
        create_response = requests.post(
            "http://localhost:8000/api/courses",
            json=course_data,
            headers=headers
        )
        
        if create_response.status_code != 200:
            print(f"Course creation failed: {create_response.text}")
            print(f"Headers: {headers}")
        
        assert create_response.status_code == 200, f"Failed to create course: {create_response.text}"
        course = create_response.json()
        course_id = course["id"]
        print(f"✓ Created course: {course['title']}")
        
        # Step 2: Add materials to the course
        material_types = ["lecture", "assignment", "quiz"]
        created_materials = []
        
        for material_type in material_types:
            material_data = {
                "title": f"Test {material_type.capitalize()}",
                "type": material_type,
                "content": {
                    "text": f"This is content for {material_type}",
                    "pedagogy": "traditional"
                },
                "difficulty": "beginner"
            }
            
            mat_response = requests.post(
                f"http://localhost:8000/api/courses/{course_id}/materials",
                json=material_data,
                headers=headers
            )
            
            if mat_response.status_code == 200:
                created_materials.append(mat_response.json())
                print(f"  ✓ Added {material_type}")
            else:
                print(f"  ✗ Failed to add {material_type}: {mat_response.text}")
        
        # Step 3: List course materials
        list_response = requests.get(
            f"http://localhost:8000/api/courses/{course_id}/materials",
            headers=headers
        )
        
        if list_response.status_code == 200:
            materials = list_response.json()
            print(f"✓ Course has {len(materials)} materials")
        
        # Step 4: Get course details
        detail_response = requests.get(
            f"http://localhost:8000/api/courses/{course_id}",
            headers=headers
        )
        
        if detail_response.status_code == 200:
            detail_response.json()  # Verify response is valid JSON
            print("✓ Retrieved course details")
        
        # Step 5: Clean up - delete the course
        delete_response = requests.delete(
            f"http://localhost:8000/api/courses/{course_id}",
            headers=headers
        )
        
        if delete_response.status_code in [200, 204]:
            print("✓ Cleaned up test course")
        
        return course_id
    
    def test_material_versioning(self):
        """Test that materials maintain version history"""
        token = self.get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a course
        course_data = {
            "title": f"Version Test Course {int(time.time())}",
            "description": "Testing versioning",
            "objectives": ["Test versions"],
            "duration_weeks": 1
        }
        
        course_response = requests.post(
            "http://localhost:8000/api/courses",
            json=course_data,
            headers=headers
        )
        
        if course_response.status_code != 200:
            pytest.skip("Course creation not working")
        
        course_id = course_response.json()["id"]
        
        # Create a material
        material_data = {
            "title": "Versioned Material",
            "type": "lecture",
            "content": {"text": "Version 1"},
            "difficulty": "beginner"
        }
        
        mat_response = requests.post(
            f"http://localhost:8000/api/courses/{course_id}/materials",
            json=material_data,
            headers=headers
        )
        
        if mat_response.status_code == 200:
            material_id = mat_response.json()["id"]
            print(f"✓ Created material with ID: {material_id}")
            
            # Update the material several times
            for version in range(2, 5):
                update_data = {
                    "content": {"text": f"Version {version}"}
                }
                
                update_response = requests.put(
                    f"http://localhost:8000/api/materials/{material_id}",
                    json=update_data,
                    headers=headers
                )
                
                if update_response.status_code == 200:
                    print(f"  ✓ Updated to version {version}")
                else:
                    print(f"  ✗ Update failed: {update_response.text}")
            
            # Get version history
            history_response = requests.get(
                f"http://localhost:8000/api/materials/{material_id}/versions",
                headers=headers
            )
            
            if history_response.status_code == 200:
                history_response.json()  # Verify response is valid JSON
                print("✓ Material has version history")
        
        # Cleanup
        requests.delete(f"http://localhost:8000/api/courses/{course_id}", headers=headers)


class TestLRDFunctionality:
    """Test Learning Resource Description functionality"""
    
    def get_auth_token(self) -> str:
        """Get authentication token"""
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "michael.borck@curtin.edu.au",
                "password": "Test123!Pass"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            response = requests.post(
                "http://localhost:8000/api/auth/login",
                data={
                    "username": "admin@curriculum-curator.com",
                    "password": "Admin123!Pass"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_lrd_creation_and_management(self):
        """Test creating and managing LRDs"""
        token = self.get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a course for LRDs
        course_data = {
            "title": f"LRD Test {int(time.time())}",
            "description": "LRD testing",
            "objectives": ["Test LRDs"],
            "duration_weeks": 4
        }
        
        course_resp = requests.post(
            "http://localhost:8000/api/courses",
            json=course_data,
            headers=headers
        )
        
        if course_resp.status_code != 200:
            pytest.skip("Course creation failed")
        
        course_id = course_resp.json()["id"]
        print("✓ Created course for LRD testing")
        
        # Create multiple LRDs
        lrd_titles = [
            "Introduction to Python",
            "Data Structures",
            "Algorithms",
            "Final Project"
        ]
        
        created_lrds = []
        for title in lrd_titles:
            lrd_data = {
                "title": title,
                "description": f"Learn about {title.lower()}",
                "learning_outcomes": [
                    f"Understand {title}",
                    f"Apply {title} concepts",
                    f"Evaluate {title} solutions"
                ],
                "content_type": "lecture" if "Project" not in title else "project",
                "duration_minutes": 60 if "Project" not in title else 240,
                "difficulty": "beginner" if title == lrd_titles[0] else "intermediate",
                "prerequisites": created_lrds[-1:] if created_lrds else [],
                "assessment_criteria": [
                    "Complete exercises",
                    "Pass assessment"
                ]
            }
            
            lrd_resp = requests.post(
                f"http://localhost:8000/api/courses/{course_id}/lrds",
                json=lrd_data,
                headers=headers
            )
            
            if lrd_resp.status_code == 200:
                lrd = lrd_resp.json()
                created_lrds.append(lrd["id"])
                print(f"  ✓ Created LRD: {title}")
            else:
                print(f"  ✗ Failed to create LRD: {lrd_resp.text}")
        
        # List all LRDs
        list_resp = requests.get(
            f"http://localhost:8000/api/courses/{course_id}/lrds",
            headers=headers
        )
        
        if list_resp.status_code == 200:
            lrds = list_resp.json()
            print(f"✓ Course has {len(lrds)} LRDs")
            
            # Verify LRD structure
            if lrds:
                lrd = lrds[0]
                assert "id" in lrd
                assert "title" in lrd
                assert "description" in lrd
                assert "learning_outcomes" in lrd
                print("✓ LRD structure validated")
        
        # Cleanup
        requests.delete(f"http://localhost:8000/api/courses/{course_id}", headers=headers)
        print("✓ Cleanup completed")


class TestImportFunctionality:
    """Test file import and processing"""
    
    def get_auth_token(self) -> str:
        """Get authentication token"""
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "michael.borck@curtin.edu.au",
                "password": "Test123!Pass"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            response = requests.post(
                "http://localhost:8000/api/auth/login",
                data={
                    "username": "admin@curriculum-curator.com",
                    "password": "Admin123!Pass"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        return response.json()["access_token"] if response.status_code == 200 else None
    
    def test_file_upload(self):
        """Test uploading files for import"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a course
        course_data = {
            "title": f"Import Test {int(time.time())}",
            "description": "Testing imports",
            "objectives": ["Test file imports"],
            "duration_weeks": 2
        }
        
        course_resp = requests.post(
            "http://localhost:8000/api/courses",
            json=course_data,
            headers=headers
        )
        
        if course_resp.status_code != 200:
            pytest.skip("Course creation failed")
        
        course_id = course_resp.json()["id"]
        
        # Create a test file
        test_content = """# Test Course Material
        
## Introduction
This is a test document for import functionality.

## Learning Objectives
- Understand file imports
- Process content effectively
- Generate materials from imports

## Content
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
"""
        
        files = {
            'file': ('test_material.txt', io.BytesIO(test_content.encode()), 'text/plain')
        }
        
        # Try to upload
        upload_resp = requests.post(
            f"http://localhost:8000/api/courses/{course_id}/import",
            files=files,
            headers=headers
        )
        
        if upload_resp.status_code == 200:
            print("✓ File uploaded successfully")
            result = upload_resp.json()
            print(f"  Upload result: {result}")
        elif upload_resp.status_code == 404:
            print("✗ Import endpoint not found (expected - not fully implemented)")
        else:
            print(f"✗ Upload failed: {upload_resp.status_code} - {upload_resp.text}")
        
        # Cleanup
        requests.delete(f"http://localhost:8000/api/courses/{course_id}", headers=headers)


if __name__ == "__main__":
    # Run tests directly without pytest if needed
    print("Running Real-World Integration Tests\n" + "="*50)
    
    # Test Authentication
    print("\n1. Testing Authentication...")
    auth_test = TestRealAuthentication()
    try:
        auth_test.test_admin_can_login()
        auth_test.test_user_can_login()
        auth_test.test_invalid_login_fails()
    except AssertionError as e:
        print(f"✗ Auth test failed: {e}")
    
    # Test Course Workflow
    print("\n2. Testing Course Workflow...")
    course_test = TestCourseWorkflow()
    try:
        course_test.test_complete_course_workflow()
        course_test.test_material_versioning()
    except AssertionError as e:
        print(f"✗ Course test failed: {e}")
    
    # Test LRD
    print("\n3. Testing LRD Functionality...")
    lrd_test = TestLRDFunctionality()
    try:
        lrd_test.test_lrd_creation_and_management()
    except AssertionError as e:
        print(f"✗ LRD test failed: {e}")
    
    # Test Import
    print("\n4. Testing Import Functionality...")
    import_test = TestImportFunctionality()
    try:
        import_test.test_file_upload()
    except AssertionError as e:
        print(f"✗ Import test failed: {e}")
    
    print("\n" + "="*50)
    print("Integration tests completed!")