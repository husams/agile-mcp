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
        structured_acceptance_criteria: A list of structured acceptance criteria
            for independent tracking. Each criterion has: {'id': str,
            'description': str, 'met': bool, 'order': int}
        tasks: A list of individual tasks that break down the story work.
            Each task has: {'id': str, 'description': str, 'completed': bool,
            'order': int}
        comments: A list of comments associated with the story.
            Each comment has: {'id': str, 'author_role': str, 'content': str,
            'timestamp': datetime, 'reply_to_id': str | None}
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
    structured_acceptance_criteria: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    tasks: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    comments: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    dev_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
        tasks: Optional[List[Dict[str, Any]]] = None,
        structured_acceptance_criteria: Optional[List[Dict[str, Any]]] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        dev_notes: Optional[str] = None,
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
        self.structured_acceptance_criteria = structured_acceptance_criteria or []
        self.tasks = tasks or []
        self.comments = comments or []
        self.dev_notes = dev_notes
        self.epic_id = epic_id
        self.status = status
        self.priority = priority
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Story instance to dictionary representation."""
        # Convert comments to serializable format
        serialized_comments = []
        for comment in self.comments:
            serialized_comment = comment.copy()
            # Ensure timestamp is always in ISO string format for serialization
            timestamp = serialized_comment.get("timestamp")
            if isinstance(timestamp, datetime):
                serialized_comment["timestamp"] = timestamp.isoformat()
            elif isinstance(timestamp, str):
                # Already a string, keep it as is (should be ISO format from validation)
                pass
            serialized_comments.append(serialized_comment)

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "structured_acceptance_criteria": self.structured_acceptance_criteria,
            "tasks": self.tasks,
            "comments": serialized_comments,
            "dev_notes": self.dev_notes,
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

    @validates("tasks")
    def validate_tasks(self, key, tasks):
        """Validate story tasks."""
        if not isinstance(tasks, list):
            raise ValueError("Tasks must be a list")

        required_fields = {"id", "description", "completed", "order"}
        used_ids = set()
        used_orders = set()

        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise ValueError(f"Task at index {i} must be a dictionary")

            # Check required fields
            if not required_fields.issubset(task.keys()):
                missing = required_fields - task.keys()
                raise ValueError(
                    f"Task at index {i} missing required fields: {missing}"
                )

            # Validate id
            if not isinstance(task["id"], str) or not task["id"].strip():
                raise ValueError(f"Task at index {i} must have a non-empty string id")
            if task["id"] in used_ids:
                raise ValueError(f"Task id '{task['id']}' is not unique")
            used_ids.add(task["id"])

            # Validate description
            if (
                not isinstance(task["description"], str)
                or not task["description"].strip()
            ):
                raise ValueError(
                    f"Task at index {i} must have a non-empty string description"
                )

            # Validate completed
            if not isinstance(task["completed"], bool):
                raise ValueError(f"Task at index {i} completed field must be a boolean")

            # Validate order
            if not isinstance(task["order"], int):
                raise ValueError(f"Task at index {i} order field must be an integer")
            if task["order"] in used_orders:
                raise ValueError(f"Task order {task['order']} is not unique")
            used_orders.add(task["order"])

        return tasks

    @validates("structured_acceptance_criteria")
    def validate_structured_acceptance_criteria(
        self, key, structured_acceptance_criteria
    ):
        """Validate story structured acceptance criteria."""
        if not isinstance(structured_acceptance_criteria, list):
            raise ValueError("Structured acceptance criteria must be a list")

        required_fields = {"id", "description", "met", "order"}
        used_ids = set()
        used_orders = set()

        for i, criterion in enumerate(structured_acceptance_criteria):
            if not isinstance(criterion, dict):
                raise ValueError(
                    f"Acceptance criterion at index {i} must be a dictionary"
                )

            # Check required fields
            if not required_fields.issubset(criterion.keys()):
                missing = required_fields - criterion.keys()
                raise ValueError(
                    f"Acceptance criterion at index {i} missing required "
                    f"fields: {missing}"
                )

            # Validate id
            if not isinstance(criterion["id"], str) or not criterion["id"].strip():
                raise ValueError(
                    f"Acceptance criterion at index {i} must have a non-empty string id"
                )
            if criterion["id"] in used_ids:
                raise ValueError(
                    f"Acceptance criterion id '{criterion['id']}' is not unique"
                )
            used_ids.add(criterion["id"])

            # Validate description
            if (
                not isinstance(criterion["description"], str)
                or not criterion["description"].strip()
            ):
                raise ValueError(
                    f"Acceptance criterion at index {i} must have a "
                    f"non-empty string description"
                )

            # Validate met
            if not isinstance(criterion["met"], bool):
                raise ValueError(
                    f"Acceptance criterion at index {i} met field must be a boolean"
                )

            # Validate order
            if not isinstance(criterion["order"], int):
                raise ValueError(
                    f"Acceptance criterion at index {i} order field must be an integer"
                )
            if criterion["order"] in used_orders:
                raise ValueError(
                    f"Acceptance criterion order {criterion['order']} is not unique"
                )
            used_orders.add(criterion["order"])

        return structured_acceptance_criteria

    @validates("comments")
    def validate_comments(self, key, comments):
        """Validate story comments."""
        if not isinstance(comments, list):
            raise ValueError("Comments must be a list")

        required_fields = {"id", "author_role", "content", "timestamp"}
        optional_fields = {"reply_to_id"}
        valid_fields = required_fields.union(optional_fields)
        used_ids = set()

        for i, comment in enumerate(comments):
            if not isinstance(comment, dict):
                raise ValueError(f"Comment at index {i} must be a dictionary")

            # Check required fields
            if not required_fields.issubset(comment.keys()):
                missing = required_fields - comment.keys()
                raise ValueError(
                    f"Comment at index {i} missing required fields: {missing}"
                )

            # Check for unexpected fields
            unexpected = set(comment.keys()) - valid_fields
            if unexpected:
                raise ValueError(
                    f"Comment at index {i} has unexpected fields: {unexpected}"
                )

            # Validate id
            if not isinstance(comment["id"], str) or not comment["id"].strip():
                raise ValueError(
                    f"Comment at index {i} must have a non-empty string id"
                )
            if comment["id"] in used_ids:
                raise ValueError(f"Comment id '{comment['id']}' is not unique")
            used_ids.add(comment["id"])

            # Validate author_role
            if (
                not isinstance(comment["author_role"], str)
                or not comment["author_role"].strip()
            ):
                raise ValueError(
                    f"Comment at index {i} must have a non-empty string author_role"
                )

            # Validate content
            if (
                not isinstance(comment["content"], str)
                or not comment["content"].strip()
            ):
                raise ValueError(
                    f"Comment at index {i} must have a non-empty string content"
                )

            # Validate timestamp (accept datetime objects or ISO format strings)
            timestamp = comment["timestamp"]
            if isinstance(timestamp, datetime):
                # Already a datetime object - valid
                pass
            elif isinstance(timestamp, str):
                # Validate it's a valid ISO format string by trying to parse it
                try:
                    from datetime import datetime as dt

                    dt.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError(
                        f"Comment at index {i} timestamp string must be in "
                        "valid ISO format"
                    )
            else:
                raise ValueError(
                    f"Comment at index {i} timestamp field must be a datetime "
                    "object or ISO format string"
                )

            # Validate reply_to_id (optional)
            if "reply_to_id" in comment:
                reply_to_id = comment["reply_to_id"]
                if reply_to_id is not None and (
                    not isinstance(reply_to_id, str) or not reply_to_id.strip()
                ):
                    raise ValueError(
                        f"Comment at index {i} reply_to_id must be None or a "
                        f"non-empty string"
                    )

        return comments

    @validates("dev_notes")
    def validate_dev_notes(self, key, dev_notes):
        """Validate story dev_notes field."""
        if dev_notes is not None:
            if not isinstance(dev_notes, str):
                raise ValueError("Dev notes must be a string")
            # Optional: Add length limit for dev_notes
            if len(dev_notes) > 10000:  # Generous limit for structured content
                raise ValueError("Dev notes cannot exceed 10000 characters")
        return dev_notes

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
