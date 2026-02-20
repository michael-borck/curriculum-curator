"""
Tests for import endpoints
"""

import pytest
import zipfile
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.user import User

client = TestClient(app)


class TestImportEndpoints:
    """Test import API endpoints"""

    def setup_method(self):
        """Setup test data"""
        self.test_user = User(
            id="test-user-id",
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            role="lecturer",
            is_active=True,
        )
        self.access_token = create_access_token(data={"sub": self.test_user.email})
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    @patch("app.api.routes.content.unit_repo.get_unit_by_id")
    @patch("app.api.routes.content.content_repo.create_content")
    @patch("app.services.file_import_service.FileImportService.process_file")
    def test_upload_content_success(
        self, mock_process_file, mock_create_content, mock_get_unit
    ):
        """Test successful file upload"""
        # Mock dependencies
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")

        mock_process_file.return_value = {
            "success": True,
            "content": "Test content from file",
            "content_type": "lecture",
            "content_type_confidence": 0.8,
            "word_count": 100,
            "sections": [],
            "suggestions": ["Add more examples"],
            "gaps": [],
            "estimated_reading_time": 5,
        }

        mock_content = Mock(id="content-123")
        mock_create_content.return_value = mock_content

        # Test file upload
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        response = client.post(
            "/api/units/unit-123/content/upload",
            files=files,
            headers=self.headers,
            params={
                "week_number": 1,
                "content_type": "lecture",
                "content_category": "general",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == "content-123"
        assert data["content_type"] == "lecture"
        assert data["content_type_confidence"] == 0.8
        assert data["wordCount"] == 100

    @patch("app.api.routes.content.unit_repo.get_unit_by_id")
    def test_upload_content_unit_not_found(self, mock_get_unit):
        """Test upload with non-existent unit"""
        mock_get_unit.return_value = None

        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        response = client.post(
            "/api/units/unit-999/content/upload", files=files, headers=self.headers
        )

        assert response.status_code == 404
        assert "Unit not found" in response.json()["detail"]

    @patch("app.api.routes.content.unit_repo.get_unit_by_id")
    def test_upload_content_file_too_large(self, mock_get_unit):
        """Test upload with file exceeding size limit"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")

        # Create large file content (51MB)
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.pdf", large_content, "application/pdf")}

        response = client.post(
            "/api/units/unit-123/content/upload", files=files, headers=self.headers
        )

        assert response.status_code == 400
        assert "exceeds 50MB limit" in response.json()["detail"]

    @patch("app.api.routes.content.unit_repo.get_unit_by_id")
    @patch("app.api.routes.content.content_repo.create_content")
    @patch("app.services.file_import_service.FileImportService.process_file")
    def test_batch_upload_success(
        self, mock_process_file, mock_create_content, mock_get_unit
    ):
        """Test successful batch file upload"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")

        mock_process_file.return_value = {
            "success": True,
            "content": "Test content",
            "content_type": "lecture",
            "content_type_confidence": 0.8,
            "word_count": 100,
            "sections": [],
            "suggestions": [],
            "gaps": [],
            "estimated_reading_time": 5,
        }

        mock_content = Mock(id="content-123")
        mock_create_content.return_value = mock_content

        # Test batch upload with multiple files
        files = [
            ("files", ("file1.pdf", b"content1", "application/pdf")),
            (
                "files",
                (
                    "file2.docx",
                    b"content2",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ),
            ),
        ]

        response = client.post(
            "/api/units/unit-123/content/upload/batch",
            files=files,
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["success"] is True
        assert data["results"][0]["filename"] == "file1.pdf"

    @patch("app.api.routes.content.unit_repo.get_unit_by_id")
    @patch("app.api.routes.content.content_repo.get_content_unit_id")
    @patch("app.models.content.Content")
    def test_update_content_type(
        self, mock_content_model, mock_get_content_unit_id, mock_get_unit
    ):
        """Test updating content type"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")
        mock_get_content_unit_id.return_value = "unit-123"

        mock_content = Mock(id="content-123", type="lecture", unit_id="unit-123")
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_content

        # Mock the database session dependency
        with patch("app.api.routes.content.deps.get_db", return_value=mock_db):
            response = client.patch(
                "/api/units/unit-123/content/content-123/type?new_type=worksheet",
                headers=self.headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content_type"] == "worksheet"

    def test_update_content_type_invalid_type(self):
        """Test updating content type with invalid type"""
        response = client.patch(
            "/api/units/unit-123/content/content-123/type?new_type=invalid_type",
            headers=self.headers,
        )

        assert response.status_code == 400
        assert "Invalid content type" in response.json()["detail"]

    @patch("app.api.routes.import_content.unit_repo.get_unit_by_id")
    @patch("app.services.file_import_service.file_import_service.process_zip_file")
    def test_import_zip_success(self, mock_process_zip, mock_get_unit):
        """Test successful ZIP import"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")

        mock_process_zip.return_value = {
            "unit_outline_found": True,
            "unit_outline_file": {
                "filename": "Unit_Outline.pdf",
                "path": "Week_01/Unit_Outline.pdf",
                "folder": "Week_01",
            },
            "files_by_week": {
                1: [
                    {
                        "filename": "Lecture_01.pdf",
                        "path": "Week_01/Lecture_01.pdf",
                        "folder": "Week_01",
                        "week_number": 1,
                        "detected_type": "lecture",
                        "processed_type": "lecture",
                        "confidence": 0.9,
                        "word_count": 1500,
                        "size": 10240,
                    }
                ]
            },
            "suggested_structure": [
                {
                    "week": 1,
                    "total_files": 1,
                    "file_types": {"lecture": 1},
                    "suggested_content": [
                        {
                            "type": "lecture",
                            "count": 1,
                            "description": "1 lecture(s) for Week 1",
                        }
                    ],
                }
            ],
            "total_files": 2,
            "processed_files": [],
        }

        # Test ZIP import
        files = {"file": ("unit_materials.zip", b"fake zip content", "application/zip")}
        response = client.post(
            "/api/content/import/zip/unit-123", files=files, headers=self.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["filename"] == "unit_materials.zip"
        assert data["analysis"]["unit_outline_found"] is True
        assert len(data["analysis"]["files_by_week"]) == 1
        assert data["analysis"]["total_files"] == 2

    @patch("app.api.routes.import_content.unit_repo.get_unit_by_id")
    def test_import_zip_invalid_file_type(self, mock_get_unit):
        """Test ZIP import with non-ZIP file"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")

        files = {"file": ("not_a_zip.pdf", b"fake pdf content", "application/pdf")}
        response = client.post(
            "/api/content/import/zip/unit-123", files=files, headers=self.headers
        )

        assert response.status_code == 400
        assert "Only ZIP files" in response.json()["detail"]

    @patch("app.api.routes.import_content.unit_repo.get_unit_by_id")
    @patch("app.services.file_import_service.file_import_service.process_zip_file")
    def test_import_zip_bad_zip(self, mock_process_zip, mock_get_unit):
        """Test ZIP import with invalid ZIP file"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")
        mock_process_zip.side_effect = zipfile.BadZipFile("Invalid ZIP file")

        files = {"file": ("bad.zip", b"not a real zip", "application/zip")}
        response = client.post(
            "/api/content/import/zip/unit-123", files=files, headers=self.headers
        )

        assert response.status_code == 400
        assert "Invalid ZIP file" in response.json()["detail"]

    @patch("app.api.routes.import_content.unit_repo.get_unit_by_id")
    @patch("app.services.pdf_parser_service.pdf_parser_service.extract_from_bytes")
    @patch(
        "app.services.document_analyzer_service.document_analyzer_service.analyze_document"
    )
    @patch(
        "app.services.document_analyzer_service.document_analyzer_service.map_to_course_structure"
    )
    def test_analyze_pdf_success(
        self, mock_map_structure, mock_analyze, mock_extract, mock_get_unit
    ):
        """Test PDF analysis endpoint"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")

        # Mock PDF extraction and analysis
        mock_extracted_doc = Mock(
            metadata=Mock(
                title="Test PDF", page_count=10, word_count=1000, has_toc=True
            ),
            extraction_method="PyPDF",
        )
        mock_extract.return_value = mock_extracted_doc

        mock_analysis = Mock(
            document_type="unit_outline",
            title="Unit Outline",
            metadata={"page_count": 10, "word_count": 1000, "has_toc": True},
            sections=[
                Mock(title="Introduction", level=1, page_start=1, word_count=100)
            ],
            learning_outcomes=["LO1", "LO2"],
            assessments=[
                Mock(name="Assignment 1", type="assignment", weight_percentage=30)
            ],
            weekly_content=[Mock(week_number=1, topic_title="Topic 1")],
            key_concepts=["Concept 1", "Concept 2"],
        )
        mock_analyze.return_value = mock_analysis

        mock_map_structure.return_value = {
            "course_outline": {
                "title": "Unit Outline",
                "description": "Test",
                "duration_weeks": 12,
            },
            "learning_outcomes": [
                {
                    "outcome_type": "knowledge",
                    "outcome_text": "LO1",
                    "bloom_level": "understand",
                }
            ],
            "weekly_topics": [{"week_number": 1, "topic_title": "Topic 1"}],
            "assessments": [
                {
                    "assessment_name": "Assignment 1",
                    "assessment_type": "assignment",
                    "weight_percentage": 30,
                }
            ],
        }

        files = {"file": ("unit_outline.pdf", b"fake pdf content", "application/pdf")}
        response = client.post(
            "/api/content/import/pdf/analyze",
            files=files,
            headers=self.headers,
            params={"extraction_method": "PyPDF"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["filename"] == "unit_outline.pdf"
        assert data["document_type"] == "unit_outline"
        assert "course_structure" in data
        assert len(data["sections"]) == 1

    @patch("app.api.routes.import_content.unit_repo.get_unit_by_id")
    @patch("app.services.pdf_parser_service.pdf_parser_service.extract_from_bytes")
    @patch(
        "app.services.document_analyzer_service.document_analyzer_service.analyze_document"
    )
    @patch(
        "app.services.document_analyzer_service.document_analyzer_service.map_to_course_structure"
    )
    def test_create_unit_structure_from_pdf(
        self, mock_map_structure, mock_analyze, mock_extract, mock_get_unit
    ):
        """Test creating unit structure from PDF"""
        mock_get_unit.return_value = Mock(id="unit-123", owner_id="test-user-id")

        # Mock database operations
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            None  # No existing outline
        )

        # Mock PDF extraction and analysis
        mock_extracted_doc = Mock(
            metadata=Mock(
                title="Test PDF", page_count=10, word_count=1000, has_toc=True
            ),
            extraction_method="PyPDF",
        )
        mock_extract.return_value = mock_extracted_doc

        mock_analysis = Mock(
            document_type="unit_outline",
            title="Unit Outline",
            metadata={"page_count": 10, "word_count": 1000, "has_toc": True},
            sections=[
                Mock(title="Introduction", level=1, page_start=1, word_count=100)
            ],
            learning_outcomes=["LO1", "LO2"],
            assessments=[
                Mock(name="Assignment 1", type="assignment", weight_percentage=30)
            ],
            weekly_content=[Mock(week_number=1, topic_title="Topic 1")],
            key_concepts=["Concept 1", "Concept 2"],
        )
        mock_analyze.return_value = mock_analysis

        mock_map_structure.return_value = {
            "course_outline": {
                "title": "Unit Outline",
                "description": "Test",
                "duration_weeks": 12,
            },
            "learning_outcomes": [
                {
                    "outcome_type": "knowledge",
                    "outcome_text": "LO1",
                    "bloom_level": "understand",
                },
                {
                    "outcome_type": "skill",
                    "outcome_text": "LO2",
                    "bloom_level": "apply",
                },
            ],
            "weekly_topics": [
                {
                    "week_number": 1,
                    "topic_title": "Topic 1",
                    "pre_class_modules": "Read Chapter 1",
                },
                {
                    "week_number": 2,
                    "topic_title": "Topic 2",
                    "in_class_activities": "Group discussion",
                },
            ],
            "assessments": [
                {
                    "assessment_name": "Assignment 1",
                    "assessment_type": "assignment",
                    "weight_percentage": 30,
                },
                {
                    "assessment_name": "Final Exam",
                    "assessment_type": "exam",
                    "weight_percentage": 70,
                },
            ],
        }

        # Mock the database session dependency
        with patch("app.api.routes.import_content.deps.get_db", return_value=mock_db):
            files = {
                "file": ("unit_outline.pdf", b"fake pdf content", "application/pdf")
            }
            response = client.post(
                "/api/content/import/pdf/create-unit-structure/unit-123",
                files=files,
                headers=self.headers,
                params={"auto_create": True},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Course structure created successfully"
        assert "created" in data
        assert "course_outline" in data["created"]
        assert len(data["created"]["learning_outcomes"]) == 2
        assert len(data["created"]["weekly_topics"]) == 2
        assert len(data["created"]["assessments"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
