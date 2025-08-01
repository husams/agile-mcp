"""Epic data model for the Agile Management MCP Server."""

from typing import Any, Dict

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Epic(Base):
    """
    Epic entity representing a high-level goal or feature.

    Attributes:
        id: Unique identifier for the epic
        title: The name of the epic
        description: A detailed explanation of the epic's goal
        status: Current state (Draft, Ready, In Progress, Done, On Hold)
        project_id: Foreign key reference to the parent Project
    """

    __tablename__ = "epics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id"), nullable=False
    )

    __table_args__ = (
        CheckConstraint("length(title) <= 200", name="ck_epic_title_length"),
        CheckConstraint(
            "length(description) <= 2000", name="ck_epic_description_length"
        ),
        CheckConstraint(
            "status IN ('Draft', 'Ready', 'In Progress', 'Done', 'On Hold')",
            name="ck_epic_status_values",
        ),
    )

    # Relationship to project (many-to-one)
    project = relationship("Project", back_populates="epics")

    # Relationship to stories (one-to-many)
    stories = relationship("Story", back_populates="epic")

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        project_id: str,
        status: str = "Draft",
    ):
        """Initialize Epic with default status of 'Draft'."""
        super().__init__()
        self.id = id
        self.title = title
        self.description = description
        self.project_id = project_id
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Convert Epic instance to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "project_id": self.project_id,
        }

    @validates("title")
    def validate_title(self, key, title):
        """Validate epic title."""
        if not title or not title.strip():
            raise ValueError("Epic title cannot be empty")
        if len(title.strip()) > 200:
            raise ValueError("Epic title cannot exceed 200 characters")
        return title.strip()

    @validates("description")
    def validate_description(self, key, description):
        """Validate epic description."""
        if not description or not description.strip():
            raise ValueError("Epic description cannot be empty")
        if len(description.strip()) > 2000:
            raise ValueError("Epic description cannot exceed 2000 characters")
        return description.strip()

    @validates("status")
    def validate_status(self, key, status):
        """Validate epic status."""
        valid_statuses = {"Draft", "Ready", "In Progress", "Done", "On Hold"}
        if status not in valid_statuses:
            raise ValueError(f"Epic status must be one of: {', '.join(valid_statuses)}")
        return status

    def __repr__(self) -> str:
        """Return string representation of Epic."""
        return f"<Epic(id='{self.id}', title='{self.title}', status='{self.status}')>"
