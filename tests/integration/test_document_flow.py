"""Integration tests for document functionality."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.database import create_tables
from src.agile_mcp.models.epic import Base
from src.agile_mcp.models.project import Project
from src.agile_mcp.repositories.document_repository import DocumentRepository
from src.agile_mcp.repositories.project_repository import ProjectRepository
from src.agile_mcp.services.document_service import DocumentService


@pytest.fixture
def test_db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_project(test_db_session):
    """Create a test project."""
    project_repo = ProjectRepository(test_db_session)
    project = project_repo.create_project(
        "Test Project", "A test project for document tests"
    )
    return project


class TestDocumentIntegrationFlow:
    """Integration tests for document flow."""

    def test_complete_document_flow(self, test_db_session, test_project):
        """Test the complete document ingestion and retrieval flow."""
        # Initialize repositories and service
        document_repo = DocumentRepository(test_db_session)
        project_repo = ProjectRepository(test_db_session)
        document_service = DocumentService(document_repo, project_repo)

        # Test markdown content
        markdown_content = """# Introduction

This is the introduction section with some content.

## Background

This section provides background information about the topic.

### Historical Context

Some historical details here.

## Methodology

This section describes the methodology used.

# Conclusion

This is the conclusion section."""

        # Test document ingestion
        document_data = document_service.ingest_document(
            project_id=test_project.id,
            file_path="/test/document.md",
            content=markdown_content,
            title="Test Document",
        )

        # Verify document was created correctly
        assert document_data["title"] == "Test Document"
        assert document_data["project_id"] == test_project.id
        assert document_data["file_path"] == "/test/document.md"
        assert len(document_data["sections"]) == 5

        # Verify sections
        sections = document_data["sections"]
        expected_sections = [
            ("Introduction", 1, 0),
            ("Background", 2, 1),
            ("Historical Context", 3, 2),
            ("Methodology", 2, 3),
            ("Conclusion", 1, 4),
        ]

        for i, (expected_title, expected_level, expected_order) in enumerate(
            expected_sections
        ):
            assert sections[i]["title"] == expected_title
            assert sections[i]["order"] == expected_order

        # Test retrieving document by ID
        retrieved_document = document_service.get_document_by_id(document_data["id"])
        assert retrieved_document is not None
        assert retrieved_document["id"] == document_data["id"]
        assert len(retrieved_document["sections"]) == 5

        # Test retrieving sections by title
        intro_sections = document_service.get_sections_by_title("Introduction")
        assert len(intro_sections) == 1
        assert intro_sections[0]["title"] == "Introduction"
        assert "This is the introduction section" in intro_sections[0]["content"]

        # Test section retrieval by ID
        section_id = sections[0]["id"]
        retrieved_section = document_service.get_section_by_id(section_id)
        assert retrieved_section is not None
        assert retrieved_section["id"] == section_id
        assert retrieved_section["title"] == "Introduction"

        # Test searching sections with filters
        background_sections = document_service.get_sections_by_title(
            "Background", document_id=document_data["id"]
        )
        assert len(background_sections) == 1
        assert background_sections[0]["title"] == "Background"

        # Test project document retrieval
        project_documents = document_service.get_documents_by_project_id(
            test_project.id
        )
        assert len(project_documents) == 1
        assert project_documents[0]["id"] == document_data["id"]

    def test_multiple_documents_same_project(self, test_db_session, test_project):
        """Test handling multiple documents in the same project."""
        # Initialize repositories and service
        document_repo = DocumentRepository(test_db_session)
        project_repo = ProjectRepository(test_db_session)
        document_service = DocumentService(document_repo, project_repo)

        # Create first document
        doc1_content = """# Document 1

This is the first document.

## Section A

Content of section A."""

        doc1_data = document_service.ingest_document(
            project_id=test_project.id, file_path="/test/doc1.md", content=doc1_content
        )

        # Create second document
        doc2_content = """# Document 2

This is the second document.

## Section A

Different content of section A.

## Section B

Content of section B."""

        doc2_data = document_service.ingest_document(
            project_id=test_project.id, file_path="/test/doc2.md", content=doc2_content
        )

        # Test that both documents exist
        project_documents = document_service.get_documents_by_project_id(
            test_project.id
        )
        assert len(project_documents) == 2

        # Test searching across documents
        section_a_results = document_service.get_sections_by_title("Section A")
        assert len(section_a_results) == 2

        # Test searching within specific document
        doc1_section_a = document_service.get_sections_by_title(
            "Section A", document_id=doc1_data["id"]
        )
        assert len(doc1_section_a) == 1
        assert "Content of section A" in doc1_section_a[0]["content"]

        doc2_section_a = document_service.get_sections_by_title(
            "Section A", document_id=doc2_data["id"]
        )
        assert len(doc2_section_a) == 1
        assert "Different content of section A" in doc2_section_a[0]["content"]

    def test_document_with_no_headings(self, test_db_session, test_project):
        """Test document ingestion with no markdown headings."""
        # Initialize repositories and service
        document_repo = DocumentRepository(test_db_session)
        project_repo = ProjectRepository(test_db_session)
        document_service = DocumentService(document_repo, project_repo)

        # Content without headings
        plain_content = """This is a document without any headings.

It has multiple paragraphs of content.

But no structured sections."""

        document_data = document_service.ingest_document(
            project_id=test_project.id,
            file_path="/test/plain.md",
            content=plain_content,
            title="Plain Document",
        )

        # Should have one section with default title
        assert len(document_data["sections"]) == 1
        assert document_data["sections"][0]["title"] == "Document Content"
        assert document_data["sections"][0]["order"] == 0
        assert plain_content.strip() in document_data["sections"][0]["content"]

    def test_error_handling(self, test_db_session):
        """Test error handling in document service."""
        # Initialize repositories and service
        document_repo = DocumentRepository(test_db_session)
        project_repo = ProjectRepository(test_db_session)
        document_service = DocumentService(document_repo, project_repo)

        # Test ingesting document with non-existent project
        with pytest.raises(Exception):  # Should raise ProjectValidationError
            document_service.ingest_document(
                project_id="nonexistent-project",
                file_path="/test/doc.md",
                content="# Test Document\n\nContent here.",
            )

        # Test retrieving non-existent document
        result = document_service.get_document_by_id("nonexistent-doc")
        assert result is None

        # Test retrieving non-existent section
        result = document_service.get_section_by_id("nonexistent-section")
        assert result is None

        # Test searching for non-existent sections
        results = document_service.get_sections_by_title("Nonexistent Title")
        assert results == []
