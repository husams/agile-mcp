"""
Repository layer for Story Dependency data access operations.
"""

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.story import Story
from ..models.story_dependency import story_dependencies


class DependencyRepository:
    """Repository class for Story Dependency database operations."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def add_dependency(self, story_id: str, depends_on_story_id: str) -> bool:
        """
        Add a dependency relationship between two stories.

        Args:
            story_id: The story that has the dependency
            depends_on_story_id: The story that must be completed first

        Returns:
            bool: True if dependency was added successfully

        Raises:
            SQLAlchemyError: If database operation fails
            IntegrityError: If foreign key constraint violation or duplicate dependency
        """
        try:
            # Check if dependency already exists
            existing = self.db_session.execute(
                text(
                    "SELECT 1 FROM story_dependencies WHERE story_id = :story_id AND depends_on_story_id = :depends_on_story_id"
                ),
                {"story_id": story_id, "depends_on_story_id": depends_on_story_id},
            ).first()

            if existing:
                return False  # Dependency already exists

            # Insert new dependency
            self.db_session.execute(
                text(
                    "INSERT INTO story_dependencies (story_id, depends_on_story_id) VALUES (:story_id, :depends_on_story_id)"
                ),
                {"story_id": story_id, "depends_on_story_id": depends_on_story_id},
            )

            self.db_session.commit()
            return True

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_story_dependencies(self, story_id: str) -> List[Story]:
        """
        Get all stories that the given story depends on.

        Args:
            story_id: The story to get dependencies for

        Returns:
            List[Story]: List of stories this story depends on

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Story)
                .join(
                    story_dependencies,
                    Story.id == story_dependencies.c.depends_on_story_id,
                )
                .filter(story_dependencies.c.story_id == story_id)
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def get_story_dependents(self, story_id: str) -> List[Story]:
        """
        Get all stories that depend on the given story.

        Args:
            story_id: The story to get dependents for

        Returns:
            List[Story]: List of stories that depend on this story

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Story)
                .join(story_dependencies, Story.id == story_dependencies.c.story_id)
                .filter(story_dependencies.c.depends_on_story_id == story_id)
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def story_exists(self, story_id: str) -> bool:
        """
        Check if a story exists in the database.

        Args:
            story_id: The story ID to check

        Returns:
            bool: True if story exists, False otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Story).filter(Story.id == story_id).first()
                is not None
            )
        except SQLAlchemyError as e:
            raise e

    def has_circular_dependency(self, story_id: str, depends_on_story_id: str) -> bool:
        """
        Check if adding this dependency would create a circular dependency.
        Uses depth-first search to detect cycles.

        Args:
            story_id: The story that would have the dependency
            depends_on_story_id: The story it would depend on

        Returns:
            bool: True if adding this dependency would create a cycle, False otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            visited = set()

            def dfs(current_story_id: str) -> bool:
                if current_story_id == story_id:  # Found cycle back to original
                    return True
                if current_story_id in visited:  # Already processed
                    return False

                visited.add(current_story_id)

                # Get all stories that current_story_id depends on
                dependencies = self.get_story_dependencies(current_story_id)
                for dep in dependencies:
                    if dfs(dep.id):
                        return True
                return False

            return dfs(depends_on_story_id)

        except SQLAlchemyError as e:
            raise e

    def remove_dependency(self, story_id: str, depends_on_story_id: str) -> bool:
        """
        Remove a dependency relationship between two stories.

        Args:
            story_id: The story that has the dependency
            depends_on_story_id: The story it depends on

        Returns:
            bool: True if dependency was removed, False if it didn't exist

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            result = self.db_session.execute(
                text(
                    "DELETE FROM story_dependencies WHERE story_id = :story_id AND depends_on_story_id = :depends_on_story_id"
                ),
                {"story_id": story_id, "depends_on_story_id": depends_on_story_id},
            )

            self.db_session.commit()
            return result.rowcount > 0

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def has_incomplete_dependencies(self, story_id: str) -> bool:
        """
        Check if a story has any incomplete dependencies.
        A dependency is incomplete if the story it depends on has status other than "Done".

        Args:
            story_id: The story to check dependencies for

        Returns:
            bool: True if story has incomplete dependencies, False otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get count of dependencies that are not "Done"
            incomplete_count = (
                self.db_session.query(Story)
                .join(
                    story_dependencies,
                    Story.id == story_dependencies.c.depends_on_story_id,
                )
                .filter(story_dependencies.c.story_id == story_id)
                .filter(Story.status != "Done")
                .count()
            )

            return incomplete_count > 0

        except SQLAlchemyError as e:
            raise e
