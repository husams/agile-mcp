"""
Repository layer for Story data access operations.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.epic import Epic
from ..models.story import Story


class StoryRepository:
    """Repository class for Story entity database operations."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def create_story(
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        epic_id: str,
        tasks: Optional[List[Dict[str, Any]]] = None,
        structured_acceptance_criteria: Optional[List[Dict[str, Any]]] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        dev_notes: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Story:
        """
        Create a new story with default "ToDo" status.

        Args:
            title: A short, descriptive title
            description: The full user story text
            acceptance_criteria: A list of conditions that must be met for the
                story to be considered complete
            epic_id: Foreign key reference to the parent Epic
            tasks: Optional list of task dictionaries
            structured_acceptance_criteria: Optional list of structured AC dictionaries
            comments: Optional list of comment dictionaries
            dev_notes: Optional pre-compiled technical context and notes
            priority: Optional story priority (integer)

        Returns:
            Story: The created story instance

        Raises:
            SQLAlchemyError: If database operation fails
            IntegrityError: If epic_id does not exist (foreign key constraint violation)
        """
        try:
            # Verify epic exists before creating story
            epic = self.db_session.query(Epic).filter(Epic.id == epic_id).first()
            if not epic:
                raise IntegrityError(
                    statement="Story creation failed",
                    params={"epic_id": epic_id},
                    orig=Exception(f"Epic with id '{epic_id}' does not exist"),
                )

            story = Story(
                id=str(uuid.uuid4()),
                title=title,
                description=description,
                acceptance_criteria=acceptance_criteria,
                epic_id=epic_id,
                status="ToDo",
                tasks=tasks or [],
                structured_acceptance_criteria=structured_acceptance_criteria or [],
                comments=comments or [],
                dev_notes=dev_notes,
                priority=priority or 0,
            )

            self.db_session.add(story)
            self.db_session.commit()
            self.db_session.refresh(story)

            return story

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def find_story_by_id(self, story_id: str) -> Optional[Story]:
        """
        Find a story by its ID.

        Args:
            story_id: The unique identifier of the story

        Returns:
            Optional[Story]: The story instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db_session.query(Story).filter(Story.id == story_id).first()
        except SQLAlchemyError as e:
            raise e

    def find_stories_by_epic_id(self, epic_id: str) -> List[Story]:
        """
        Find all stories belonging to a specific epic.

        Args:
            epic_id: The unique identifier of the epic

        Returns:
            List[Story]: List of story instances belonging to the epic

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db_session.query(Story).filter(Story.epic_id == epic_id).all()
        except SQLAlchemyError as e:
            raise e

    def update_story_status(self, story_id: str, status: str) -> Optional[Story]:
        """
        Update the status of an existing story.

        Args:
            story_id: The unique identifier of the story
            status: The new status value

        Returns:
            Optional[Story]: The updated story instance if found, None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            story = self.db_session.query(Story).filter(Story.id == story_id).first()
            if story:
                story.status = status  # This will trigger model validation
                self.db_session.commit()
                self.db_session.refresh(story)
            return story
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def find_stories_by_status_ordered(self, status: str) -> List[Story]:
        """
        Find all stories with the given status, ordered by priority (desc) then
        created_at (asc).
        Higher priority numbers come first, then earlier creation dates.

        Args:
            status: The status to filter stories by

        Returns:
            List[Story]: List of story instances with the given status, ordered by
            priority and creation date

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Story)
                .filter(Story.status == status)
                .order_by(Story.priority.desc(), Story.created_at.asc())
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def update_story(self, story_id: str, updates: Dict[str, Any]) -> Optional[Story]:
        """
        Update story with partial field changes.

        Args:
            story_id: The unique identifier of the story
            updates: Dictionary of fields to update

        Returns:
            Optional[Story]: The updated story instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            story = self.db_session.query(Story).filter(Story.id == story_id).first()
            if not story:
                return None

            # Update basic fields
            for field, value in updates.items():
                if hasattr(story, field):
                    setattr(story, field, value)

                    # For JSON fields, need to flag as modified
                    if field in ["tasks", "structured_acceptance_criteria", "comments"]:
                        from sqlalchemy.orm.attributes import flag_modified

                        flag_modified(story, field)

            self.db_session.commit()
            self.db_session.refresh(story)
            return story

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
