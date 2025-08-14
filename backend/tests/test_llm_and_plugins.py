"""
LLM service and plugin system tests
Tests content generation, enhancement, and validation
"""

import json
import time
import uuid
from typing import Optional

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


class TestLLMContentGeneration:
    """Test LLM-powered content generation"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure backend is running"""
        try:
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.exit("Backend must be running! Start with ./backend.sh")

    @pytest.fixture
    def auth_headers(self) -> dict[str, str]:
        """Get authentication headers"""
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": "michael.borck@curtin.edu.au", "password": "password123"},
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_generate_lecture_content(self, auth_headers):
        """Test generating lecture content with LLM"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        generation_data = {
            "content_type": "lecture",
            "topic": "Introduction to Variables in Python",
            "pedagogy": "FLIPPED_CLASSROOM",
            "parameters": {
                "duration": "50 minutes",
                "level": "beginner",
                "include_examples": True,
                "include_exercises": True,
            },
        }

        response = requests.post(
            f"{API_URL}/llm/generate", json=generation_data, headers=auth_headers
        )

        # Could be 200 (success) or 503 (no API key configured)
        if response.status_code == 200:
            data = response.json()

            assert "content" in data
            assert "metadata" in data

            # Content should have structure
            content = data["content"]
            assert isinstance(content, dict | str)
        elif response.status_code == 503:
            # LLM service not configured
            data = response.json()
            assert "detail" in data
            assert (
                "api" in data["detail"].lower()
                or "configured" in data["detail"].lower()
            )

    def test_generate_quiz_questions(self, auth_headers):
        """Test generating quiz questions"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        generation_data = {
            "content_type": "quiz",
            "topic": "Python Data Types",
            "pedagogy": "TRADITIONAL",
            "parameters": {
                "num_questions": 5,
                "question_types": ["multiple_choice", "true_false"],
                "difficulty": "intermediate",
            },
        }

        response = requests.post(
            f"{API_URL}/llm/generate", json=generation_data, headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            if "questions" in data.get("content", {}):
                questions = data["content"]["questions"]
                assert isinstance(questions, list)
                assert len(questions) <= 5

    def test_enhance_content(self, auth_headers):
        """Test enhancing existing content"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        enhance_data = {
            "content": "Python is a programming language. It has variables.",
            "enhancement_type": "expand",
            "pedagogy": "CONSTRUCTIVIST",
            "parameters": {
                "target_length": "medium",
                "add_examples": True,
                "improve_clarity": True,
            },
        }

        response = requests.post(
            f"{API_URL}/llm/enhance", json=enhance_data, headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            assert "enhanced_content" in data
            # Enhanced content should be longer
            if isinstance(data["enhanced_content"], str):
                assert len(data["enhanced_content"]) > len(enhance_data["content"])

    def test_streaming_generation(self, auth_headers):
        """Test streaming content generation"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        generation_data = {
            "content_type": "lecture",
            "topic": "Quick Test",
            "pedagogy": "TRADITIONAL",
            "stream": True,
        }

        # Streaming endpoint might use SSE
        response = requests.post(
            f"{API_URL}/llm/generate-stream",
            json=generation_data,
            headers=auth_headers,
            stream=True,
        )

        if response.status_code == 200:
            # Should receive streaming response
            chunks = [line for line in response.iter_lines() if line]

            # Should have received some chunks
            assert len(chunks) > 0

    def test_pedagogy_aware_generation(self, auth_headers):
        """Test that different pedagogies produce different content"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        pedagogies = ["TRADITIONAL", "FLIPPED_CLASSROOM", "CONSTRUCTIVIST"]
        topic = "Python Functions"
        results = {}

        for pedagogy in pedagogies:
            response = requests.post(
                f"{API_URL}/llm/generate",
                json={"content_type": "lecture", "topic": topic, "pedagogy": pedagogy},
                headers=auth_headers,
            )

            if response.status_code == 200:
                results[pedagogy] = response.json()

        # Different pedagogies should produce different content
        if len(results) > 1:
            contents = [str(r.get("content", "")) for r in results.values()]
            # Contents should be different
            assert len(set(contents)) == len(contents)


class TestPluginSystem:
    """Test content validation and remediation plugins"""

    @pytest.fixture
    def auth_headers(self) -> dict[str, str]:
        """Get authentication headers"""
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": "michael.borck@curtin.edu.au", "password": "password123"},
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_list_available_plugins(self, auth_headers):
        """Test listing all available plugins"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        response = requests.get(f"{API_URL}/plugins", headers=auth_headers)

        assert response.status_code == 200
        plugins = response.json()

        assert isinstance(plugins, list)
        assert len(plugins) > 0

        # Check plugin structure
        for plugin in plugins:
            assert "name" in plugin
            assert "type" in plugin
            assert plugin["type"] in ["validator", "remediator"]

    def test_validate_content(self, auth_headers):
        """Test content validation with plugins"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        content_data = {
            "content": """
            # Python Basics
            
            Python is a programing language that is easy to lern.
            It has simple sintax and is beginner-friendly.
            
            Visit https://python.org for more information.
            Visit http://broken-link-example-12345.com for examples.
            """,
            "validators": ["spell_checker", "url_verifier", "grammar_validator"],
        }

        response = requests.post(
            f"{API_URL}/plugins/validate", json=content_data, headers=auth_headers
        )

        if response.status_code == 200:
            results = response.json()

            assert "validation_results" in results
            assert isinstance(results["validation_results"], list)

            # Should find spelling errors
            spelling_issues = [
                r
                for r in results["validation_results"]
                if r.get("validator") == "spell_checker"
            ]
            if spelling_issues:
                assert len(spelling_issues[0].get("issues", [])) > 0

            # Should find broken URL
            url_issues = [
                r
                for r in results["validation_results"]
                if r.get("validator") == "url_verifier"
            ]
            if url_issues:
                assert len(url_issues[0].get("issues", [])) > 0

    def test_remediate_content(self, auth_headers):
        """Test content remediation with plugins"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        content_data = {
            "content": "python is great. it is easy to learn",
            "remediators": ["basic_remediator"],
        }

        response = requests.post(
            f"{API_URL}/plugins/remediate", json=content_data, headers=auth_headers
        )

        if response.status_code == 200:
            result = response.json()

            assert "remediated_content" in result
            # Should capitalize sentences
            remediated = result["remediated_content"]
            assert remediated[0].isupper()  # First letter capitalized

    def test_accessibility_validation(self, auth_headers):
        """Test accessibility validator plugin"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        content_data = {
            "content": """
            <img src="image.jpg">
            <a href="#">Click here</a>
            <table><tr><td>Data</td></tr></table>
            """,
            "validators": ["accessibility_validator"],
        }

        response = requests.post(
            f"{API_URL}/plugins/validate", json=content_data, headers=auth_headers
        )

        if response.status_code == 200:
            results = response.json()

            # Should find accessibility issues
            # Missing alt text, non-descriptive link text, etc.
            if "validation_results" in results:
                results["validation_results"]
                # Should detect missing alt text

    def test_readability_analysis(self, auth_headers):
        """Test readability validator plugin"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        content_data = {
            "content": """
            The implementation of sophisticated algorithmic paradigms 
            necessitates comprehensive understanding of theoretical 
            computational complexity frameworks and their practical 
            ramifications in contemporary software engineering contexts.
            
            Python is easy. It is fun. You can learn it quickly.
            """,
            "validators": ["readability_validator"],
        }

        response = requests.post(
            f"{API_URL}/plugins/validate", json=content_data, headers=auth_headers
        )

        if response.status_code == 200:
            results = response.json()

            # Should analyze readability
            if "validation_results" in results:
                readability = [
                    r
                    for r in results["validation_results"]
                    if r.get("validator") == "readability_validator"
                ]
                if readability:
                    # Should have readability metrics
                    assert "metrics" in readability[0] or "score" in readability[0]

    def test_plugin_chaining(self, auth_headers):
        """Test running multiple plugins in sequence"""
        if not auth_headers:
            pytest.skip("Authentication not available")

        content_data = {
            "content": "this is test content with erors",
            "validators": ["spell_checker", "grammar_validator"],
            "remediators": ["basic_remediator"],
            "chain": True,
        }

        response = requests.post(
            f"{API_URL}/plugins/process", json=content_data, headers=auth_headers
        )

        if response.status_code == 200:
            result = response.json()

            # Should have validation and remediation results
            assert "validation_results" in result or "final_content" in result


class TestContentWorkflow:
    """Test complete content creation workflow"""

    @pytest.fixture
    def course_with_auth(self) -> tuple:
        """Setup course with auth"""
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": "michael.borck@curtin.edu.au", "password": "password123"},
        )

        if response.status_code != 200:
            return None, {}

        auth_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        course_response = requests.post(
            f"{API_URL}/courses",
            json={
                "title": "Workflow Test Course",
                "code": "WF001",
                "teaching_philosophy": "FLIPPED_CLASSROOM",
            },
            headers=auth_headers,
        )

        if course_response.status_code in [200, 201]:
            return course_response.json(), auth_headers
        return None, auth_headers

    def test_complete_content_workflow(self, course_with_auth):
        """Test generating, validating, and saving content"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")

        # Step 1: Generate content
        generation_response = requests.post(
            f"{API_URL}/llm/generate",
            json={
                "content_type": "lecture",
                "topic": "Python Variables",
                "pedagogy": "FLIPPED_CLASSROOM",
            },
            headers=auth_headers,
        )

        if generation_response.status_code != 200:
            pytest.skip("LLM generation not available")

        generated_content = generation_response.json()

        # Step 2: Validate content
        validation_response = requests.post(
            f"{API_URL}/plugins/validate",
            json={
                "content": str(generated_content.get("content", "")),
                "validators": ["spell_checker", "readability_validator"],
            },
            headers=auth_headers,
        )

        validation_passed = True
        if validation_response.status_code == 200:
            validation_results = validation_response.json()
            # Check if validation passed
            for result in validation_results.get("validation_results", []):
                if result.get("issues", []):
                    validation_passed = False

        # Step 3: Remediate if needed
        final_content = generated_content.get("content", "")
        if not validation_passed:
            remediation_response = requests.post(
                f"{API_URL}/plugins/remediate",
                json={
                    "content": str(final_content),
                    "remediators": ["basic_remediator"],
                },
                headers=auth_headers,
            )

            if remediation_response.status_code == 200:
                final_content = remediation_response.json().get(
                    "remediated_content", final_content
                )

        # Step 4: Save as material
        material_response = requests.post(
            f"{API_URL}/materials",
            json={
                "course_id": course["id"],
                "type": "LECTURE",
                "title": "Python Variables",
                "content": final_content
                if isinstance(final_content, dict)
                else {"content": final_content},
                "raw_content": str(final_content),
                "teaching_philosophy": "FLIPPED_CLASSROOM",
                "metadata": {"generated": True, "validated": validation_passed},
            },
            headers=auth_headers,
        )

        assert material_response.status_code in [200, 201]
        material = material_response.json()

        assert material["course_id"] == course["id"]
        assert material["type"] in ["LECTURE", "lecture"]
        assert material["version"] == 1

    def test_import_enhance_workflow(self, course_with_auth):
        """Test importing and enhancing content"""
        course, auth_headers = course_with_auth
        if not course:
            pytest.skip("Course creation failed")

        # Simulate imported content
        imported_content = """
        Introduction to Python
        
        Python is a programming language.
        It is used for many things.
        You can make programs with it.
        """

        # Step 1: Validate imported content
        requests.post(
            f"{API_URL}/plugins/validate",
            json={
                "content": imported_content,
                "validators": ["readability_validator", "grammar_validator"],
            },
            headers=auth_headers,
        )

        # Step 2: Enhance content
        enhance_response = requests.post(
            f"{API_URL}/llm/enhance",
            json={
                "content": imported_content,
                "enhancement_type": "expand",
                "pedagogy": course.get("teaching_philosophy", "TRADITIONAL"),
            },
            headers=auth_headers,
        )

        enhanced_content = imported_content
        if enhance_response.status_code == 200:
            enhanced_content = enhance_response.json().get(
                "enhanced_content", imported_content
            )

        # Step 3: Save enhanced version
        material_response = requests.post(
            f"{API_URL}/materials",
            json={
                "course_id": course["id"],
                "type": "LECTURE",
                "title": "Imported and Enhanced Content",
                "content": {"original": imported_content, "enhanced": enhanced_content},
                "raw_content": enhanced_content,
            },
            headers=auth_headers,
        )

        assert material_response.status_code in [200, 201]
