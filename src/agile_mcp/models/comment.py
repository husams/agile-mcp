"""
Comment data model for the Agile Management MCP Server.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .epic import Base


class AuthorRole(Enum):
    """Enumeration of predefined author roles for comments."""
    
    DEVELOPER_AGENT = "Developer Agent"
    QA_AGENT = "QA Agent"
    SCRUM_MASTER = "Scrum Master"
    PRODUCT_OWNER = "Product Owner"
    HUMAN_REVIEWER = "Human Reviewer"
    SYSTEM = "System"

    @classmethod
    def get_valid_roles(cls) -> list[str]:
        """Get list of valid role values."""
        return [role.value for role in cls]

    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """Check if a role value is valid."""
        return role in cls.get_valid_roles()

    def __str__(self) -> str:
        """Return the role value as string."""
        return self.value


class Comment(Base):
    """
    Comment entity representing feedback on a story.

    Attributes:
        id: Unique identifier for the comment
        story_id: Foreign key reference to the parent Story
        author_role: The role of the comment author (enum)
        content: The comment text content
        timestamp: When the comment was created
        reply_to_id: Optional foreign key for threaded comments (self-reference)
    """

    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    story_id: Mapped[str] = mapped_column(String, ForeignKey("stories.id"), nullable=False)
    author_role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    reply_to_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("comments.id"), nullable=True
    )

    # Relationship to story (many-to-one)
    story = relationship("Story", back_populates="story_comments")

    def __init__(
        self,
        id: str,
        story_id: str,
        author_role: str,
        content: str,
        reply_to_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Initialize Comment with auto-generated timestamp."""
        super().__init__()
        self.id = id
        self.story_id = story_id
        self.author_role = author_role
        self.content = content
        self.reply_to_id = reply_to_id
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Comment instance to dictionary representation."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "author_role": self.author_role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "reply_to_id": self.reply_to_id,
        }

    @validates("author_role")
    def validate_author_role(self, key, author_role):
        """Validate author role against predefined enumeration."""
        if not AuthorRole.is_valid_role(author_role):
            valid_roles = ", ".join(AuthorRole.get_valid_roles())
            raise ValueError(f"Author role must be one of: {valid_roles}")
        return author_role

    @validates("content")
    def validate_content(self, key, content):
        """Validate comment content."""
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")
        
        # Set reasonable maximum length for comment content
        max_length = 10000
        if len(content.strip()) > max_length:
            raise ValueError(f"Comment content cannot exceed {max_length} characters")
        
        return content.strip()

    @validates("reply_to_id")
    def validate_reply_to_id(self, key, reply_to_id):
        """Validate reply_to_id to prevent circular references."""
        if reply_to_id is not None:
            if not isinstance(reply_to_id, str) or not reply_to_id.strip():
                raise ValueError("reply_to_id must be None or a non-empty string")
            
            # Prevent self-referencing
            if reply_to_id == getattr(self, 'id', None):
                raise ValueError("Comment cannot reply to itself")
        
        return reply_to_id

    def __repr__(self) -> str:
        return (
            f"<Comment(id='{self.id}', story_id='{self.story_id}', "
            f"author_role='{self.author_role}', reply_to='{self.reply_to_id}')>"
        )


# Add self-referential relationships after the class definition
Comment.replies = relationship(
    "Comment",
    backref="parent_comment",
    remote_side=[Comment.id],
    foreign_keys=[Comment.reply_to_id]
)