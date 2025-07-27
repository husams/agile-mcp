"""
Repository layer for Artifact data access operations.
"""

import uuid
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.artifact import Artifact
from ..models.story import Story


class ArtifactRepository:
    """Repository class for Artifact entity database operations."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def create_artifact(self, uri: str, relation: str, story_id: str) -> Artifact:
        """
        Create a new artifact linking to a story.

        Args:
            uri: The Uniform Resource Identifier for the artifact
            relation: The relationship type between artifact and story
            story_id: Foreign key reference to the linked Story

        Returns:
            Artifact: The created artifact instance

        Raises:
            SQLAlchemyError: If database operation fails
            IntegrityError: If story_id does not exist (foreign key constraint violation)
        """
        try:
            # Verify story exists before creating artifact
            story = self.db_session.query(Story).filter(Story.id == story_id).first()
            if not story:
                raise IntegrityError(
                    statement="Artifact creation failed",
                    params={"story_id": story_id},
                    orig=Exception(f"Story with id '{story_id}' does not exist"),
                )

            artifact = Artifact(
                id=str(uuid.uuid4()), uri=uri, relation=relation, story_id=story_id
            )

            self.db_session.add(artifact)
            self.db_session.commit()
            self.db_session.refresh(artifact)

            return artifact

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def find_artifact_by_id(self, artifact_id: str) -> Optional[Artifact]:
        """
        Find an artifact by its ID.

        Args:
            artifact_id: The unique identifier of the artifact

        Returns:
            Optional[Artifact]: The artifact instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Artifact)
                .filter(Artifact.id == artifact_id)
                .first()
            )
        except SQLAlchemyError as e:
            raise e

    def find_artifacts_by_story_id(self, story_id: str) -> List[Artifact]:
        """
        Find all artifacts linked to a specific story.

        Args:
            story_id: The unique identifier of the story

        Returns:
            List[Artifact]: List of artifact instances linked to the story

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Artifact)
                .filter(Artifact.story_id == story_id)
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def delete_artifact(self, artifact_id: str) -> bool:
        """
        Delete an artifact by its ID.

        Args:
            artifact_id: The unique identifier of the artifact

        Returns:
            bool: True if artifact was deleted, False if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            artifact = (
                self.db_session.query(Artifact)
                .filter(Artifact.id == artifact_id)
                .first()
            )
            if artifact:
                self.db_session.delete(artifact)
                self.db_session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
