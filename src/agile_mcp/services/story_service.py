"""
Service layer for Story business logic operations.
"""

from typing import List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..repositories.story_repository import StoryRepository
from ..models.story import Story
from .exceptions import StoryValidationError, StoryNotFoundError, EpicNotFoundError, DatabaseError, InvalidStoryStatusError


class StoryService:
    """Service class for Story business logic operations."""
    
    # Constants for validation
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 2000
    DEFAULT_STATUS = "ToDo"
    VALID_STATUSES = {"ToDo", "InProgress", "Review", "Done"}
    
    def __init__(self, story_repository: StoryRepository):
        """Initialize service with repository dependency."""
        self.story_repository = story_repository
    
    def create_story(self, title: str, description: str, acceptance_criteria: List[str], epic_id: str) -> Dict[str, Any]:
        """
        Create a new story with validation.
        
        Args:
            title: A short, descriptive title
            description: The full user story text
            acceptance_criteria: A list of conditions that must be met for the story to be considered complete
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
            raise StoryValidationError(f"Story title cannot exceed {self.MAX_TITLE_LENGTH} characters")
        
        if len(description.strip()) > self.MAX_DESCRIPTION_LENGTH:
            raise StoryValidationError(f"Story description cannot exceed {self.MAX_DESCRIPTION_LENGTH} characters")
        
        if not isinstance(acceptance_criteria, list):
            raise StoryValidationError("Acceptance criteria must be a non-empty list")
        
        if not acceptance_criteria or len(acceptance_criteria) == 0:
            raise StoryValidationError("At least one acceptance criterion is required")
        
        for criterion in acceptance_criteria:
            if not isinstance(criterion, str) or not criterion.strip():
                raise StoryValidationError("Each acceptance criterion must be a non-empty string")
        
        if not epic_id or not epic_id.strip():
            raise StoryValidationError("Epic ID cannot be empty")
        
        try:
            story = self.story_repository.create_story(
                title.strip(), 
                description.strip(), 
                [criterion.strip() for criterion in acceptance_criteria],
                epic_id.strip()
            )
            return story.to_dict()
        except ValueError as e:
            # Handle SQLAlchemy model validation errors
            raise StoryValidationError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations (e.g., epic_id doesn't exist)
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
            raise DatabaseError(f"Database operation failed while retrieving story: {str(e)}")
    
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
            raise DatabaseError(f"Database operation failed while retrieving stories: {str(e)}")
    
    def update_story_status(self, story_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of an existing story.
        
        Args:
            story_id: The unique identifier of the story
            status: The new status value ("ToDo", "InProgress", "Review", "Done")
            
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
            raise InvalidStoryStatusError(f"Status must be one of: {', '.join(sorted(self.VALID_STATUSES))}")
        
        try:
            story = self.story_repository.update_story_status(story_id.strip(), status)
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")
            return story.to_dict()
        except ValueError as e:
            # Handle model validation errors
            raise InvalidStoryStatusError(str(e))
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed while updating story status: {str(e)}")