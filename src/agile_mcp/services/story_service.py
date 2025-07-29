"""
Service layer for Story business logic operations.
"""

import os
import uuid
from datetime import datetime, timezone
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
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        epic_id: str,
        tasks: Optional[List[Dict[str, Any]]] = None,
        structured_acceptance_criteria: Optional[List[Dict[str, Any]]] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new story with validation.

        Args:
            title: A short, descriptive title
            description: The full user story text
            acceptance_criteria: A list of conditions that must be met for the
                story to be considered complete
            epic_id: Foreign key reference to the parent Epic
            tasks: Optional list of task dictionaries with id, description,
                completed, order
            structured_acceptance_criteria: Optional list of structured AC
                dictionaries
            comments: Optional list of comment dictionaries
            priority: Optional story priority (integer)

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

        # Validate structured fields if provided
        if tasks is not None:
            self._validate_tasks(tasks)
        if structured_acceptance_criteria is not None:
            self._validate_structured_acceptance_criteria(
                structured_acceptance_criteria
            )
        if comments is not None:
            self._validate_comments(comments)

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
                tasks=tasks or [],
                structured_acceptance_criteria=structured_acceptance_criteria or [],
                comments=comments or [],
                priority=priority,
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

    def update_story(
        self,
        story_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        acceptance_criteria: Optional[List[str]] = None,
        tasks: Optional[List[Dict[str, Any]]] = None,
        structured_acceptance_criteria: Optional[List[Dict[str, Any]]] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update story with partial field updates.

        Args:
            story_id: The unique identifier of the story
            title: Optional new title
            description: Optional new description
            acceptance_criteria: Optional new acceptance criteria list
            tasks: Optional new tasks list
            structured_acceptance_criteria: Optional new structured AC list
            comments: Optional new comments list
            status: Optional new status

        Returns:
            Dict[str, Any]: Dictionary representation of the updated story

        Raises:
            StoryValidationError: If validation fails
            StoryNotFoundError: If story is not found
            DatabaseError: If database operation fails
        """
        # Validate story_id
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        # Validate structured fields if provided
        if tasks is not None:
            self._validate_tasks(tasks)
        if structured_acceptance_criteria is not None:
            self._validate_structured_acceptance_criteria(
                structured_acceptance_criteria
            )
        if comments is not None:
            self._validate_comments(comments)

        # Validate basic fields if provided
        if title is not None:
            if not title or not title.strip():
                raise StoryValidationError("Story title cannot be empty")
            if len(title.strip()) > self.MAX_TITLE_LENGTH:
                raise StoryValidationError(
                    f"Story title cannot exceed {self.MAX_TITLE_LENGTH} characters"
                )

        if description is not None:
            if not description or not description.strip():
                raise StoryValidationError("Story description cannot be empty")
            if len(description.strip()) > self.MAX_DESCRIPTION_LENGTH:
                raise StoryValidationError(
                    f"Story description cannot exceed "
                    f"{self.MAX_DESCRIPTION_LENGTH} characters"
                )

        if acceptance_criteria is not None:
            if not isinstance(acceptance_criteria, list):
                raise StoryValidationError("Acceptance criteria must be a list")
            if not acceptance_criteria or len(acceptance_criteria) == 0:
                raise StoryValidationError(
                    "At least one acceptance criterion is required"
                )
            for criterion in acceptance_criteria:
                if not isinstance(criterion, str) or not criterion.strip():
                    raise StoryValidationError(
                        "Each acceptance criterion must be a non-empty string"
                    )

        if status is not None:
            if not status or not isinstance(status, str):
                raise StoryValidationError("Status must be a non-empty string")
            if status not in self.VALID_STATUSES:
                raise StoryValidationError(
                    f"Status must be one of: {', '.join(sorted(self.VALID_STATUSES))}"
                )

        try:
            self.logger.info(
                "Updating story",
                **create_entity_context(story_id=story_id.strip()),
                operation="update_story",
            )

            # Prepare updates dictionary
            updates: Dict[str, Any] = {}
            if title is not None:
                updates["title"] = title.strip()
            if description is not None:
                updates["description"] = description.strip()
            if acceptance_criteria is not None:
                updates["acceptance_criteria"] = [
                    criterion.strip() for criterion in acceptance_criteria
                ]
            if tasks is not None:
                updates["tasks"] = tasks
            if structured_acceptance_criteria is not None:
                updates["structured_acceptance_criteria"] = (
                    structured_acceptance_criteria
                )
            if comments is not None:
                updates["comments"] = comments
            if status is not None:
                updates["status"] = status

            story = self.story_repository.update_story(story_id.strip(), updates)
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            self.logger.info(
                "Story updated successfully",
                **create_entity_context(story_id=story_id.strip()),
                operation="update_story",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle SQLAlchemy model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while updating story: {str(e)}"
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

    def add_task_to_story(
        self, story_id: str, description: str, order: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a new task to a story.

        Args:
            story_id: The unique identifier of the story
            description: Description of the task
            order: Optional order for the task (auto-incremented if not provided)

        Returns:
            Dict: Updated story with the new task

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not description or not description.strip():
            raise StoryValidationError("Task description cannot be empty")

        try:
            self.logger.info(
                "Adding task to story",
                **create_entity_context(story_id=story_id.strip()),
                task_description=description[:50] if description else None,
                operation="add_task_to_story",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Generate task ID and determine order
            task_id = str(uuid.uuid4())
            if order is None:
                existing_orders = [task.get("order", 0) for task in story.tasks]
                order = max(existing_orders, default=0) + 1

            # Create new task
            new_task = {
                "id": task_id,
                "description": description.strip(),
                "completed": False,
                "order": order,
            }

            # Add task to story
            updated_tasks = story.tasks + [new_task]
            story.tasks = updated_tasks

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "tasks")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Task added to story successfully",
                **create_entity_context(story_id=story_id.strip()),
                task_id=task_id,
                operation="add_task_to_story",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while adding task to story: {str(e)}"
            )

    def update_task_status(
        self, story_id: str, task_id: str, completed: bool
    ) -> Dict[str, Any]:
        """
        Update the completion status of a task within a story.

        Args:
            story_id: The unique identifier of the story
            task_id: The unique identifier of the task
            completed: New completion status

        Returns:
            Dict: Updated story with modified task

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If task not found or validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not task_id or not task_id.strip():
            raise StoryValidationError("Task ID cannot be empty")

        try:
            self.logger.info(
                "Updating task status",
                **create_entity_context(story_id=story_id.strip()),
                task_id=task_id.strip(),
                new_completed=completed,
                operation="update_task_status",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Find and update the task
            task_found = False
            updated_tasks = []
            for task in story.tasks:
                if task["id"] == task_id.strip():
                    task["completed"] = completed
                    task_found = True
                updated_tasks.append(task)

            if not task_found:
                raise StoryValidationError(
                    f"Task with ID '{task_id}' not found in story"
                )

            # Set the updated tasks list to trigger SQLAlchemy change detection
            story.tasks = updated_tasks

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "tasks")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Task status updated successfully",
                **create_entity_context(story_id=story_id.strip()),
                task_id=task_id.strip(),
                new_completed=completed,
                operation="update_task_status",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while updating task status: {str(e)}"
            )

    def update_task_description(
        self, story_id: str, task_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Update the description of a task within a story.

        Args:
            story_id: The unique identifier of the story
            task_id: The unique identifier of the task
            description: New task description

        Returns:
            Dict: Updated story with modified task

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If task not found or validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not task_id or not task_id.strip():
            raise StoryValidationError("Task ID cannot be empty")

        if not description or not description.strip():
            raise StoryValidationError("Task description cannot be empty")

        try:
            self.logger.info(
                "Updating task description",
                **create_entity_context(story_id=story_id.strip()),
                task_id=task_id.strip(),
                new_description=description[:50] if description else None,
                operation="update_task_description",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Find and update the task
            task_found = False
            updated_tasks = []
            for task in story.tasks:
                if task["id"] == task_id.strip():
                    task["description"] = description.strip()
                    task_found = True
                updated_tasks.append(task)

            if not task_found:
                raise StoryValidationError(
                    f"Task with ID '{task_id}' not found in story"
                )

            # Set the updated tasks list to trigger SQLAlchemy change detection
            story.tasks = updated_tasks

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "tasks")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Task description updated successfully",
                **create_entity_context(story_id=story_id.strip()),
                task_id=task_id.strip(),
                operation="update_task_description",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while updating task description: {str(e)}"
            )

    def reorder_tasks(
        self, story_id: str, task_orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reorder tasks within a story.

        Args:
            story_id: The unique identifier of the story
            task_orders: List of dicts with task_id and new order
                Format: [{'task_id': 'id1', 'order': 1}, {'task_id': 'id2', 'order': 2}]

        Returns:
            Dict: Updated story with reordered tasks

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not isinstance(task_orders, list):
            raise StoryValidationError("Task orders must be a list")

        try:
            self.logger.info(
                "Reordering tasks in story",
                **create_entity_context(story_id=story_id.strip()),
                task_count=len(task_orders),
                operation="reorder_tasks",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Create mapping of task_id to new order
            order_mapping = {}
            for item in task_orders:
                if (
                    not isinstance(item, dict)
                    or "task_id" not in item
                    or "order" not in item
                ):
                    raise StoryValidationError(
                        "Each task order item must have 'task_id' and 'order' fields"
                    )
                order_mapping[item["task_id"]] = item["order"]

            # Update task orders
            for task in story.tasks:
                if task["id"] in order_mapping:
                    task["order"] = order_mapping[task["id"]]

            # Set tasks to trigger validation and change detection
            story.tasks = story.tasks

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "tasks")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Tasks reordered successfully",
                **create_entity_context(story_id=story_id.strip()),
                operation="reorder_tasks",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while reordering tasks: {str(e)}"
            )

    def add_acceptance_criterion_to_story(
        self, story_id: str, description: str, order: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a new acceptance criterion to a story.

        Args:
            story_id: The unique identifier of the story
            description: Description of the acceptance criterion
            order: Optional order for the criterion (auto-incremented if not provided)

        Returns:
            Dict: Updated story with the new acceptance criterion

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not description or not description.strip():
            raise StoryValidationError(
                "Acceptance criterion description cannot be empty"
            )

        try:
            self.logger.info(
                "Adding acceptance criterion to story",
                **create_entity_context(story_id=story_id.strip()),
                criterion_description=description[:50] if description else None,
                operation="add_acceptance_criterion_to_story",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Generate criterion ID and determine order
            criterion_id = str(uuid.uuid4())
            if order is None:
                existing_orders = [
                    criterion.get("order", 0)
                    for criterion in story.structured_acceptance_criteria
                ]
                order = max(existing_orders, default=0) + 1

            # Create new acceptance criterion
            new_criterion = {
                "id": criterion_id,
                "description": description.strip(),
                "met": False,
                "order": order,
            }

            # Add criterion to story
            updated_criteria = story.structured_acceptance_criteria + [new_criterion]
            story.structured_acceptance_criteria = updated_criteria

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "structured_acceptance_criteria")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Acceptance criterion added to story successfully",
                **create_entity_context(story_id=story_id.strip()),
                criterion_id=criterion_id,
                operation="add_acceptance_criterion_to_story",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while adding acceptance "
                f"criterion to story: {str(e)}"
            )

    def update_acceptance_criterion_status(
        self, story_id: str, criterion_id: str, met: bool
    ) -> Dict[str, Any]:
        """
        Update the met status of an acceptance criterion within a story.

        Args:
            story_id: The unique identifier of the story
            criterion_id: The unique identifier of the acceptance criterion
            met: New met status

        Returns:
            Dict: Updated story with modified acceptance criterion

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If criterion not found or validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not criterion_id or not criterion_id.strip():
            raise StoryValidationError("Acceptance criterion ID cannot be empty")

        try:
            self.logger.info(
                "Updating acceptance criterion status",
                **create_entity_context(story_id=story_id.strip()),
                criterion_id=criterion_id.strip(),
                new_met=met,
                operation="update_acceptance_criterion_status",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Find and update the acceptance criterion
            criterion_found = False
            updated_criteria = []
            for criterion in story.structured_acceptance_criteria:
                if criterion["id"] == criterion_id.strip():
                    criterion["met"] = met
                    criterion_found = True
                updated_criteria.append(criterion)

            if not criterion_found:
                raise StoryValidationError(
                    f"Acceptance criterion with ID '{criterion_id}' not found in story"
                )

            # Set the updated criteria list to trigger SQLAlchemy change detection
            story.structured_acceptance_criteria = updated_criteria

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "structured_acceptance_criteria")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Acceptance criterion status updated successfully",
                **create_entity_context(story_id=story_id.strip()),
                criterion_id=criterion_id.strip(),
                new_met=met,
                operation="update_acceptance_criterion_status",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while updating acceptance "
                f"criterion status: {str(e)}"
            )

    def update_acceptance_criterion_description(
        self, story_id: str, criterion_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Update the description of an acceptance criterion within a story.

        Args:
            story_id: The unique identifier of the story
            criterion_id: The unique identifier of the acceptance criterion
            description: New criterion description

        Returns:
            Dict: Updated story with modified acceptance criterion

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If criterion not found or validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not criterion_id or not criterion_id.strip():
            raise StoryValidationError("Acceptance criterion ID cannot be empty")

        if not description or not description.strip():
            raise StoryValidationError(
                "Acceptance criterion description cannot be empty"
            )

        try:
            self.logger.info(
                "Updating acceptance criterion description",
                **create_entity_context(story_id=story_id.strip()),
                criterion_id=criterion_id.strip(),
                new_description=description[:50] if description else None,
                operation="update_acceptance_criterion_description",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Find and update the acceptance criterion
            criterion_found = False
            updated_criteria = []
            for criterion in story.structured_acceptance_criteria:
                if criterion["id"] == criterion_id.strip():
                    criterion["description"] = description.strip()
                    criterion_found = True
                updated_criteria.append(criterion)

            if not criterion_found:
                raise StoryValidationError(
                    f"Acceptance criterion with ID '{criterion_id}' not found in story"
                )

            # Set the updated criteria list to trigger SQLAlchemy change detection
            story.structured_acceptance_criteria = updated_criteria

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "structured_acceptance_criteria")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Acceptance criterion description updated successfully",
                **create_entity_context(story_id=story_id.strip()),
                criterion_id=criterion_id.strip(),
                operation="update_acceptance_criterion_description",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while updating acceptance "
                f"criterion description: {str(e)}"
            )

    def reorder_acceptance_criteria(
        self, story_id: str, criterion_orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reorder acceptance criteria within a story.

        Args:
            story_id: The unique identifier of the story
            criterion_orders: List of dicts with criterion_id and new order
                Format: [{'criterion_id': 'id1', 'order': 1},
                {'criterion_id': 'id2', 'order': 2}]

        Returns:
            Dict: Updated story with reordered acceptance criteria

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not criterion_orders or not isinstance(criterion_orders, list):
            raise StoryValidationError("Criterion orders must be a non-empty list")

        try:
            self.logger.info(
                "Reordering acceptance criteria",
                **create_entity_context(story_id=story_id.strip()),
                criterion_count=len(criterion_orders),
                operation="reorder_acceptance_criteria",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Create mapping of criterion_id to new order
            order_mapping = {}
            for item in criterion_orders:
                if (
                    not isinstance(item, dict)
                    or "criterion_id" not in item
                    or "order" not in item
                ):
                    raise StoryValidationError(
                        "Each criterion order item must have 'criterion_id' "
                        "and 'order' fields"
                    )
                order_mapping[item["criterion_id"]] = item["order"]

            # Update criterion orders
            for criterion in story.structured_acceptance_criteria:
                if criterion["id"] in order_mapping:
                    criterion["order"] = order_mapping[criterion["id"]]

            # Set criteria to trigger validation and change detection
            story.structured_acceptance_criteria = story.structured_acceptance_criteria

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "structured_acceptance_criteria")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Acceptance criteria reordered successfully",
                **create_entity_context(story_id=story_id.strip()),
                operation="reorder_acceptance_criteria",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while reordering acceptance "
                f"criteria: {str(e)}"
            )

    def add_comment_to_story(
        self,
        story_id: str,
        author_role: str,
        content: str,
        reply_to_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a new comment to a story.

        Args:
            story_id: The unique identifier of the story
            author_role: Role of commenter (e.g., 'Developer Agent', 'QA Agent',
                'Human Reviewer')
            content: The comment text content
            reply_to_id: Optional ID of comment this is replying to for threading

        Returns:
            Dict: Updated story with the new comment

        Raises:
            StoryNotFoundError: If story is not found
            StoryValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not story_id or not story_id.strip():
            raise StoryValidationError("Story ID cannot be empty")

        if not author_role or not author_role.strip():
            raise StoryValidationError("Author role cannot be empty")

        if not content or not content.strip():
            raise StoryValidationError("Comment content cannot be empty")

        try:
            self.logger.info(
                "Adding comment to story",
                **create_entity_context(story_id=story_id.strip()),
                author_role=author_role,
                content_preview=content[:50] if content else None,
                operation="add_comment_to_story",
            )

            # Get the story
            story = self.story_repository.find_story_by_id(story_id.strip())
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Validate reply_to_id if provided
            if reply_to_id:
                reply_to_id = reply_to_id.strip()
                if reply_to_id:
                    existing_comment_ids = [
                        comment.get("id") for comment in story.comments
                    ]
                    if reply_to_id not in existing_comment_ids:
                        raise StoryValidationError(
                            f"Reply to comment ID '{reply_to_id}' not found"
                        )

            # Generate comment ID and create new comment
            comment_id = str(uuid.uuid4())
            new_comment = {
                "id": comment_id,
                "author_role": author_role.strip(),
                "content": content.strip(),
                "timestamp": datetime.now(timezone.utc),
                "reply_to_id": reply_to_id if reply_to_id else None,
            }

            # Add the comment to the story
            story.comments.append(new_comment)

            # Set comments to trigger validation and change detection
            story.comments = story.comments

            # Force SQLAlchemy to recognize the change
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(story, "comments")

            # Save changes
            self.story_repository.db_session.commit()
            self.story_repository.db_session.refresh(story)

            self.logger.info(
                "Comment added to story successfully",
                **create_entity_context(story_id=story_id.strip()),
                comment_id=comment_id,
                operation="add_comment_to_story",
            )

            return story.to_dict()

        except ValueError as e:
            # Handle model validation errors
            raise StoryValidationError(str(e))
        except SQLAlchemyError as e:
            self.story_repository.db_session.rollback()
            raise DatabaseError(
                f"Database operation failed while adding comment: {str(e)}"
            )

    def _validate_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """Validate task structure and content."""
        if not isinstance(tasks, list):
            raise StoryValidationError("Tasks must be a list")

        seen_ids = set()
        seen_orders = set()

        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise StoryValidationError(f"Task {i} must be a dictionary")

            # Check required fields
            required_fields = ["id", "description", "completed", "order"]
            for field in required_fields:
                if field not in task:
                    raise StoryValidationError(
                        f"Task {i} missing required field '{field}'"
                    )

            # Validate field types and values
            task_id = task["id"]
            if not isinstance(task_id, str) or not task_id.strip():
                raise StoryValidationError(f"Task {i} id must be a non-empty string")

            if task_id in seen_ids:
                raise StoryValidationError(f"Duplicate task id '{task_id}'")
            seen_ids.add(task_id)

            if (
                not isinstance(task["description"], str)
                or not task["description"].strip()
            ):
                raise StoryValidationError(
                    f"Task {i} description must be a non-empty string"
                )

            if not isinstance(task["completed"], bool):
                raise StoryValidationError(f"Task {i} completed must be a boolean")

            if not isinstance(task["order"], int) or task["order"] < 1:
                raise StoryValidationError(f"Task {i} order must be a positive integer")

            if task["order"] in seen_orders:
                raise StoryValidationError(f"Duplicate task order {task['order']}")
            seen_orders.add(task["order"])

    def _validate_structured_acceptance_criteria(
        self, criteria: List[Dict[str, Any]]
    ) -> None:
        """Validate structured acceptance criteria structure and content."""
        if not isinstance(criteria, list):
            raise StoryValidationError("Structured acceptance criteria must be a list")

        seen_ids = set()
        seen_orders = set()

        for i, criterion in enumerate(criteria):
            if not isinstance(criterion, dict):
                raise StoryValidationError(
                    f"Acceptance criterion {i} must be a dictionary"
                )

            # Check required fields
            required_fields = ["id", "description", "met", "order"]
            for field in required_fields:
                if field not in criterion:
                    raise StoryValidationError(
                        f"Acceptance criterion {i} missing required field '{field}'"
                    )

            # Validate field types and values
            criterion_id = criterion["id"]
            if not isinstance(criterion_id, str) or not criterion_id.strip():
                raise StoryValidationError(
                    f"Acceptance criterion {i} id must be a non-empty string"
                )

            if criterion_id in seen_ids:
                raise StoryValidationError(
                    f"Duplicate acceptance criterion id '{criterion_id}'"
                )
            seen_ids.add(criterion_id)

            if (
                not isinstance(criterion["description"], str)
                or not criterion["description"].strip()
            ):
                raise StoryValidationError(
                    f"Acceptance criterion {i} description must be a non-empty string"
                )

            if not isinstance(criterion["met"], bool):
                raise StoryValidationError(
                    f"Acceptance criterion {i} met must be a boolean"
                )

            if not isinstance(criterion["order"], int) or criterion["order"] < 1:
                raise StoryValidationError(
                    f"Acceptance criterion {i} order must be a positive integer"
                )

            if criterion["order"] in seen_orders:
                raise StoryValidationError(
                    f"Duplicate acceptance criterion order {criterion['order']}"
                )
            seen_orders.add(criterion["order"])

    def _validate_comments(self, comments: List[Dict[str, Any]]) -> None:
        """Validate comment structure and content."""
        if not isinstance(comments, list):
            raise StoryValidationError("Comments must be a list")

        seen_ids = set()

        for i, comment in enumerate(comments):
            if not isinstance(comment, dict):
                raise StoryValidationError(f"Comment {i} must be a dictionary")

            # Check required fields
            required_fields = ["id", "author_role", "content", "timestamp"]
            for field in required_fields:
                if field not in comment:
                    raise StoryValidationError(
                        f"Comment {i} missing required field '{field}'"
                    )

            # Validate field types and values
            comment_id = comment["id"]
            if not isinstance(comment_id, str) or not comment_id.strip():
                raise StoryValidationError(f"Comment {i} id must be a non-empty string")

            if comment_id in seen_ids:
                raise StoryValidationError(f"Duplicate comment id '{comment_id}'")
            seen_ids.add(comment_id)

            if (
                not isinstance(comment["author_role"], str)
                or not comment["author_role"].strip()
            ):
                raise StoryValidationError(
                    f"Comment {i} author_role must be a non-empty string"
                )

            if (
                not isinstance(comment["content"], str)
                or not comment["content"].strip()
            ):
                raise StoryValidationError(
                    f"Comment {i} content must be a non-empty string"
                )

            # timestamp validation is flexible - can be datetime or string
            # reply_to_id is optional
