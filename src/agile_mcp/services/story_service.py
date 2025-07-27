"""
Service layer for Story business logic operations.
"""

import os
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..repositories.dependency_repository import DependencyRepository
from ..repositories.story_repository import StoryRepository
from ..utils.logging_config import create_entity_context, get_logger
from ..utils.story_parser import StoryParser
from .exceptions import (
    DatabaseError,
    EpicNotFoundError,
    InvalidStoryStatusError,
    SectionNotFoundError,
    StoryNotFoundError,
    StoryValidationError,
)


class StoryService:
    """Service class for Story business logic operations."""

    # Constants for validation
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 2000
    DEFAULT_STATUS = "ToDo"
    VALID_STATUSES = {"ToDo", "InProgress", "Review", "Done"}

    def __init__(
        self,
        story_repository: StoryRepository,
        dependency_repository: Optional[DependencyRepository] = None,
    ):
        """Initialize service with repository dependencies."""
        self.story_repository = story_repository
        self.dependency_repository = dependency_repository
        self.story_parser = StoryParser()
        self.logger = get_logger(__name__)

    def create_story(
        self, title: str, description: str, acceptance_criteria: List[str], epic_id: str
    ) -> Dict[str, Any]:
        """
        Create a new story with validation.

        Args:
            title: A short, descriptive title
            description: The full user story text
            acceptance_criteria: A list of conditions that must be met for the
                story to be considered complete
            epic_id: Foreign key reference to the parent Epic

        Returns:
            Dict[str, Any]: Dictionary representation of the created story

        Raises:
            StoryValidationError: If validation fails
            EpicNotFoundError: If epic_id does not exist
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not title or not title.strip():
            raise StoryValidationError("Story title cannot be empty")

        if not description or not description.strip():
            raise StoryValidationError("Story description cannot be empty")

        if len(title.strip()) > self.MAX_TITLE_LENGTH:
            raise StoryValidationError(
                f"Story title cannot exceed {self.MAX_TITLE_LENGTH} characters"
            )

        if len(description.strip()) > self.MAX_DESCRIPTION_LENGTH:
            raise StoryValidationError(
                f"Story description cannot exceed "
                f"{self.MAX_DESCRIPTION_LENGTH} characters"
            )

        if not isinstance(acceptance_criteria, list):
            raise StoryValidationError("Acceptance criteria must be a non-empty list")

        if not acceptance_criteria or len(acceptance_criteria) == 0:
            raise StoryValidationError("At least one acceptance criterion is required")

        for criterion in acceptance_criteria:
            if not isinstance(criterion, str) or not criterion.strip():
                raise StoryValidationError(
                    "Each acceptance criterion must be a non-empty string"
                )

        if not epic_id or not epic_id.strip():
            raise StoryValidationError("Epic ID cannot be empty")

        try:
            self.logger.info(
                "Creating story",
                **create_entity_context(epic_id=epic_id.strip()),
                title=title.strip()[:50],  # Truncate for logging
                operation="create_story",
            )

            story = self.story_repository.create_story(
                title.strip(),
                description.strip(),
                [criterion.strip() for criterion in acceptance_criteria],
                epic_id.strip(),
            )

            self.logger.info(
                "Story created successfully",
                **create_entity_context(story_id=story.id, epic_id=epic_id.strip()),
                title=title.strip()[:50],
                status=story.status,
                operation="create_story",
            )

            return story.to_dict()
        except ValueError as e:
            # Handle SQLAlchemy model validation errors
            raise StoryValidationError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations
            # (e.g., epic_id doesn't exist)
            if "Epic with id" in str(e) and "does not exist" in str(e):
                raise EpicNotFoundError(f"Epic with ID '{epic_id}' not found")
            raise DatabaseError(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def get_story(self, story_id: str) -> Dict[str, Any]:
        """
        Retrieve a story by its ID.

        Args:
            story_id: The unique identifier of the story

        Returns:
            Dict[str, Any]: Dictionary representation of the story

        Raises:
            StoryNotFoundError: If story is not found
            DatabaseError: If database operation fails
        """
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        try:
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")
            return story.to_dict()
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while retrieving story: {str(e)}"
            )

    def find_stories_by_epic(self, epic_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all stories belonging to a specific epic.

        Args:
            epic_id: The unique identifier of the epic

        Returns:
            List[Dict[str, Any]]: List of story dictionaries

        Raises:
            DatabaseError: If database operation fails
        """
        if not epic_id or not epic_id.strip():
            raise StoryValidationError("Epic ID cannot be empty")

        try:
            stories = self.story_repository.find_stories_by_epic_id(epic_id.strip())
            return [story.to_dict() for story in stories]
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while retrieving stories: {str(e)}"
            )

    def update_story_status(self, story_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of an existing story.

        Args:
            story_id: The unique identifier of the story
            status: The new status value
                ("ToDo", "InProgress", "Review", "Done")

        Returns:
            Dict[str, Any]: Dictionary representation of the updated story

        Raises:
            StoryValidationError: If story_id is empty
            InvalidStoryStatusError: If status is not a valid value
            StoryNotFoundError: If story is not found
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not status or not isinstance(status, str):
            raise InvalidStoryStatusError("Status must be a non-empty string")

        if status not in self.VALID_STATUSES:
            raise InvalidStoryStatusError(
                f"Status must be one of: " f"{', '.join(sorted(self.VALID_STATUSES))}"
            )

        try:
            self.logger.info(
                "Updating story status",
                **create_entity_context(story_id=story_id.strip()),
                new_status=status,
                operation="update_story_status",
            )

            story = self.story_repository.update_story_status(story_id.strip(), status)
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            self.logger.info(
                "Story status updated successfully",
                **create_entity_context(story_id=story_id.strip()),
                old_status=getattr(story, "_previous_status", "unknown"),
                new_status=status,
                operation="update_story_status",
            )

            return story.to_dict()
        except ValueError as e:
            # Handle model validation errors
            raise InvalidStoryStatusError(str(e))
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while updating story status: " f"{str(e)}"
            )

    def get_story_section(self, story_id: str, section_name: str) -> str:
        """
        Retrieve a specific section from a story by reading its markdown
        file.

        Args:
            story_id: The unique identifier of the story
                (used to locate the markdown file)
            section_name: The name of the section to extract

        Returns:
            str: The content of the requested section

        Raises:
            StoryValidationError: If story_id or section_name is empty
            StoryNotFoundError: If story file is not found
            SectionNotFoundError: If the section is not found in the story
            DatabaseError: If file operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not section_name or not section_name.strip():
            raise StoryValidationError("Section name cannot be empty")

        # Construct file path - stories are in docs/stories/ directory
        # Story files use the format {story_id}.*.md
        # (e.g., "1.1.service-initialization.md")
        story_id_clean = story_id.strip()

        # Find the story file - it should be in docs/stories/ directory
        stories_dir = os.path.join("docs", "stories")
        if not os.path.exists(stories_dir):
            raise StoryNotFoundError(f"Stories directory '{stories_dir}' not found")

        # Look for files that start with the story_id
        story_file = None
        try:
            for filename in os.listdir(stories_dir):
                if filename.startswith(story_id_clean) and filename.endswith(".md"):
                    story_file = os.path.join(stories_dir, filename)
                    break

            if not story_file:
                raise StoryNotFoundError(
                    f"Story file for ID '{story_id}' not found in " f"'{stories_dir}'"
                )

            # Read the story file content
            with open(story_file, "r", encoding="utf-8") as f:
                story_content = f.read()

            if not story_content.strip():
                raise StoryNotFoundError(f"Story file '{story_file}' is empty")

            # Use the parser to extract the section
            try:
                section_content = self.story_parser.extract_section(
                    story_content, section_name
                )
                return section_content
            except SectionNotFoundError:
                # Re-raise with the same message
                raise
            except ValueError as e:
                # Convert parser validation errors to our exception type
                raise StoryValidationError(f"Section parsing error: {str(e)}")

        except OSError as e:
            raise DatabaseError(f"File operation failed: {str(e)}")
        except Exception as e:
            # Catch any other unexpected errors
            if isinstance(
                e, (StoryValidationError, StoryNotFoundError, SectionNotFoundError)
            ):
                raise
            raise DatabaseError(
                f"Unexpected error while processing story section: {str(e)}"
            )

    def get_next_ready_story(self) -> Optional[Dict[str, Any]]:
        """
        Get the next story that is ready for implementation.

        A story is ready if:
        - Status is "ToDo"
        - All stories it depends on have status "Done"

        Stories are ordered by:
        1. Priority (highest first)
        2. Created date (earliest first) for same priority

        When a story is retrieved, its status is automatically updated to
        "InProgress".

        Returns:
            Optional[Dict[str, Any]]: Dictionary representation of the next
                ready story,
                or None if no stories are ready

        Raises:
            DatabaseError: If database operation fails
            StoryValidationError: If dependency repository is not available
        """
        if not self.dependency_repository:
            raise StoryValidationError(
                "Dependency repository required for get_next_ready_story " "operation"
            )

        try:
            # Get all ToDo stories ordered by priority (desc) and
            # created_at (asc)
            todo_stories = self.story_repository.find_stories_by_status_ordered("ToDo")

            # Find the first story that has no incomplete dependencies
            for story in todo_stories:
                if not self.dependency_repository.has_incomplete_dependencies(story.id):
                    # This story is ready - update its status to InProgress
                    updated_story = self.story_repository.update_story_status(
                        story.id, "InProgress"
                    )
                    if updated_story:
                        return updated_story.to_dict()

            # No ready stories found
            return None

        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while finding next ready story: "
                f"{str(e)}"
            )
        except Exception as e:
            if isinstance(e, (StoryValidationError, DatabaseError)):
                raise
            raise DatabaseError(
                f"Unexpected error while finding next ready story: {str(e)}"
            )
