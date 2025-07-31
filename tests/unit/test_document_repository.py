"""Unit tests for DocumentRepository."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.agile_mcp.models.document import Document, DocumentSection
from src.agile_mcp.repositories.document_repository import DocumentRepository


class TestDocumentRepository:
    """Test cases for DocumentRepository."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.repository = DocumentRepository(self.mock_session)

    def test_init(self):
        """Test DocumentRepository initialization."""
        assert self.repository.db_session == self.mock_session

    @patch("uuid.uuid4")
    def test_create_document_with_sections_success(self, mock_uuid):
        """Test successful document creation with sections."""
        # Mock UUID generation
        mock_uuid.side_effect = ["doc-id", "section-1", "section-2"]

        # Mock successful database operations
        self.mock_session.add = MagicMock()
        self.mock_session.flush = MagicMock()
        self.mock_session.commit = MagicMock()
        self.mock_session.refresh = MagicMock()

        sections_data = [
            {"title": "Introduction", "content": "Intro content", "order": 0},
            {"title": "Conclusion", "content": "Conclusion content", "order": 1},
        ]

        result = self.repository.create_document_with_sections(
            project_id="project-1",
            title="Test Document",
            file_path="/path/to/doc.md",
            sections_data=sections_data,
        )

        # Verify document creation
        assert isinstance(result, Document)
        assert result.id == "doc-id"
        assert result.project_id == "project-1"
        assert result.title == "Test Document"
        assert result.file_path == "/path/to/doc.md"

        # Verify database operations
        assert self.mock_session.add.call_count == 3  # 1 document + 2 sections
        self.mock_session.flush.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once_with(result)

    def test_create_document_with_sections_database_error(self):
        """Test document creation with database error."""
        self.mock_session.add.side_effect = SQLAlchemyError("Database error")

        sections_data = [{"title": "Section", "content": "Content", "order": 0}]

        with pytest.raises(SQLAlchemyError):
            self.repository.create_document_with_sections(
                project_id="project-1",
                title="Test Document",
                file_path="/path/to/doc.md",
                sections_data=sections_data,
            )

        self.mock_session.rollback.assert_called_once()

    def test_find_document_by_id_found(self):
        """Test finding document by ID when it exists."""
        mock_document = MagicMock(spec=Document)
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = (
            mock_document
        )
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_document_by_id("doc-1")

        assert result == mock_document
        self.mock_session.query.assert_called_once_with(Document)

    def test_find_document_by_id_not_found(self):
        """Test finding document by ID when it doesn't exist."""
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_document_by_id("nonexistent")

        assert result is None

    def test_find_document_by_id_database_error(self):
        """Test finding document by ID with database error."""
        self.mock_session.query.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(SQLAlchemyError):
            self.repository.find_document_by_id("doc-1")

    def test_find_documents_by_project_id_success(self):
        """Test finding documents by project ID."""
        mock_documents = [MagicMock(spec=Document), MagicMock(spec=Document)]
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.all.return_value = (
            mock_documents
        )
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_documents_by_project_id("project-1")

        assert result == mock_documents
        self.mock_session.query.assert_called_once_with(Document)

    def test_find_documents_by_project_id_database_error(self):
        """Test finding documents by project ID with database error."""
        self.mock_session.query.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(SQLAlchemyError):
            self.repository.find_documents_by_project_id("project-1")

    def test_find_section_by_id_found(self):
        """Test finding section by ID when it exists."""
        mock_section = MagicMock(spec=DocumentSection)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_section
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_section_by_id("section-1")

        assert result == mock_section
        self.mock_session.query.assert_called_once_with(DocumentSection)

    def test_find_section_by_id_not_found(self):
        """Test finding section by ID when it doesn't exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_section_by_id("nonexistent")

        assert result is None

    def test_find_sections_by_title_basic_search(self):
        """Test finding sections by title."""
        mock_sections = [MagicMock(spec=DocumentSection)]
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_sections
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_sections_by_title("Introduction")

        assert result == mock_sections
        self.mock_session.query.assert_called_once_with(DocumentSection)

    def test_find_sections_by_title_with_document_filter(self):
        """Test finding sections by title filtered by document."""
        mock_sections = [MagicMock(spec=DocumentSection)]
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = (
            mock_sections
        )
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_sections_by_title(
            "Introduction", document_id="doc-1"
        )

        assert result == mock_sections

    def test_find_sections_by_title_with_project_filter(self):
        """Test finding sections by title filtered by project."""
        mock_sections = [MagicMock(spec=DocumentSection)]
        mock_query = MagicMock()
        mock_query.filter.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_sections
        )
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_sections_by_title(
            "Introduction", project_id="project-1"
        )

        assert result == mock_sections

    def test_find_all_sections_for_document_success(self):
        """Test finding all sections for a document."""
        mock_sections = [
            MagicMock(spec=DocumentSection),
            MagicMock(spec=DocumentSection),
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = (
            mock_sections
        )
        self.mock_session.query.return_value = mock_query

        result = self.repository.find_all_sections_for_document("doc-1")

        assert result == mock_sections
        self.mock_session.query.assert_called_once_with(DocumentSection)

    def test_delete_document_success(self):
        """Test successful document deletion."""
        mock_document = MagicMock(spec=Document)

        # Mock the find_document_by_id method
        with patch.object(
            self.repository, "find_document_by_id", return_value=mock_document
        ):
            result = self.repository.delete_document("doc-1")

        assert result is True
        self.mock_session.delete.assert_called_once_with(mock_document)
        self.mock_session.commit.assert_called_once()

    def test_delete_document_not_found(self):
        """Test document deletion when document doesn't exist."""
        # Mock the find_document_by_id method to return None
        with patch.object(self.repository, "find_document_by_id", return_value=None):
            result = self.repository.delete_document("nonexistent")

        assert result is False
        self.mock_session.delete.assert_not_called()
        self.mock_session.commit.assert_not_called()

    def test_delete_document_database_error(self):
        """Test document deletion with database error."""
        mock_document = MagicMock(spec=Document)

        # Mock the find_document_by_id method
        with patch.object(
            self.repository, "find_document_by_id", return_value=mock_document
        ):
            self.mock_session.delete.side_effect = SQLAlchemyError("Database error")

            with pytest.raises(SQLAlchemyError):
                self.repository.delete_document("doc-1")

        self.mock_session.rollback.assert_called_once()
