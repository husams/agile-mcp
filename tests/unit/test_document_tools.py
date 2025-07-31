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
        from fastmcp.exceptions import McpError

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

        # Verify McpError is raised
        with pytest.raises(McpError) as exc_info:
            documents_ingest(
                project_id="nonexistent",
                file_path="/path/to/doc.md",
                content="Content",
                title=None,
            )

        assert exc_info.value.error.code == -32001
        assert "Project not found" in exc_info.value.error.message

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
        from fastmcp.exceptions import McpError

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

        # Verify McpError is raised
        with pytest.raises(McpError) as exc_info:
            documents_ingest(
                project_id="project-1",
                file_path="/path/to/doc.md",
                content="Content",
                title=None,
            )

        assert exc_info.value.error.code == -32002
        assert "Database connection failed" in exc_info.value.error.message

    @patch("src.agile_mcp.api.document_tools.get_db")
    def test_documents_ingest_unexpected_error(self, mock_get_db):
        """Test document ingestion with unexpected error."""
        from fastmcp.exceptions import McpError

        # Mock database session to raise unexpected error
        mock_get_db.side_effect = Exception("Unexpected error")

        # Verify McpError is raised
        with pytest.raises(McpError) as exc_info:
            documents_ingest(
                project_id="project-1",
                file_path="/path/to/doc.md",
                content="Content",
                title=None,
            )

        assert exc_info.value.error.code == -32000
        assert "Unexpected error" in exc_info.value.error.message


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
            "document_id": "doc-1",
            "title": "Introduction",
            "content": "This is the introduction.",
            "order": 0,
        }

        result = documents_getSection(section_id="section-1")

        # Verify success response
        assert result["id"] == "section-1"
        assert result["document_id"] == "doc-1"
        assert result["title"] == "Introduction"
        assert result["content"] == "This is the introduction."
        assert result["order"] == 0

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
        from fastmcp.exceptions import McpError

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

        # Verify McpError is raised
        with pytest.raises(McpError) as exc_info:
            documents_getSection(section_id="nonexistent")

        assert exc_info.value.error.code == -32003
        assert "Section with ID 'nonexistent' not found" in exc_info.value.error.message

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
            {
                "id": "section-1",
                "document_id": "doc-1",
                "title": "Introduction",
                "content": "Content 1",
                "order": 0,
            },
            {
                "id": "section-2",
                "document_id": "doc-1",
                "title": "Introduction",
                "content": "Content 2",
                "order": 1,
            },
        ]

        result = documents_getSection(title="Introduction")

        # Verify response is a list of section model dumps
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == "section-1"
        assert result[0]["title"] == "Introduction"
        assert result[1]["id"] == "section-2"
        assert result[1]["title"] == "Introduction"

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
            {
                "id": "section-1",
                "document_id": "doc-1",
                "title": "Introduction",
                "content": "Content",
                "order": 0,
            }
        ]

        result = documents_getSection(
            title="Introduction", document_id="doc-1", project_id="project-1"
        )

        # Verify response is a list of section model dumps
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "section-1"
        assert result[0]["title"] == "Introduction"

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
        from fastmcp.exceptions import McpError

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

        # Verify McpError is raised for not found
        with pytest.raises(McpError) as exc_info:
            documents_getSection(title="Nonexistent")

        assert exc_info.value.error.code == -32003
        assert (
            "No sections found with title containing 'Nonexistent'"
            in exc_info.value.error.message
        )

    def test_documents_getSection_no_parameters(self):
        """Test section retrieval with no search parameters."""
        from fastmcp.exceptions import McpError

        # Verify McpError is raised
        with pytest.raises(McpError) as exc_info:
            documents_getSection()

        assert exc_info.value.error.code == -32001
        assert "Must provide either section_id or title" in exc_info.value.error.message

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
        mock_service.get_section_by_id.side_effect = DocumentValidationError(
            "Invalid section ID"
        )

        # Verify McpError is raised - empty section_id triggers validation error
        with pytest.raises(McpError) as exc_info:
            documents_getSection(section_id="")

        assert exc_info.value.error.code == -32001
        assert "Must provide either section_id or title" in exc_info.value.error.message

    @patch("src.agile_mcp.api.document_tools.get_db")
    def test_documents_getSection_unexpected_error(self, mock_get_db):
        """Test section retrieval with unexpected error."""
        from fastmcp.exceptions import McpError

        # Mock database session to raise unexpected error
        mock_get_db.side_effect = Exception("Unexpected error")

        # Verify McpError is raised
        with pytest.raises(McpError) as exc_info:
            documents_getSection(section_id="section-1")

        assert exc_info.value.error.code == -32000
        assert "Unexpected error" in exc_info.value.error.message
