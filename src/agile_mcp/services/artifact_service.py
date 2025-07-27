"""
Service layer for Artifact business logic operations.
"""

from typing import List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..repositories.artifact_repository import ArtifactRepository
from ..models.artifact import Artifact
from ..utils.validators import URIValidator, RelationValidator
from ..utils.logging_config import get_logger, create_entity_context
from .exceptions import (
    ArtifactValidationError, 
    ArtifactNotFoundError, 
    StoryNotFoundError, 
    DatabaseError, 
    InvalidRelationTypeError
)


class ArtifactService:
    """Service class for Artifact business logic operations."""
    
    # Constants for validation
    MAX_URI_LENGTH = 500
    
    def __init__(self, artifact_repository: ArtifactRepository):
        """Initialize service with repository dependency."""
        self.artifact_repository = artifact_repository
        self.logger = get_logger(__name__)
    
    def link_artifact_to_story(self, story_id: str, uri: str, relation: str) -> Dict[str, Any]:
        """
        Link an artifact to a story with validation.
        
        Args:
            story_id: The unique identifier of the story
            uri: The Uniform Resource Identifier for the artifact
            relation: The relationship type between artifact and story
            
        Returns:
            Dict[str, Any]: Dictionary representation of the created artifact
            
        Raises:
            ArtifactValidationError: If validation fails
            InvalidRelationTypeError: If relation type is invalid
            StoryNotFoundError: If story_id does not exist
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise ArtifactValidationError("Story ID cannot be empty")
        
        if not uri or not uri.strip():
            raise ArtifactValidationError("Artifact URI cannot be empty")
        
        if not relation or not relation.strip():
            raise InvalidRelationTypeError("Artifact relation cannot be empty")
        
        # Trim inputs
        story_id = story_id.strip()
        uri = uri.strip()
        relation = relation.strip()
        
        # Validate URI format and length
        try:
            uri = URIValidator.validate_uri_or_raise(uri, max_length=self.MAX_URI_LENGTH)
        except ValueError as e:
            raise ArtifactValidationError(str(e))
        
        # Validate relation type
        try:
            relation = RelationValidator.validate_relation_or_raise(relation)
        except ValueError as e:
            raise InvalidRelationTypeError(str(e))
        
        try:
            self.logger.info(
                "Linking artifact to story",
                **create_entity_context(story_id=story_id),
                uri=uri[:100],  # Truncate URI for logging
                relation=relation,
                operation="link_artifact_to_story"
            )
            
            artifact = self.artifact_repository.create_artifact(uri, relation, story_id)
            
            self.logger.info(
                "Artifact linked to story successfully",
                **create_entity_context(story_id=story_id, artifact_id=artifact.id),
                uri=uri[:100],
                relation=relation,
                operation="link_artifact_to_story"
            )
            
            return artifact.to_dict()
        except ValueError as e:
            # Handle SQLAlchemy model validation errors
            raise ArtifactValidationError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations (e.g., story_id doesn't exist)
            if "Story with id" in str(e) and "does not exist" in str(e):
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")
            raise DatabaseError(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    def get_artifacts_for_story(self, story_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all artifacts linked to a specific story.
        
        Args:
            story_id: The unique identifier of the story
            
        Returns:
            List[Dict[str, Any]]: List of artifact dictionaries
            
        Raises:
            ArtifactValidationError: If story_id is empty
            DatabaseError: If database operation fails
        """
        if not story_id or not story_id.strip():
            raise ArtifactValidationError("Story ID cannot be empty")
        
        try:
            artifacts = self.artifact_repository.find_artifacts_by_story_id(story_id.strip())
            return [artifact.to_dict() for artifact in artifacts]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed while retrieving artifacts: {str(e)}")
    
    def get_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """
        Retrieve an artifact by its ID.
        
        Args:
            artifact_id: The unique identifier of the artifact
            
        Returns:
            Dict[str, Any]: Dictionary representation of the artifact
            
        Raises:
            ArtifactNotFoundError: If artifact is not found
            DatabaseError: If database operation fails
        """
        if not artifact_id or not artifact_id.strip():
            raise ArtifactValidationError("Artifact ID cannot be empty")
        
        try:
            artifact = self.artifact_repository.find_artifact_by_id(artifact_id.strip())
            if not artifact:
                raise ArtifactNotFoundError(f"Artifact with ID '{artifact_id}' not found")
            return artifact.to_dict()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed while retrieving artifact: {str(e)}")