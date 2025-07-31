"""
Repository layer for Document data access operations.
"""

import uuid
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from ..models.document import Document, DocumentSection


class DocumentRepository:
    """Repository class for Document entity database operations."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def create_document_with_sections(
        self,
        project_id: str,
        title: str,
        file_path: str,
        sections_data: List[dict],
    ) -> Document:
        """
        Create a new document with its sections atomically.

        Args:
            project_id: The ID of the project this document belongs to
            title: The title of the document
            file_path: The path to the original file
            sections_data: List of section dictionaries with title, content, and order

        Returns:
            Document: The created document instance with sections

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Create document
            document = Document(
                id=str(uuid.uuid4()),
                project_id=project_id,
                title=title,
                file_path=file_path,
            )

            self.db_session.add(document)
            self.db_session.flush()  # Flush to get document ID

            # Create sections
            for section_data in sections_data:
                section = DocumentSection(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    title=section_data["title"],
                    content=section_data["content"],
                    order=section_data["order"],
                )
                self.db_session.add(section)

            self.db_session.commit()
            self.db_session.refresh(document)

            return document

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def find_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        Find a document by its ID, including its sections.

        Args:
            document_id: The unique identifier of the document

        Returns:
            Optional[Document]: The document instance with sections if found,
                None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Document)
                .options(selectinload(Document.sections))
                .filter(Document.id == document_id)
                .first()
            )
        except SQLAlchemyError as e:
            raise e

    def find_documents_by_project_id(self, project_id: str) -> List[Document]:
        """
        Find all documents for a given project.

        Args:
            project_id: The unique identifier of the project

        Returns:
            List[Document]: List of document instances with sections

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Document)
                .options(selectinload(Document.sections))
                .filter(Document.project_id == project_id)
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def find_section_by_id(self, section_id: str) -> Optional[DocumentSection]:
        """
        Find a document section by its ID.

        Args:
            section_id: The unique identifier of the section

        Returns:
            Optional[DocumentSection]: The section instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(DocumentSection)
                .filter(DocumentSection.id == section_id)
                .first()
            )
        except SQLAlchemyError as e:
            raise e

    def find_sections_by_title(
        self,
        title: str,
        document_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[DocumentSection]:
        """
        Find document sections by title, optionally filtered by document or project.

        Args:
            title: The title to search for (case-insensitive)
            document_id: Optional document ID to filter by
            project_id: Optional project ID to filter by

        Returns:
            List[DocumentSection]: List of matching section instances

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            query = self.db_session.query(DocumentSection)

            # Filter by title (case-insensitive)
            query = query.filter(DocumentSection.title.ilike(f"%{title}%"))

            # Filter by document if specified
            if document_id:
                query = query.filter(DocumentSection.document_id == document_id)

            # Filter by project if specified
            if project_id:
                query = query.join(Document).filter(Document.project_id == project_id)

            return query.all()

        except SQLAlchemyError as e:
            raise e

    def find_all_sections_for_document(self, document_id: str) -> List[DocumentSection]:
        """
        Find all sections for a document, ordered by section order.

        Args:
            document_id: The unique identifier of the document

        Returns:
            List[DocumentSection]: List of section instances ordered by their
                order field

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(DocumentSection)
                .filter(DocumentSection.document_id == document_id)
                .order_by(DocumentSection.order)
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its sections.

        Args:
            document_id: The unique identifier of the document to delete

        Returns:
            bool: True if document was deleted, False if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            document = self.find_document_by_id(document_id)
            if not document:
                return False

            self.db_session.delete(document)
            self.db_session.commit()
            return True

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
