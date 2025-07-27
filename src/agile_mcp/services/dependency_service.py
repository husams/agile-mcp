"""
Service layer for Story Dependency business logic operations.
"""

from typing import Any, Dict, List

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..repositories.dependency_repository import DependencyRepository
from ..utils.logging_config import create_entity_context, get_logger
from .exceptions import (
    CircularDependencyError,
    DatabaseError,
    DependencyValidationError,
    DuplicateDependencyError,
    StoryNotFoundError,
)


class DependencyService:
    """Service class for Story Dependency business logic operations."""

    def __init__(self, dependency_repository: DependencyRepository):
        """Initialize service with repository dependency."""
        self.dependency_repository = dependency_repository
        self.logger = get_logger(__name__)

    def add_story_dependency(
        self, story_id: str, depends_on_story_id: str
    ) -> Dict[str, Any]:
        """
        Add a dependency relationship between two stories with comprehensive
        validation.

        Args:
            story_id: The story that will have the dependency
            depends_on_story_id: The story that must be completed first

        Returns:
            Dict[str, Any]: Success response with dependency details

        Raises:
            DependencyValidationError: If validation fails
            CircularDependencyError: If adding dependency would create a cycle
            DuplicateDependencyError: If dependency already exists
            StoryNotFoundError: If either story doesn't exist
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise DependencyValidationError("Story ID cannot be empty")

        if not depends_on_story_id or not depends_on_story_id.strip():
            raise DependencyValidationError("Dependency story ID cannot be empty")

        story_id = story_id.strip()
        depends_on_story_id = depends_on_story_id.strip()

        # Prevent self-dependency
        if story_id == depends_on_story_id:
            raise DependencyValidationError("A story cannot depend on itself")

        try:
            self.logger.info(
                "Adding story dependency",
                **create_entity_context(story_id=story_id),
                depends_on_story_id=depends_on_story_id,
                operation="add_story_dependency",
            )

            # Validate that both stories exist
            if not self.dependency_repository.story_exists(story_id):
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            if not self.dependency_repository.story_exists(depends_on_story_id):
                raise StoryNotFoundError(
                    f"Story with ID '{depends_on_story_id}' not found"
                )

            # Check for circular dependency
            if self.dependency_repository.has_circular_dependency(
                story_id, depends_on_story_id
            ):
                raise CircularDependencyError(
                    f"Adding dependency from '{story_id}' to '"
                    f"{depends_on_story_id}' would create a circular "
                    "dependency"
                )

            # Add the dependency
            result = self.dependency_repository.add_dependency(
                story_id, depends_on_story_id
            )

            if not result:
                raise DuplicateDependencyError(
                    f"Dependency from '{story_id}' to '"
                    f"{depends_on_story_id}' already exists"
                )

            self.logger.info(
                "Story dependency added successfully",
                **create_entity_context(story_id=story_id),
                depends_on_story_id=depends_on_story_id,
                operation="add_story_dependency",
            )

            return {
                "status": "success",
                "story_id": story_id,
                "depends_on_story_id": depends_on_story_id,
                "message": (
                    f"Dependency added: Story {story_id} now depends on "
                    f"Story {depends_on_story_id}"
                ),
            }

        except (
            DependencyValidationError,
            CircularDependencyError,
            DuplicateDependencyError,
            StoryNotFoundError,
        ):
            # Re-raise business logic exceptions as-is
            raise
        except IntegrityError as e:
            # Handle database constraint violations
            if "FOREIGN KEY constraint failed" in str(e):
                raise StoryNotFoundError("One or both stories do not exist")
            elif "UNIQUE constraint failed" in str(e):
                raise DuplicateDependencyError(
                    f"Dependency from '{story_id}' to '"
                    f"{depends_on_story_id}' already exists"
                )
            else:
                raise DatabaseError(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def get_story_dependencies(self, story_id: str) -> List[Dict[str, Any]]:
        """
        Get all stories that the given story depends on.

        Args:
            story_id: The story to get dependencies for

        Returns:
            List[Dict[str, Any]]: List of story dictionaries this story
                depends on

        Raises:
            DependencyValidationError: If story_id is empty
            StoryNotFoundError: If story doesn't exist
            DatabaseError: If database operation fails
        """
        if not story_id or not story_id.strip():
            raise DependencyValidationError("Story ID cannot be empty")

        story_id = story_id.strip()

        try:
            # Validate that story exists
            if not self.dependency_repository.story_exists(story_id):
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            dependencies = self.dependency_repository.get_story_dependencies(story_id)
            return [story.to_dict() for story in dependencies]

        except (DependencyValidationError, StoryNotFoundError):
            # Re-raise business logic exceptions as-is
            raise
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while retrieving dependencies: " f"{str(e)}"
            )

    def get_story_dependents(self, story_id: str) -> List[Dict[str, Any]]:
        """
        Get all stories that depend on the given story.

        Args:
            story_id: The story to get dependents for

        Returns:
            List[Dict[str, Any]]: List of story dictionaries that depend on
                this story

        Raises:
            DependencyValidationError: If story_id is empty
            StoryNotFoundError: If story doesn't exist
            DatabaseError: If database operation fails
        """
        if not story_id or not story_id.strip():
            raise DependencyValidationError("Story ID cannot be empty")

        story_id = story_id.strip()

        try:
            # Validate that story exists
            if not self.dependency_repository.story_exists(story_id):
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            dependents = self.dependency_repository.get_story_dependents(story_id)
            return [story.to_dict() for story in dependents]

        except (DependencyValidationError, StoryNotFoundError):
            # Re-raise business logic exceptions as-is
            raise
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while retrieving dependents: " f"{str(e)}"
            )

    def remove_story_dependency(
        self, story_id: str, depends_on_story_id: str
    ) -> Dict[str, Any]:
        """
        Remove a dependency relationship between two stories.

        Args:
            story_id: The story that has the dependency
            depends_on_story_id: The story it depends on

        Returns:
            Dict[str, Any]: Success response with removal details

        Raises:
            DependencyValidationError: If validation fails
            StoryNotFoundError: If dependency doesn't exist
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise DependencyValidationError("Story ID cannot be empty")

        if not depends_on_story_id or not depends_on_story_id.strip():
            raise DependencyValidationError("Dependency story ID cannot be empty")

        story_id = story_id.strip()
        depends_on_story_id = depends_on_story_id.strip()

        try:
            result = self.dependency_repository.remove_dependency(
                story_id, depends_on_story_id
            )

            if not result:
                raise StoryNotFoundError(
                    f"Dependency from '{story_id}' to '"
                    f"{depends_on_story_id}' does not exist"
                )

            return {
                "status": "success",
                "story_id": story_id,
                "depends_on_story_id": depends_on_story_id,
                "message": f"Dependency removed: Story {story_id} no longer "
                f"depends on Story {depends_on_story_id}",
            }

        except (DependencyValidationError, StoryNotFoundError):
            # Re-raise business logic exceptions as-is
            raise
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def validate_dependency_graph(self, story_id: str) -> Dict[str, Any]:
        """
        Validate the entire dependency graph for circular dependencies
        starting from a story.

        Args:
            story_id: The story to start validation from

        Returns:
            Dict[str, Any]: Validation result with any issues found

        Raises:
            DependencyValidationError: If story_id is empty
            StoryNotFoundError: If story doesn't exist
            DatabaseError: If database operation fails
        """
        if not story_id or not story_id.strip():
            raise DependencyValidationError("Story ID cannot be empty")

        story_id = story_id.strip()

        try:
            # Validate that story exists
            if not self.dependency_repository.story_exists(story_id):
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Get all dependencies for this story
            dependencies = self.dependency_repository.get_story_dependencies(story_id)

            validation_result = {
                "status": "valid",
                "story_id": story_id,
                "total_dependencies": len(dependencies),
                "dependency_chain": [dep.id for dep in dependencies],
                "issues": [],
            }

            # Check each dependency for potential issues
            for dep in dependencies:
                if self.dependency_repository.has_circular_dependency(story_id, dep.id):
                    validation_result["issues"].append(
                        {
                            "type": "circular_dependency",
                            "description": (
                                f"Circular dependency detected involving "
                                f"story {dep.id}"
                            ),
                        }
                    )
                    validation_result["status"] = "invalid"

            return validation_result

        except (DependencyValidationError, StoryNotFoundError):
            # Re-raise business logic exceptions as-is
            raise
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed during validation: {str(e)}"
            )
