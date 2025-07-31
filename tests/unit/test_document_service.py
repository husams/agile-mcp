"""Unit tests for DocumentService."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.agile_mcp.models.document import Document, DocumentSection
from src.agile_mcp.models.project import Project
from src.agile_mcp.repositories.document_repository import DocumentRepository
from src.agile_mcp.repositories.project_repository import ProjectRepository
from src.agile_mcp.services.document_service import (
    DocumentService,
    DocumentValidationError,
)
from src.agile_mcp.services.exceptions import DatabaseError, ProjectValidationError
from src.agile_mcp.utils.markdown_parser import MarkdownParser, MarkdownSection


class TestDocumentService:
    """Test cases for DocumentService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_document_repo = MagicMock(spec=DocumentRepository)
        self.mock_project_repo = MagicMock(spec=ProjectRepository)
        self.service = DocumentService(self.mock_document_repo, self.mock_project_repo)

    def test_init(self):
        """Test DocumentService initialization."""
        assert self.service.document_repository == self.mock_document_repo
        assert self.service.project_repository == self.mock_project_repo
        assert isinstance(self.service.markdown_parser, MarkdownParser)

    def test_ingest_document_success(self):
        """Test successful document ingestion."""
        # Mock project exists
        mock_project = MagicMock(spec=Project)
        self.mock_project_repo.find_project_by_id.return_value = mock_project

        # Mock markdown parsing
        mock_sections = [
            MarkdownSection("Introduction", "Intro content", 1, 0),
            MarkdownSection("Conclusion", "Conclusion content", 1, 1),
        ]
        with patch.object(
            self.service.markdown_parser, "validate_content", return_value=True
        ), patch.object(
            self.service.markdown_parser,
            "extract_metadata",
            return_value=("Test Doc", "Description"),
        ), patch.object(
            self.service.markdown_parser, "parse", return_value=mock_sections
        ):

            # Mock document creation
            mock_document = MagicMock(spec=Document)
            mock_document.to_dict.return_value = {"id": "doc-1", "title": "Test Doc"}
            self.mock_document_repo.create_document_with_sections.return_value = (
                mock_document
            )

            result = self.service.ingest_document(
                project_id="project-1",
                file_path="/path/to/doc.md",
                content="# Introduction\n\nIntro content\n\n# Conclusion\n\nConclusion content",
            )

            assert result == {"id": "doc-1", "title": "Test Doc"}

    def test_ingest_document_with_custom_title(self):
        """Test document ingestion with custom title."""
        # Mock project exists
        mock_project = MagicMock(spec=Project)
        self.mock_project_repo.find_project_by_id.return_value = mock_project

        # Mock markdown parsing
        mock_sections = [MarkdownSection("Section", "Content", 1, 0)]
        with patch.object(
            self.service.markdown_parser, "validate_content", return_value=True
        ), patch.object(
            self.service.markdown_parser, "parse", return_value=mock_sections
        ):

            # Mock document creation
            mock_document = MagicMock(spec=Document)
            mock_document.to_dict.return_value = {
                "id": "doc-1",
                "title": "Custom Title",
            }
            self.mock_document_repo.create_document_with_sections.return_value = (
                mock_document
            )

            result = self.service.ingest_document(
                project_id="project-1",
                file_path="/path/to/doc.md",
                content="Content",
                title="Custom Title",
            )

            # Verify custom title was used
            call_args = self.mock_document_repo.create_document_with_sections.call_args
            assert call_args[1]["title"] == "Custom Title"

    def test_ingest_document_empty_project_id(self):
        """Test document ingestion with empty project ID."""
        with pytest.raises(DocumentValidationError, match="Project ID cannot be empty"):
            self.service.ingest_document("", "/path/to/doc.md", "Content")

    def test_ingest_document_empty_file_path(self):
        """Test document ingestion with empty file path."""
        with pytest.raises(DocumentValidationError, match="File path cannot be empty"):
            self.service.ingest_document("project-1", "", "Content")

    def test_ingest_document_empty_content(self):
        """Test document ingestion with empty content."""
        with pytest.raises(
            DocumentValidationError, match="Document content cannot be empty"
        ):
            self.service.ingest_document("project-1", "/path/to/doc.md", "")

    def test_ingest_document_file_path_too_long(self):
        """Test document ingestion with file path too long."""
        long_path = "x" * 501
        with pytest.raises(
            DocumentValidationError, match="File path cannot exceed 500 characters"
        ):
            self.service.ingest_document("project-1", long_path, "Content")

    def test_ingest_document_content_too_large(self):
        """Test document ingestion with content too large."""
        large_content = "x" * (10_000_001)
        with pytest.raises(
            DocumentValidationError, match="Document content size cannot exceed"
        ):
            self.service.ingest_document("project-1", "/path/to/doc.md", large_content)

    def test_ingest_document_invalid_markdown(self):
        """Test document ingestion with invalid markdown."""
        with patch.object(
            self.service.markdown_parser, "validate_content", return_value=False
        ):
            with pytest.raises(
                DocumentValidationError, match="Invalid Markdown content"
            ):
                self.service.ingest_document("project-1", "/path/to/doc.md", "Content")

    def test_ingest_document_project_not_found(self):
        """Test document ingestion when project doesn't exist."""
        self.mock_project_repo.find_project_by_id.return_value = None

        with patch.object(
            self.service.markdown_parser, "validate_content", return_value=True
        ):
            with pytest.raises(
                ProjectValidationError, match="Project with ID 'project-1' not found"
            ):
                self.service.ingest_document("project-1", "/path/to/doc.md", "Content")

    def test_ingest_document_title_too_long_gets_truncated(self):
        """Test document ingestion with title that gets truncated."""
        # Mock project exists
        mock_project = MagicMock(spec=Project)
        self.mock_project_repo.find_project_by_id.return_value = mock_project

        long_title = "x" * 250
        with patch.object(
            self.service.markdown_parser, "validate_content", return_value=True
        ), patch.object(
            self.service.markdown_parser,
            "extract_metadata",
            return_value=(long_title, "Description"),
        ), patch.object(
            self.service.markdown_parser, "parse", return_value=[]
        ):

            mock_document = MagicMock(spec=Document)
            mock_document.to_dict.return_value = {"id": "doc-1"}
            self.mock_document_repo.create_document_with_sections.return_value = (
                mock_document
            )

            self.service.ingest_document("project-1", "/path/to/doc.md", "Content")

            # Verify title was truncated
            call_args = self.mock_document_repo.create_document_with_sections.call_args
            title_used = call_args[1]["title"]
            assert len(title_used) <= 200
            assert title_used.endswith("...")

    def test_ingest_document_database_error(self):
        """Test document ingestion with database error."""
        # Mock project exists
        mock_project = MagicMock(spec=Project)
        self.mock_project_repo.find_project_by_id.return_value = mock_project

        with patch.object(
            self.service.markdown_parser, "validate_content", return_value=True
        ), patch.object(
            self.service.markdown_parser,
            "extract_metadata",
            return_value=("Title", "Description"),
        ), patch.object(
            self.service.markdown_parser, "parse", return_value=[]
        ):

            self.mock_document_repo.create_document_with_sections.side_effect = (
                SQLAlchemyError("DB Error")
            )

            with pytest.raises(DatabaseError, match="Database operation failed"):
                self.service.ingest_document("project-1", "/path/to/doc.md", "Content")

    def test_ingest_document_integrity_error(self):
        """Test document ingestion with integrity error."""
        # Mock project exists
        mock_project = MagicMock(spec=Project)
        self.mock_project_repo.find_project_by_id.return_value = mock_project

        with patch.object(
            self.service.markdown_parser, "validate_content", return_value=True
        ), patch.object(
            self.service.markdown_parser,
            "extract_metadata",
            return_value=("Title", "Description"),
        ), patch.object(
            self.service.markdown_parser, "parse", return_value=[]
        ):

            self.mock_document_repo.create_document_with_sections.side_effect = (
                IntegrityError("msg", "orig", "params")
            )

            with pytest.raises(DatabaseError, match="Data integrity error"):
                self.service.ingest_document("project-1", "/path/to/doc.md", "Content")

    def test_get_document_by_id_success(self):
        """Test successful document retrieval by ID."""
        mock_document = MagicMock(spec=Document)
        mock_document.to_dict.return_value = {"id": "doc-1", "title": "Test Doc"}
        self.mock_document_repo.find_document_by_id.return_value = mock_document

        result = self.service.get_document_by_id("doc-1")

        assert result == {"id": "doc-1", "title": "Test Doc"}
        self.mock_document_repo.find_document_by_id.assert_called_once_with("doc-1")

    def test_get_document_by_id_not_found(self):
        """Test document retrieval by ID when not found."""
        self.mock_document_repo.find_document_by_id.return_value = None

        result = self.service.get_document_by_id("nonexistent")

        assert result is None

    def test_get_document_by_id_empty_id(self):
        """Test document retrieval with empty ID."""
        with pytest.raises(
            DocumentValidationError, match="Document ID cannot be empty"
        ):
            self.service.get_document_by_id("")

    def test_get_document_by_id_database_error(self):
        """Test document retrieval with database error."""
        self.mock_document_repo.find_document_by_id.side_effect = SQLAlchemyError(
            "DB Error"
        )

        with pytest.raises(DatabaseError, match="Database operation failed"):
            self.service.get_document_by_id("doc-1")

    def test_get_section_by_id_success(self):
        """Test successful section retrieval by ID."""
        mock_section = MagicMock(spec=DocumentSection)
        mock_section.to_dict.return_value = {"id": "section-1", "title": "Introduction"}
        self.mock_document_repo.find_section_by_id.return_value = mock_section

        result = self.service.get_section_by_id("section-1")

        assert result == {"id": "section-1", "title": "Introduction"}
        self.mock_document_repo.find_section_by_id.assert_called_once_with("section-1")

    def test_get_section_by_id_not_found(self):
        """Test section retrieval by ID when not found."""
        self.mock_document_repo.find_section_by_id.return_value = None

        result = self.service.get_section_by_id("nonexistent")

        assert result is None

    def test_get_section_by_id_empty_id(self):
        """Test section retrieval with empty ID."""
        with pytest.raises(DocumentValidationError, match="Section ID cannot be empty"):
            self.service.get_section_by_id("")

    def test_get_sections_by_title_success(self):
        """Test successful section retrieval by title."""
        mock_sections = [
            MagicMock(spec=DocumentSection),
            MagicMock(spec=DocumentSection),
        ]
        mock_sections[0].to_dict.return_value = {
            "id": "section-1",
            "title": "Introduction",
        }
        mock_sections[1].to_dict.return_value = {
            "id": "section-2",
            "title": "Introduction",
        }
        self.mock_document_repo.find_sections_by_title.return_value = mock_sections

        result = self.service.get_sections_by_title("Introduction")

        assert len(result) == 2
        assert result[0] == {"id": "section-1", "title": "Introduction"}
        assert result[1] == {"id": "section-2", "title": "Introduction"}

    def test_get_sections_by_title_with_filters(self):
        """Test section retrieval by title with filters."""
        mock_sections = [MagicMock(spec=DocumentSection)]
        mock_sections[0].to_dict.return_value = {
            "id": "section-1",
            "title": "Introduction",
        }
        self.mock_document_repo.find_sections_by_title.return_value = mock_sections

        result = self.service.get_sections_by_title(
            "Introduction",
            document_id="doc-1",
            project_id="project-1",
        )

        assert len(result) == 1
        self.mock_document_repo.find_sections_by_title.assert_called_once_with(
            "Introduction", "doc-1", "project-1"
        )

    def test_get_sections_by_title_empty_title(self):
        """Test section retrieval with empty title."""
        with pytest.raises(
            DocumentValidationError, match="Section title cannot be empty"
        ):
            self.service.get_sections_by_title("")

    def test_get_documents_by_project_id_success(self):
        """Test successful document retrieval by project ID."""
        mock_documents = [MagicMock(spec=Document), MagicMock(spec=Document)]
        mock_documents[0].to_dict.return_value = {"id": "doc-1", "title": "Doc 1"}
        mock_documents[1].to_dict.return_value = {"id": "doc-2", "title": "Doc 2"}
        self.mock_document_repo.find_documents_by_project_id.return_value = (
            mock_documents
        )

        result = self.service.get_documents_by_project_id("project-1")

        assert len(result) == 2
        assert result[0] == {"id": "doc-1", "title": "Doc 1"}
        assert result[1] == {"id": "doc-2", "title": "Doc 2"}

    def test_get_documents_by_project_id_empty_id(self):
        """Test document retrieval with empty project ID."""
        with pytest.raises(DocumentValidationError, match="Project ID cannot be empty"):
            self.service.get_documents_by_project_id("")

    def test_get_documents_by_project_id_database_error(self):
        """Test document retrieval by project ID with database error."""
        self.mock_document_repo.find_documents_by_project_id.side_effect = (
            SQLAlchemyError("DB Error")
        )

        with pytest.raises(DatabaseError, match="Database operation failed"):
            self.service.get_documents_by_project_id("project-1")
