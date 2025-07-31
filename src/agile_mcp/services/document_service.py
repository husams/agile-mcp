"""
Service layer for Document business logic operations.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..repositories.document_repository import DocumentRepository
from ..repositories.project_repository import ProjectRepository
from ..utils.logging_config import create_entity_context, get_logger
from ..utils.markdown_parser import MarkdownParser
from .exceptions import (
    DatabaseError,
    ProjectValidationError,
)


class DocumentValidationError(Exception):
    """Exception raised for document validation errors."""

    pass


class DocumentService:
    """Service class for Document business logic operations."""

    # Constants for validation
    MAX_TITLE_LENGTH = 200
    MAX_FILE_PATH_LENGTH = 500
    MAX_CONTENT_SIZE = 10_000_000  # 10MB

    def __init__(
        self,
        document_repository: DocumentRepository,
        project_repository: ProjectRepository,
    ):
        """Initialize service with repository dependencies."""
        self.document_repository = document_repository
        self.project_repository = project_repository
        self.markdown_parser = MarkdownParser()
        self.logger = get_logger(__name__)

    def ingest_document(
        self,
        project_id: str,
        file_path: str,
        content: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a document by parsing its Markdown content into structured sections.

        Args:
            project_id: The ID of the project this document belongs to
            file_path: The path to the original file
            content: The Markdown content to parse
            title: Optional custom title (if not provided, extracted from content)

        Returns:
            Dict[str, Any]: Dictionary representation of the created document with sections

        Raises:
            DocumentValidationError: If validation fails
            ProjectValidationError: If project doesn't exist
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not project_id or not project_id.strip():
            raise DocumentValidationError("Project ID cannot be empty")

        if not file_path or not file_path.strip():
            raise DocumentValidationError("File path cannot be empty")

        if not content or not content.strip():
            raise DocumentValidationError("Document content cannot be empty")

        if len(file_path.strip()) > self.MAX_FILE_PATH_LENGTH:
            raise DocumentValidationError(
                f"File path cannot exceed {self.MAX_FILE_PATH_LENGTH} " "characters"
            )

        if len(content) > self.MAX_CONTENT_SIZE:
            raise DocumentValidationError(
                f"Document content size cannot exceed {self.MAX_CONTENT_SIZE} " "bytes"
            )

        # Validate Markdown content
        if not self.markdown_parser.validate_content(content):
            raise DocumentValidationError("Invalid Markdown content")

        try:
            # Verify project exists
            project = self.project_repository.find_project_by_id(project_id.strip())
            if not project:
                raise ProjectValidationError(
                    f"Project with ID '{project_id}' not found"
                )

            # Extract title if not provided
            if not title:
                title, _ = self.markdown_parser.extract_metadata(content)

            if len(title) > self.MAX_TITLE_LENGTH:
                title = title[: self.MAX_TITLE_LENGTH - 3] + "..."

            self.logger.info(
                "Ingesting document",
                **create_entity_context(project_id=project_id),
                file_path=file_path[:100],  # Truncate for logging
                operation="ingest_document",
            )

            # Parse content into sections
            markdown_sections = self.markdown_parser.parse(content)

            # Convert to section data format
            sections_data = []
            for section in markdown_sections:
                section_data = {
                    "title": section.title,
                    "content": section.content,
                    "order": section.order,
                }
                sections_data.append(section_data)

            # Create document with sections
            document = self.document_repository.create_document_with_sections(
                project_id=project_id.strip(),
                title=title,
                file_path=file_path.strip(),
                sections_data=sections_data,
            )

            self.logger.info(
                "Document ingested successfully",
                **create_entity_context(project_id=project_id, document_id=document.id),
                sections_count=len(sections_data),
                operation="ingest_document",
            )

            return document.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise DocumentValidationError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations
            raise DatabaseError(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID.

        Args:
            document_id: The unique identifier of the document

        Returns:
            Optional[Dict[str, Any]]: Document dictionary if found, None otherwise

        Raises:
            DocumentValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        if not document_id or not document_id.strip():
            raise DocumentValidationError("Document ID cannot be empty")

        try:
            document = self.document_repository.find_document_by_id(document_id.strip())
            return document.to_dict() if document else None

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def get_section_by_id(self, section_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document section by its ID.

        Args:
            section_id: The unique identifier of the section

        Returns:
            Optional[Dict[str, Any]]: Section dictionary if found, None otherwise

        Raises:
            DocumentValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        if not section_id or not section_id.strip():
            raise DocumentValidationError("Section ID cannot be empty")

        try:
            section = self.document_repository.find_section_by_id(section_id.strip())
            return section.to_dict() if section else None

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def get_sections_by_title(
        self,
        title: str,
        document_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find document sections by title.

        Args:
            title: The title to search for
            document_id: Optional document ID to filter by
            project_id: Optional project ID to filter by

        Returns:
            List[Dict[str, Any]]: List of matching section dictionaries

        Raises:
            DocumentValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        if not title or not title.strip():
            raise DocumentValidationError("Section title cannot be empty")

        try:
            sections = self.document_repository.find_sections_by_title(
                title.strip(), document_id, project_id
            )
            return [section.to_dict() for section in sections]

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def get_documents_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all documents for a given project.

        Args:
            project_id: The unique identifier of the project

        Returns:
            List[Dict[str, Any]]: List of document dictionaries

        Raises:
            DocumentValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        if not project_id or not project_id.strip():
            raise DocumentValidationError("Project ID cannot be empty")

        try:
            documents = self.document_repository.find_documents_by_project_id(
                project_id.strip()
            )
            return [document.to_dict() for document in documents]

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")
