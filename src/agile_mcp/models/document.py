"""Document and DocumentSection data models for the Agile Management MCP Server."""

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .epic import Base


class Document(Base):
    """
    Document entity representing a structured document in a project.

    Attributes:
        id: Unique identifier for the document
        project_id: Foreign key reference to the parent Project
        title: The title of the document
        file_path: Path to the original file
        created_at: Timestamp when the document was created
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    __table_args__ = (
        CheckConstraint("length(title) <= 200", name="ck_document_title_length"),
        CheckConstraint("length(file_path) <= 500", name="ck_document_path_length"),
    )

    # Relationship to project (many-to-one)
    project = relationship("Project")

    # Relationship to sections (one-to-many)
    sections = relationship(
        "DocumentSection", back_populates="document", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        id: str,
        project_id: str,
        title: str,
        file_path: str,
        created_at: datetime = None,
    ):
        """Initialize Document."""
        super().__init__()
        self.id = id
        self.project_id = project_id
        self.title = title
        self.file_path = file_path
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Document instance to dictionary representation."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sections": [section.to_dict() for section in self.sections],
        }

    @validates("title")
    def validate_title(self, key, title):
        """Validate document title."""
        if not title or not title.strip():
            raise ValueError("Document title cannot be empty")
        if len(title.strip()) > 200:
            raise ValueError("Document title cannot exceed 200 characters")
        return title.strip()

    @validates("file_path")
    def validate_file_path(self, key, file_path):
        """Validate document file path."""
        if not file_path or not file_path.strip():
            raise ValueError("Document file path cannot be empty")
        if len(file_path.strip()) > 500:
            raise ValueError("Document file path cannot exceed 500 characters")
        return file_path.strip()

    def __repr__(self) -> str:
        """Return string representation of Document."""
        return f"<Document(id='{self.id}', title='{self.title}')>"


class DocumentSection(Base):
    """
    DocumentSection entity representing a section within a document.

    Attributes:
        id: Unique identifier for the section
        document_id: Foreign key reference to the parent Document
        title: The title of the section (from Markdown heading)
        content: The content of the section
        order: The order of the section within the document
    """

    __tablename__ = "document_sections"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column("section_order", Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("length(title) <= 300", name="ck_section_title_length"),
        CheckConstraint("section_order >= 0", name="ck_section_order_positive"),
    )

    # Relationship to document (many-to-one)
    document = relationship("Document", back_populates="sections")

    def __init__(
        self,
        id: str,
        document_id: str,
        title: str,
        content: str,
        order: int,
    ):
        """Initialize DocumentSection."""
        super().__init__()
        self.id = id
        self.document_id = document_id
        self.title = title
        self.content = content
        self.order = order

    def to_dict(self) -> Dict[str, Any]:
        """Convert DocumentSection instance to dictionary representation."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content,
            "order": self.order,
        }

    @validates("title")
    def validate_title(self, key, title):
        """Validate section title."""
        if not title or not title.strip():
            raise ValueError("Section title cannot be empty")
        if len(title.strip()) > 300:
            raise ValueError("Section title cannot exceed 300 characters")
        return title.strip()

    @validates("content")
    def validate_content(self, key, content):
        """Validate section content."""
        if content is None:
            raise ValueError("Section content cannot be None")
        return content

    @validates("order")
    def validate_order(self, key, order):
        """Validate section order."""
        if order < 0:
            raise ValueError("Section order must be non-negative")
        return order

    def __repr__(self) -> str:
        """Return string representation of DocumentSection."""
        return (
            f"<DocumentSection(id='{self.id}', title='{self.title}', "
            f"order={self.order})>"
        )
