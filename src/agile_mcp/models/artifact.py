"""
Artifact data model for the Agile Management MCP Server.
"""

from typing import Any, Dict

from sqlalchemy import CheckConstraint, Column, ForeignKey, String
from sqlalchemy.orm import relationship, validates

from ..utils.validators import RelationValidator, URIValidator
from .epic import Base


class Artifact(Base):
    """
    Artifact entity representing a linked resource to a user story.

    Attributes:
        id: Unique identifier for the artifact
        uri: The Uniform Resource Identifier for the artifact
        relation: The relationship type between artifact and story
        story_id: Foreign key reference to the linked Story
    """

    __tablename__ = "artifacts"

    id = Column(String, primary_key=True)
    uri = Column(String(500), nullable=False)
    relation = Column(String(50), nullable=False)
    story_id = Column(String, ForeignKey("stories.id"), nullable=False)

    __table_args__ = (
        CheckConstraint("length(uri) <= 500", name="ck_artifact_uri_length"),
        CheckConstraint(
            "relation IN ('implementation', 'design', 'test')",
            name="ck_artifact_relation_values",
        ),
    )

    # Relationship to story (many-to-one)
    story = relationship("Story", back_populates="artifacts")

    def __init__(self, id: str, uri: str, relation: str, story_id: str):
        """Initialize Artifact with required fields."""
        self.id = id
        self.uri = uri
        self.relation = relation
        self.story_id = story_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert Artifact instance to dictionary representation."""
        return {
            "id": self.id,
            "uri": self.uri,
            "relation": self.relation,
            "story_id": self.story_id,
        }

    @validates("uri")
    def validate_uri(self, key, uri):
        """Validate artifact URI using shared validator."""
        return URIValidator.validate_uri_or_raise(uri, max_length=500)

    @validates("relation")
    def validate_relation(self, key, relation):
        """Validate artifact relation type using shared validator."""
        return RelationValidator.validate_relation_or_raise(relation)

    def __repr__(self) -> str:
        return (
            f"<Artifact(id='{self.id}', uri='{self.uri}', "
            f"relation='{self.relation}', story_id='{self.story_id}')>"
        )
