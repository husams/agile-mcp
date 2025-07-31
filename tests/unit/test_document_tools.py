"""Unit tests for document tools."""

from unittest.mock import MagicMock, patch

import pytest

from src.agile_mcp.api.document_tools import documents_getSection, documents_ingest
from src.agile_mcp.services.document_service import DocumentValidationError
from src.agile_mcp.services.exceptions import DatabaseError, ProjectValidationError


class TestDocumentsIngest:
    """Test cases for documents_ingest function."""

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_ingest_success(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test successful document ingestion."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.ingest_document.return_value = {
            "id": "doc-1",
            "project_id": "project-1",
            "title": "Test Document",
            "file_path": "/path/to/doc.md",
            "created_at": "2025-07-31T10:00:00.000000",
            "sections": [
                {
                    "id": "section-1",
                    "title": "Introduction",
                    "content": "Test content",
                    "document_id": "doc-1",
                    "order": 0,
                }
            ],
        }

        result = documents_ingest(
            project_id="project-1",
            file_path="/path/to/doc.md",
            content="# Introduction\n\nTest content",
            title="Test Document",
        )

        # Verify response matches DocumentResponse model
        assert result["id"] == "doc-1"
        assert result["title"] == "Test Document"
        assert result["project_id"] == "project-1"
        assert len(result["sections"]) == 1
        assert result["sections"][0]["title"] == "Introduction"

        # Verify service was called correctly
        mock_service.ingest_document.assert_called_once_with(
            project_id="project-1",
            file_path="/path/to/doc.md",
            content="# Introduction\n\nTest content",
            title="Test Document",
        )

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_ingest_validation_error(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test document ingestion with validation error."""
        from fastmcp.exceptions import McpError

        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service to raise validation error
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.ingest_document.side_effect = DocumentValidationError(
            "Invalid content"
        )

        # Verify McpError is raised
        with pytest.raises(McpError) as exc_info:
            documents_ingest(
                project_id="project-1",
                file_path="/path/to/doc.md",
                content="",
                title=None,
            )

        assert exc_info.value.error.code == -32001
        assert "Invalid content" in exc_info.value.error.message

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_ingest_project_validation_error(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test document ingestion with project validation error."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service to raise project validation error
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.ingest_document.side_effect = ProjectValidationError(
            "Project not found"
        )

        result = documents_ingest(
            project_id="nonexistent",
            file_path="/path/to/doc.md",
            content="Content",
            title=None,
        )

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "Project not found" in result["message"]

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_ingest_database_error(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test document ingestion with database error."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service to raise database error
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.ingest_document.side_effect = DatabaseError(
            "Database connection failed"
        )

        result = documents_ingest(
            project_id="project-1",
            file_path="/path/to/doc.md",
            content="Content",
            title=None,
        )

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "DATABASE_ERROR"
        assert "Database connection failed" in result["message"]

    @patch("src.agile_mcp.api.document_tools.get_db")
    def test_documents_ingest_unexpected_error(self, mock_get_db):
        """Test document ingestion with unexpected error."""
        # Mock database session to raise unexpected error
        mock_get_db.side_effect = Exception("Unexpected error")

        result = documents_ingest(
            project_id="project-1",
            file_path="/path/to/doc.md",
            content="Content",
            title=None,
        )

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "INTERNAL_ERROR"
        assert "Unexpected error during document ingestion" in result["message"]


class TestDocumentsGetSection:
    """Test cases for documents_getSection function."""

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_getSection_by_id_success(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test successful section retrieval by ID."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_section_by_id.return_value = {
            "id": "section-1",
            "title": "Introduction",
            "content": "This is the introduction.",
        }

        result = documents_getSection(section_id="section-1")

        # Verify success response
        assert result["status"] == "success"
        assert result["data"]["id"] == "section-1"
        assert "Introduction" in result["message"]

        # Verify service was called correctly
        mock_service.get_section_by_id.assert_called_once_with("section-1")

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_getSection_by_id_not_found(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test section retrieval by ID when not found."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service to return None
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_section_by_id.return_value = None

        result = documents_getSection(section_id="nonexistent")

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "NOT_FOUND"
        assert "Section with ID 'nonexistent' not found" in result["message"]

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_getSection_by_title_success(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test successful section retrieval by title."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_sections_by_title.return_value = [
            {"id": "section-1", "title": "Introduction", "content": "Content 1"},
            {"id": "section-2", "title": "Introduction", "content": "Content 2"},
        ]

        result = documents_getSection(title="Introduction")

        # Verify success response
        assert result["status"] == "success"
        assert len(result["data"]) == 2
        assert "Found 2 section(s)" in result["message"]

        # Verify service was called correctly
        mock_service.get_sections_by_title.assert_called_once_with(
            title="Introduction", document_id=None, project_id=None
        )

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_getSection_by_title_with_filters(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test section retrieval by title with filters."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_sections_by_title.return_value = [
            {"id": "section-1", "title": "Introduction", "content": "Content"}
        ]

        result = documents_getSection(
            title="Introduction", document_id="doc-1", project_id="project-1"
        )

        # Verify success response
        assert result["status"] == "success"
        assert len(result["data"]) == 1

        # Verify service was called with filters
        mock_service.get_sections_by_title.assert_called_once_with(
            title="Introduction", document_id="doc-1", project_id="project-1"
        )

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_getSection_by_title_not_found(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test section retrieval by title when not found."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service to return empty list
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_sections_by_title.return_value = []

        result = documents_getSection(title="Nonexistent")

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "NOT_FOUND"
        assert (
            "No sections found with title containing 'Nonexistent'" in result["message"]
        )

    def test_documents_getSection_no_parameters(self):
        """Test section retrieval with no search parameters."""
        result = documents_getSection()

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "Must provide either section_id or title" in result["message"]

    @patch("src.agile_mcp.api.document_tools.get_db")
    @patch("src.agile_mcp.api.document_tools.DocumentRepository")
    @patch("src.agile_mcp.api.document_tools.ProjectRepository")
    @patch("src.agile_mcp.api.document_tools.DocumentService")
    def test_documents_getSection_validation_error(
        self,
        mock_service_class,
        mock_project_repo_class,
        mock_doc_repo_class,
        mock_get_db,
    ):
        """Test section retrieval with validation error."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_project_repo = MagicMock()
        mock_doc_repo_class.return_value = mock_doc_repo
        mock_project_repo_class.return_value = mock_project_repo

        # Mock service to raise validation error
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_section_by_id.side_effect = DocumentValidationError(
            "Invalid section ID"
        )

        result = documents_getSection(section_id="")

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "Invalid section ID" in result["message"]

    @patch("src.agile_mcp.api.document_tools.get_db")
    def test_documents_getSection_unexpected_error(self, mock_get_db):
        """Test section retrieval with unexpected error."""
        # Mock database session to raise unexpected error
        mock_get_db.side_effect = Exception("Unexpected error")

        result = documents_getSection(section_id="section-1")

        # Verify error response
        assert result["status"] == "error"
        assert result["error_code"] == "INTERNAL_ERROR"
        assert "Unexpected error during section retrieval" in result["message"]
