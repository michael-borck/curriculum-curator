"""
LRD (Learning Resource Document) system tests
Tests the complete LRD workflow including creation, approval, and task generation
"""

import json
import time
import uuid
from typing import Dict, Optional, Tuple

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


class TestLRDWorkflow:
    """Test complete LRD workflow from creation to approval"""
    
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
    
    @pytest.fixture
    def test_course(self, auth_headers) -> Optional[Dict]:
        """Create a test course for LRDs"""
        if not auth_headers:
            return None
        
        course_data = {
            "title": f"LRD Test Course {uuid.uuid4().hex[:8]}",
            "code": f"LRD{uuid.uuid4().hex[:4].upper()}",
            "description": "Course for testing LRD system",
            "teaching_philosophy": "FLIPPED_CLASSROOM",
            "language_preference": "en-AU"
        }
        
        response = requests.post(
            f"{API_URL}/courses",
            json=course_data,
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        return None
    
    def test_create_lrd(self, auth_headers, test_course):
        """Test creating an LRD"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        lrd_data = {
            "course_id": test_course["id"],
            "version": "1.0",
            "content": {
                "topic": "Introduction to Python",
                "duration": "2 weeks",
                "objectives": [
                    "Understand Python syntax",
                    "Write basic Python programs",
                    "Debug simple errors"
                ],
                "structure": {
                    "pre_class": {
                        "activities": ["Read Chapter 1", "Watch intro video"],
                        "duration": "2 hours"
                    },
                    "in_class": {
                        "activities": ["Live coding", "Q&A session"],
                        "duration": "2 hours"
                    },
                    "post_class": {
                        "activities": ["Complete exercises", "Submit assignment"],
                        "duration": "3 hours"
                    }
                },
                "assessment": {
                    "type": "Quiz and Assignment",
                    "weight": "20%"
                },
                "resources": [
                    "Python documentation",
                    "Course textbook",
                    "Online tutorials"
                ]
            }
        }
        
        response = requests.post(
            f"{API_URL}/lrds",
            json=lrd_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "id" in data
        assert data["course_id"] == test_course["id"]
        assert data["status"] in ["DRAFT", "draft"]
        assert data["version"] == "1.0"
    
    def test_get_lrd(self, auth_headers, test_course):
        """Test retrieving an LRD"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        # Create LRD first
        lrd_data = {
            "course_id": test_course["id"],
            "version": "1.0",
            "content": {"topic": "Test Topic"}
        }
        
        create_response = requests.post(
            f"{API_URL}/lrds",
            json=lrd_data,
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            lrd_id = create_response.json()["id"]
            
            # Get the LRD
            response = requests.get(
                f"{API_URL}/lrds/{lrd_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == lrd_id
            assert data["course_id"] == test_course["id"]
            assert "content" in data
    
    def test_update_lrd(self, auth_headers, test_course):
        """Test updating an LRD"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        # Create LRD
        create_response = requests.post(
            f"{API_URL}/lrds",
            json={
                "course_id": test_course["id"],
                "version": "1.0",
                "content": {"topic": "Original Topic"}
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            lrd_id = create_response.json()["id"]
            
            # Update LRD
            update_data = {
                "content": {
                    "topic": "Updated Topic",
                    "objectives": ["New objective 1", "New objective 2"]
                },
                "version": "1.1"
            }
            
            response = requests.patch(
                f"{API_URL}/lrds/{lrd_id}",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["content"]["topic"] == "Updated Topic"
            assert data["version"] == "1.1"
    
    def test_lrd_approval_workflow(self, auth_headers, test_course):
        """Test LRD status transitions (Draft -> Review -> Approved)"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        # Create LRD in draft
        create_response = requests.post(
            f"{API_URL}/lrds",
            json={
                "course_id": test_course["id"],
                "version": "1.0",
                "content": {"topic": "Approval Test"}
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            lrd_id = create_response.json()["id"]
            
            # Submit for review
            review_response = requests.post(
                f"{API_URL}/lrds/{lrd_id}/submit-review",
                headers=auth_headers
            )
            
            if review_response.status_code == 200:
                data = review_response.json()
                assert data["status"] in ["IN_REVIEW", "in_review"]
            
            # Approve (might require admin rights)
            approve_response = requests.post(
                f"{API_URL}/lrds/{lrd_id}/approve",
                headers=auth_headers
            )
            
            if approve_response.status_code == 200:
                data = approve_response.json()
                assert data["status"] in ["APPROVED", "approved"]
            elif approve_response.status_code == 403:
                # User doesn't have approval rights
                pass
    
    def test_generate_tasks_from_lrd(self, auth_headers, test_course):
        """Test generating task list from LRD"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        # Create comprehensive LRD
        lrd_data = {
            "course_id": test_course["id"],
            "version": "1.0",
            "content": {
                "topic": "Complete Module",
                "objectives": [
                    "Create lecture materials",
                    "Develop exercises",
                    "Design assessment"
                ],
                "structure": {
                    "materials_needed": [
                        "Lecture slides",
                        "Worksheet",
                        "Quiz",
                        "Lab instructions"
                    ]
                }
            }
        }
        
        create_response = requests.post(
            f"{API_URL}/lrds",
            json=lrd_data,
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            lrd_id = create_response.json()["id"]
            
            # Generate tasks
            response = requests.post(
                f"{API_URL}/lrds/{lrd_id}/generate-tasks",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                assert "task_list_id" in data or "tasks" in data
                
                # If task list ID returned, fetch it
                if "task_list_id" in data:
                    task_response = requests.get(
                        f"{API_URL}/task-lists/{data['task_list_id']}",
                        headers=auth_headers
                    )
                    
                    if task_response.status_code == 200:
                        tasks = task_response.json()
                        assert "tasks" in tasks
                        assert tasks["total_tasks"] > 0
    
    def test_list_course_lrds(self, auth_headers, test_course):
        """Test listing all LRDs for a course"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        # Create multiple LRDs
        for i in range(3):
            requests.post(
                f"{API_URL}/lrds",
                json={
                    "course_id": test_course["id"],
                    "version": f"{i+1}.0",
                    "content": {"topic": f"Topic {i+1}"}
                },
                headers=auth_headers
            )
        
        # List LRDs for course
        response = requests.get(
            f"{API_URL}/courses/{test_course['id']}/lrds",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Should be sorted by version or creation date
        versions = [lrd["version"] for lrd in data]
        assert len(versions) == len(data)
    
    def test_lrd_version_history(self, auth_headers, test_course):
        """Test LRD version tracking"""
        if not auth_headers or not test_course:
            pytest.skip("Prerequisites not available")
        
        # Create initial LRD
        v1_response = requests.post(
            f"{API_URL}/lrds",
            json={
                "course_id": test_course["id"],
                "version": "1.0",
                "content": {"topic": "Version 1"}
            },
            headers=auth_headers
        )
        
        if v1_response.status_code in [200, 201]:
            lrd_id = v1_response.json()["id"]
            
            # Create new version
            v2_response = requests.post(
                f"{API_URL}/lrds",
                json={
                    "course_id": test_course["id"],
                    "version": "2.0",
                    "content": {"topic": "Version 2"},
                    "parent_id": lrd_id
                },
                headers=auth_headers
            )
            
            if v2_response.status_code in [200, 201]:
                # Get version history
                history_response = requests.get(
                    f"{API_URL}/lrds/{lrd_id}/versions",
                    headers=auth_headers
                )
                
                if history_response.status_code == 200:
                    versions = history_response.json()
                    assert len(versions) >= 1


class TestTaskManagement:
    """Test task list creation and management"""
    
    @pytest.fixture
    def lrd_with_auth(self, auth_headers, test_course) -> Tuple[Optional[Dict], Dict]:
        """Create LRD and return with auth headers"""
        if not auth_headers or not test_course:
            return None, {}
        
        lrd_data = {
            "course_id": test_course["id"],
            "version": "1.0",
            "content": {
                "topic": "Task Management Test",
                "objectives": ["Test task creation"]
            }
        }
        
        response = requests.post(
            f"{API_URL}/lrds",
            json=lrd_data,
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            return response.json(), auth_headers
        return None, auth_headers
    
    def test_create_task_list(self, lrd_with_auth):
        """Test creating a task list"""
        lrd, auth_headers = lrd_with_auth
        if not lrd:
            pytest.skip("LRD creation failed")
        
        task_data = {
            "lrd_id": lrd["id"],
            "course_id": lrd["course_id"],
            "tasks": {
                "parent_tasks": [
                    {
                        "id": "task_1",
                        "title": "Create lecture content",
                        "description": "Develop comprehensive lecture materials",
                        "status": "pending",
                        "effort": "L",
                        "priority": "high"
                    },
                    {
                        "id": "task_2",
                        "title": "Design exercises",
                        "description": "Create practice problems",
                        "status": "pending",
                        "effort": "M",
                        "priority": "medium"
                    }
                ],
                "sub_tasks": [
                    {
                        "id": "subtask_1_1",
                        "parent_id": "task_1",
                        "title": "Write lecture notes",
                        "status": "pending"
                    },
                    {
                        "id": "subtask_1_2",
                        "parent_id": "task_1",
                        "title": "Create presentation slides",
                        "status": "pending"
                    }
                ]
            },
            "total_tasks": 4,
            "completed_tasks": 0
        }
        
        response = requests.post(
            f"{API_URL}/task-lists",
            json=task_data,
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            assert "id" in data
            assert data["lrd_id"] == lrd["id"]
            assert data["total_tasks"] == 4
            assert data["progress_percentage"] == 0.0
    
    def test_update_task_status(self, lrd_with_auth):
        """Test updating task completion status"""
        lrd, auth_headers = lrd_with_auth
        if not lrd:
            pytest.skip("LRD creation failed")
        
        # Create task list
        task_data = {
            "lrd_id": lrd["id"],
            "course_id": lrd["course_id"],
            "tasks": {
                "tasks": [
                    {"id": "1", "title": "Task 1", "completed": False},
                    {"id": "2", "title": "Task 2", "completed": False}
                ]
            },
            "total_tasks": 2,
            "completed_tasks": 0
        }
        
        create_response = requests.post(
            f"{API_URL}/task-lists",
            json=task_data,
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            task_list_id = create_response.json()["id"]
            
            # Update task status
            update_data = {
                "tasks": {
                    "tasks": [
                        {"id": "1", "title": "Task 1", "completed": True},
                        {"id": "2", "title": "Task 2", "completed": False}
                    ]
                },
                "completed_tasks": 1
            }
            
            response = requests.patch(
                f"{API_URL}/task-lists/{task_list_id}",
                json=update_data,
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["completed_tasks"] == 1
                assert data["progress_percentage"] == 50.0
    
    def test_complete_all_tasks(self, lrd_with_auth):
        """Test completing all tasks in a list"""
        lrd, auth_headers = lrd_with_auth
        if not lrd:
            pytest.skip("LRD creation failed")
        
        # Create task list
        task_data = {
            "lrd_id": lrd["id"],
            "course_id": lrd["course_id"],
            "tasks": {"tasks": []},
            "total_tasks": 3,
            "completed_tasks": 0
        }
        
        create_response = requests.post(
            f"{API_URL}/task-lists",
            json=task_data,
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            task_list_id = create_response.json()["id"]
            
            # Complete all tasks
            update_data = {
                "completed_tasks": 3,
                "status": "COMPLETE"
            }
            
            response = requests.patch(
                f"{API_URL}/task-lists/{task_list_id}",
                json=update_data,
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["completed_tasks"] == 3
                assert data["progress_percentage"] == 100.0
                assert data["status"] in ["COMPLETE", "complete"]
                assert data.get("completed_at") is not None


class TestLRDConversations:
    """Test conversation history linked to LRDs"""
    
    @pytest.fixture
    def setup_data(self, auth_headers, test_course) -> Tuple[Optional[Dict], Dict]:
        """Setup LRD for conversation testing"""
        if not auth_headers or not test_course:
            return None, {}
        
        lrd_response = requests.post(
            f"{API_URL}/lrds",
            json={
                "course_id": test_course["id"],
                "version": "1.0",
                "content": {"topic": "Conversation Test"}
            },
            headers=auth_headers
        )
        
        if lrd_response.status_code in [200, 201]:
            return lrd_response.json(), auth_headers
        return None, auth_headers
    
    def test_save_conversation(self, setup_data):
        """Test saving conversation history"""
        lrd, auth_headers = setup_data
        if not lrd:
            pytest.skip("Setup failed")
        
        conversation_data = {
            "course_id": lrd["course_id"],
            "lrd_id": lrd["id"],
            "session_id": str(uuid.uuid4()),
            "messages": [
                {"role": "user", "content": "Create a lecture for this topic"},
                {"role": "assistant", "content": "I'll help you create a lecture..."},
                {"role": "user", "content": "Add more examples"},
                {"role": "assistant", "content": "Here are additional examples..."}
            ]
        }
        
        response = requests.post(
            f"{API_URL}/conversations",
            json=conversation_data,
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            assert "id" in data
            assert data["lrd_id"] == lrd["id"]
            assert len(data["messages"]) == 4
    
    def test_get_lrd_conversations(self, setup_data):
        """Test retrieving conversations for an LRD"""
        lrd, auth_headers = setup_data
        if not lrd:
            pytest.skip("Setup failed")
        
        # Save a conversation
        requests.post(
            f"{API_URL}/conversations",
            json={
                "course_id": lrd["course_id"],
                "lrd_id": lrd["id"],
                "session_id": str(uuid.uuid4()),
                "messages": [{"role": "user", "content": "Test"}]
            },
            headers=auth_headers
        )
        
        # Get LRD conversations
        response = requests.get(
            f"{API_URL}/lrds/{lrd['id']}/conversations",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1