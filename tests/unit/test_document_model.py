"""Unit tests for Document and DocumentSection models."""

from datetime import datetime

import pytest

from src.agile_mcp.models.document import Document, DocumentSection


class TestDocument:
    """Test cases for Document model."""

    def test_document_creation(self):
        """Test creating a Document instance."""
        doc = Document(
            id="doc-1",
            project_id="project-1",
            title="Test Document",
            file_path="/path/to/doc.md",
        )

        assert doc.id == "doc-1"
        assert doc.project_id == "project-1"
        assert doc.title == "Test Document"
        assert doc.file_path == "/path/to/doc.md"
        assert isinstance(doc.created_at, datetime)

    def test_document_creation_with_custom_timestamp(self):
        """Test creating a Document with custom timestamp."""
        created_time = datetime(2024, 1, 1, 12, 0, 0)
        doc = Document(
            id="doc-1",
            project_id="project-1",
            title="Test Document",
            file_path="/path/to/doc.md",
            created_at=created_time,
        )

        assert doc.created_at == created_time

    def test_document_to_dict(self):
        """Test Document to_dict method."""
        created_time = datetime(2024, 1, 1, 12, 0, 0)
        doc = Document(
            id="doc-1",
            project_id="project-1",
            title="Test Document",
            file_path="/path/to/doc.md",
            created_at=created_time,
        )

        result = doc.to_dict()

        assert result["id"] == "doc-1"
        assert result["project_id"] == "project-1"
        assert result["title"] == "Test Document"
        assert result["file_path"] == "/path/to/doc.md"
        assert result["created_at"] == "2024-01-01T12:00:00"
        assert result["sections"] == []

    def test_document_title_validation(self):
        """Test Document title validation."""
        # Empty title should raise ValueError
        with pytest.raises(ValueError, match="Document title cannot be empty"):
            Document(
                id="doc-1",
                project_id="project-1",
                title="",
                file_path="/path/to/doc.md",
            )

        # Whitespace-only title should raise ValueError
        with pytest.raises(ValueError, match="Document title cannot be empty"):
            Document(
                id="doc-1",
                project_id="project-1",
                title="   ",
                file_path="/path/to/doc.md",
            )

        # Title too long should raise ValueError
        long_title = "x" * 201
        with pytest.raises(
            ValueError, match="Document title cannot exceed 200 characters"
        ):
            Document(
                id="doc-1",
                project_id="project-1",
                title=long_title,
                file_path="/path/to/doc.md",
            )

        # Valid title with whitespace should be trimmed
        doc = Document(
            id="doc-1",
            project_id="project-1",
            title="  Valid Title  ",
            file_path="/path/to/doc.md",
        )
        assert doc.title == "Valid Title"

    def test_document_file_path_validation(self):
        """Test Document file path validation."""
        # Empty file path should raise ValueError
        with pytest.raises(ValueError, match="Document file path cannot be empty"):
            Document(
                id="doc-1",
                project_id="project-1",
                title="Test Document",
                file_path="",
            )

        # Whitespace-only file path should raise ValueError
        with pytest.raises(ValueError, match="Document file path cannot be empty"):
            Document(
                id="doc-1",
                project_id="project-1",
                title="Test Document",
                file_path="   ",
            )

        # File path too long should raise ValueError
        long_path = "x" * 501
        with pytest.raises(
            ValueError, match="Document file path cannot exceed 500 characters"
        ):
            Document(
                id="doc-1",
                project_id="project-1",
                title="Test Document",
                file_path=long_path,
            )

        # Valid file path with whitespace should be trimmed
        doc = Document(
            id="doc-1",
            project_id="project-1",
            title="Test Document",
            file_path="  /path/to/doc.md  ",
        )
        assert doc.file_path == "/path/to/doc.md"

    def test_document_repr(self):
        """Test Document string representation."""
        doc = Document(
            id="doc-1",
            project_id="project-1",
            title="Test Document",
            file_path="/path/to/doc.md",
        )

        repr_str = repr(doc)
        assert "Document" in repr_str
        assert "doc-1" in repr_str
        assert "Test Document" in repr_str


class TestDocumentSection:
    """Test cases for DocumentSection model."""

    def test_document_section_creation(self):
        """Test creating a DocumentSection instance."""
        section = DocumentSection(
            id="section-1",
            document_id="doc-1",
            title="Introduction",
            content="This is the introduction content.",
            order=0,
        )

        assert section.id == "section-1"
        assert section.document_id == "doc-1"
        assert section.title == "Introduction"
        assert section.content == "This is the introduction content."
        assert section.order == 0

    def test_document_section_to_dict(self):
        """Test DocumentSection to_dict method."""
        section = DocumentSection(
            id="section-1",
            document_id="doc-1",
            title="Introduction",
            content="This is the introduction content.",
            order=0,
        )

        result = section.to_dict()

        assert result["id"] == "section-1"
        assert result["document_id"] == "doc-1"
        assert result["title"] == "Introduction"
        assert result["content"] == "This is the introduction content."
        assert result["order"] == 0

    def test_document_section_title_validation(self):
        """Test DocumentSection title validation."""
        # Empty title should raise ValueError
        with pytest.raises(ValueError, match="Section title cannot be empty"):
            DocumentSection(
                id="section-1",
                document_id="doc-1",
                title="",
                content="Content",
                order=0,
            )

        # Whitespace-only title should raise ValueError
        with pytest.raises(ValueError, match="Section title cannot be empty"):
            DocumentSection(
                id="section-1",
                document_id="doc-1",
                title="   ",
                content="Content",
                order=0,
            )

        # Title too long should raise ValueError
        long_title = "x" * 301
        with pytest.raises(
            ValueError, match="Section title cannot exceed 300 characters"
        ):
            DocumentSection(
                id="section-1",
                document_id="doc-1",
                title=long_title,
                content="Content",
                order=0,
            )

        # Valid title with whitespace should be trimmed
        section = DocumentSection(
            id="section-1",
            document_id="doc-1",
            title="  Valid Title  ",
            content="Content",
            order=0,
        )
        assert section.title == "Valid Title"

    def test_document_section_content_validation(self):
        """Test DocumentSection content validation."""
        # None content should raise ValueError
        with pytest.raises(ValueError, match="Section content cannot be None"):
            DocumentSection(
                id="section-1",
                document_id="doc-1",
                title="Title",
                content=None,
                order=0,
            )

        # Empty content should be allowed
        section = DocumentSection(
            id="section-1",
            document_id="doc-1",
            title="Title",
            content="",
            order=0,
        )
        assert section.content == ""

    def test_document_section_order_validation(self):
        """Test DocumentSection order validation."""
        # Negative order should raise ValueError
        with pytest.raises(ValueError, match="Section order must be non-negative"):
            DocumentSection(
                id="section-1",
                document_id="doc-1",
                title="Title",
                content="Content",
                order=-1,
            )

        # Zero order should be valid
        section = DocumentSection(
            id="section-1",
            document_id="doc-1",
            title="Title",
            content="Content",
            order=0,
        )
        assert section.order == 0

        # Positive order should be valid
        section = DocumentSection(
            id="section-1",
            document_id="doc-1",
            title="Title",
            content="Content",
            order=5,
        )
        assert section.order == 5

    def test_document_section_repr(self):
        """Test DocumentSection string representation."""
        section = DocumentSection(
            id="section-1",
            document_id="doc-1",
            title="Introduction",
            content="Content",
            order=0,
        )

        repr_str = repr(section)
        assert "DocumentSection" in repr_str
        assert "section-1" in repr_str
        assert "Introduction" in repr_str
        assert "order=0" in repr_str
