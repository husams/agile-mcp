"""
Story data model for the Agile Management MCP Server.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .epic import Base
from .story_dependency import story_dependencies


class Story(Base):
    """
    Story entity representing a unit of work within an Epic.

    Attributes:
        id: Unique identifier for the story
        title: A short, descriptive title
        description: The full user story text
        acceptance_criteria: A list of conditions that must be met for the
            story to be considered complete
        status: Current state (ToDo, InProgress, Review, Done)
        priority: Priority level for ordering (higher number = higher priority),
            default 0
        created_at: Timestamp when story was created (for ordering)
        epic_id: Foreign key reference to the parent Epic
    """

    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ToDo")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    epic_id: Mapped[str] = mapped_column(String, ForeignKey("epics.id"), nullable=False)

    __table_args__ = (
        CheckConstraint("length(title) <= 200", name="ck_story_title_length"),
        CheckConstraint(
            "length(description) <= 2000", name="ck_story_description_length"
        ),
        CheckConstraint(
            "status IN ('ToDo', 'InProgress', 'Review', 'Done')",
            name="ck_story_status_values",
        ),
    )

    # Relationship to epic (many-to-one)
    epic = relationship("Epic", back_populates="stories")

    # Relationship to artifacts (one-to-many)
    artifacts = relationship("Artifact", back_populates="story")

    # Many-to-many relationship for dependencies
    dependencies = relationship(
        "Story",
        secondary=story_dependencies,
        primaryjoin="Story.id == story_dependencies.c.story_id",
        secondaryjoin="Story.id == story_dependencies.c.depends_on_story_id",
        back_populates="dependents",
    )

    dependents = relationship(
        "Story",
        secondary=story_dependencies,
        primaryjoin="Story.id == story_dependencies.c.depends_on_story_id",
        secondaryjoin="Story.id == story_dependencies.c.story_id",
        back_populates="dependencies",
    )

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        epic_id: str,
        status: str = "ToDo",
        priority: int = 0,
        created_at: Optional[datetime] = None,
    ):
        """Initialize Story with default status of 'ToDo', priority 0, and current
        timestamp."""
        super().__init__()
        self.id = id
        self.title = title
        self.description = description
        self.acceptance_criteria = acceptance_criteria
        self.epic_id = epic_id
        self.status = status
        self.priority = priority
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Story instance to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "epic_id": self.epic_id,
        }

    @validates("title")
    def validate_title(self, key, title):
        """Validate story title."""
        if not title or not title.strip():
            raise ValueError("Story title cannot be empty")
        if len(title.strip()) > 200:
            raise ValueError("Story title cannot exceed 200 characters")
        return title.strip()

    @validates("description")
    def validate_description(self, key, description):
        """Validate story description."""
        if not description or not description.strip():
            raise ValueError("Story description cannot be empty")
        if len(description.strip()) > 2000:
            raise ValueError("Story description cannot exceed 2000 characters")
        return description.strip()

    @validates("acceptance_criteria")
    def validate_acceptance_criteria(self, key, acceptance_criteria):
        """Validate story acceptance criteria."""
        if not isinstance(acceptance_criteria, list):
            raise ValueError("Acceptance criteria must be a non-empty list")
        if not acceptance_criteria or len(acceptance_criteria) == 0:
            raise ValueError("At least one acceptance criterion is required")
        for criterion in acceptance_criteria:
            if not isinstance(criterion, str) or not criterion.strip():
                raise ValueError("Each acceptance criterion must be a non-empty string")
        return acceptance_criteria

    @validates("status")
    def validate_status(self, key, status):
        """Validate story status."""
        valid_statuses = {"ToDo", "InProgress", "Review", "Done"}
        if status not in valid_statuses:
            raise ValueError(
                f"Story status must be one of: {', '.join(valid_statuses)}"
            )
        return status

    def __repr__(self) -> str:
        return (
            f"<Story(id='{self.id}', title='{self.title}', "
            f"status='{self.status}', epic_id='{self.epic_id}')>"
        )
