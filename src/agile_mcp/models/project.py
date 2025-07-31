"""Project data model for the Agile Management MCP Server."""

from typing import Any, Dict

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .epic import Base


class Project(Base):
    """
    Project entity representing a top-level project container.

    Attributes:
        id: Unique identifier for the project
        name: The name of the project
        description: A detailed explanation of the project's purpose
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint("length(name) <= 200", name="ck_project_name_length"),
        CheckConstraint(
            "length(description) <= 2000", name="ck_project_description_length"
        ),
    )

    # Relationship to epics (one-to-many)
    epics = relationship("Epic", back_populates="project")

    # Relationship to documents (one-to-many)
    documents = relationship("Document", back_populates="project")

    def __init__(self, id: str, name: str, description: str):
        """Initialize Project."""
        super().__init__()
        self.id = id
        self.name = name
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert Project instance to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }

    @validates("name")
    def validate_name(self, key, name):
        """Validate project name."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        if len(name.strip()) > 200:
            raise ValueError("Project name cannot exceed 200 characters")
        return name.strip()

    @validates("description")
    def validate_description(self, key, description):
        """Validate project description."""
        if not description or not description.strip():
            raise ValueError("Project description cannot be empty")
        if len(description.strip()) > 2000:
            raise ValueError("Project description cannot exceed 2000 characters")
        return description.strip()

    def __repr__(self) -> str:
        """Return string representation of Project."""
        return f"<Project(id='{self.id}', name='{self.name}')>"
