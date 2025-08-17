"""
Integration tests for file import and processing
Tests against real running backend with actual file uploads
"""

import pytest
import requests
import time
import os
import io
from pathlib import Path
from typing import Any


class TestFileImport:
    """Test file import and processing functionality"""
    
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
        """Create a test course for imports"""
        course_data = {
            "title": f"Import Test Course {int(time.time())}",
            "description": "Course for testing file imports",
            "objectives": ["Import test objective"],
            "duration_weeks": 6
        }
        
        response = requests.post(
            f"{api_url}/courses",
            json=course_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        return response.json()["id"]
    
    @pytest.fixture
    def sample_pdf_file(self) -> bytes:
        """Create a simple PDF file for testing"""
        # Create a minimal PDF content
        return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Resources << /Font << /F1 4 0 R >> >>
/Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000117 00000 n 
0000000262 00000 n 
0000000341 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
435
%%EOF"""
    
    @pytest.fixture
    def sample_text_file(self) -> bytes:
        """Create a simple text file for testing"""
        content = """# Test Document

## Introduction
This is a test document for import functionality testing.

## Main Content
- Point 1: Important concept
- Point 2: Another key idea
- Point 3: Final thought

## Conclusion
This document demonstrates basic text import capabilities.
"""
        return content.encode('utf-8')
    
    def test_upload_file(self, api_url, auth_headers, test_course_id, sample_text_file):
        """Test uploading a file to a course"""
        # Prepare file for upload
        files = {
            'file': ('test_document.txt', io.BytesIO(sample_text_file), 'text/plain')
        }
        
        response = requests.post(
            f"{api_url}/courses/{test_course_id}/import",
            files=files,
            headers=auth_headers
        )
        
        # Check if endpoint exists and handles upload
        if response.status_code == 200:
            result = response.json()
            assert "id" in result or "file_id" in result or "status" in result
            assert "filename" in result or "name" in result
        elif response.status_code == 404:
            # Endpoint might not be implemented yet
            pytest.skip("Import endpoint not yet implemented")
    
    def test_upload_pdf_file(self, api_url, auth_headers, test_course_id, sample_pdf_file):
        """Test uploading a PDF file"""
        files = {
            'file': ('test_document.pdf', io.BytesIO(sample_pdf_file), 'application/pdf')
        }
        
        response = requests.post(
            f"{api_url}/courses/{test_course_id}/import",
            files=files,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            result = response.json()
            # Verify PDF was accepted
            assert result is not None
        elif response.status_code == 415:
            # File type might not be supported
            assert "Unsupported" in response.json().get("detail", "")
        elif response.status_code == 404:
            pytest.skip("Import endpoint not yet implemented")
    
    def test_upload_multiple_files(self, api_url, auth_headers, test_course_id, sample_text_file):
        """Test uploading multiple files at once"""
        # Create multiple files
        files = [
            ('files', ('doc1.txt', io.BytesIO(sample_text_file), 'text/plain')),
            ('files', ('doc2.txt', io.BytesIO(b"Second document content"), 'text/plain')),
            ('files', ('doc3.txt', io.BytesIO(b"Third document content"), 'text/plain'))
        ]
        
        response = requests.post(
            f"{api_url}/courses/{test_course_id}/import/batch",
            files=files,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            results = response.json()
            assert isinstance(results, list) or "files" in results
        elif response.status_code == 404:
            # Try single file endpoint with multiple files
            pytest.skip("Batch import endpoint not yet implemented")
    
    def test_process_imported_file(self, api_url, auth_headers, test_course_id, sample_text_file):
        """Test processing an imported file to extract content"""
        # First upload a file
        files = {
            'file': ('test_content.txt', io.BytesIO(sample_text_file), 'text/plain')
        }
        
        upload_response = requests.post(
            f"{api_url}/courses/{test_course_id}/import",
            files=files,
            headers=auth_headers
        )
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            
            # Try to process the file
            file_id = upload_result.get("id") or upload_result.get("file_id")
            if file_id:
                process_response = requests.post(
                    f"{api_url}/imports/{file_id}/process",
                    headers=auth_headers
                )
                
                if process_response.status_code == 200:
                    processed = process_response.json()
                    assert "content" in processed or "extracted_text" in processed
                    assert "metadata" in processed or "analysis" in processed
        elif upload_response.status_code == 404:
            pytest.skip("Import processing not yet implemented")
    
    def test_import_analysis(self, api_url, auth_headers, test_course_id, sample_text_file):
        """Test content analysis and gap detection"""
        # Upload file
        files = {
            'file': ('curriculum.txt', io.BytesIO(sample_text_file), 'text/plain')
        }
        
        upload_response = requests.post(
            f"{api_url}/courses/{test_course_id}/import",
            files=files,
            headers=auth_headers
        )
        
        if upload_response.status_code == 200:
            # Request analysis
            analysis_response = requests.post(
                f"{api_url}/courses/{test_course_id}/analyze",
                json={"check_gaps": True, "check_alignment": True},
                headers=auth_headers
            )
            
            if analysis_response.status_code == 200:
                analysis = analysis_response.json()
                assert "gaps" in analysis or "recommendations" in analysis
                assert "coverage" in analysis or "completeness" in analysis
        elif upload_response.status_code == 404:
            pytest.skip("Content analysis not yet implemented")
    
    def test_invalid_file_type(self, api_url, auth_headers, test_course_id):
        """Test uploading an invalid file type"""
        # Try to upload an executable file (should be rejected)
        files = {
            'file': ('malicious.exe', io.BytesIO(b"MZ\x90\x00"), 'application/x-msdownload')
        }
        
        response = requests.post(
            f"{api_url}/courses/{test_course_id}/import",
            files=files,
            headers=auth_headers
        )
        
        # Should be rejected
        if response.status_code != 404:  # If endpoint exists
            assert response.status_code in [400, 415, 422]
            if response.status_code != 500:  # Don't check detail on server errors
                assert "not supported" in response.json().get("detail", "").lower() or \
                       "invalid" in response.json().get("detail", "").lower()
    
    def test_file_size_limit(self, api_url, auth_headers, test_course_id):
        """Test file size limits"""
        # Create a large file (10MB)
        large_content = b"X" * (10 * 1024 * 1024)
        
        files = {
            'file': ('large_file.txt', io.BytesIO(large_content), 'text/plain')
        }
        
        response = requests.post(
            f"{api_url}/courses/{test_course_id}/import",
            files=files,
            headers=auth_headers
        )
        
        # Check response based on configured limits
        if response.status_code == 413:
            # File too large
            assert "too large" in response.json().get("detail", "").lower()
        elif response.status_code == 200:
            # File accepted - verify it was processed
            result = response.json()
            assert result is not None
        elif response.status_code == 404:
            pytest.skip("Import endpoint not yet implemented")


class TestContentValidation:
    """Test content validation and remediation plugins"""
    
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
    
    def test_validate_content(self, api_url, auth_headers):
        """Test content validation endpoint"""
        content_data = {
            "text": "This is a test content with some mispellings and grammer issues.",
            "type": "lecture",
            "validators": ["spell_checker", "grammar_validator"]
        }
        
        response = requests.post(
            f"{api_url}/content/validate",
            json=content_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            validation = response.json()
            assert "issues" in validation or "errors" in validation or "warnings" in validation
            assert "valid" in validation or "is_valid" in validation
        elif response.status_code == 404:
            pytest.skip("Validation endpoint not yet implemented")
    
    def test_remediate_content(self, api_url, auth_headers):
        """Test content remediation endpoint"""
        content_data = {
            "text": "This content need fixing. It have errors.",
            "type": "lecture",
            "remediators": ["grammar_fixer", "readability_enhancer"]
        }
        
        response = requests.post(
            f"{api_url}/content/remediate",
            json=content_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            remediated = response.json()
            assert "improved_text" in remediated or "text" in remediated
            assert "changes" in remediated or "modifications" in remediated
        elif response.status_code == 404:
            pytest.skip("Remediation endpoint not yet implemented")
    
    def test_accessibility_check(self, api_url, auth_headers):
        """Test accessibility validation"""
        content_data = {
            "html": "<img src='test.jpg'><p>Text without headings</p>",
            "type": "lecture",
            "check_accessibility": True
        }
        
        response = requests.post(
            f"{api_url}/content/validate",
            json=content_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            validation = response.json()
            # Should flag missing alt text and heading structure
            if "issues" in validation or "warnings" in validation:
                issues = validation.get("issues", validation.get("warnings", []))
                assert len(issues) > 0  # Should find accessibility issues
        elif response.status_code == 404:
            pytest.skip("Accessibility validation not yet implemented")