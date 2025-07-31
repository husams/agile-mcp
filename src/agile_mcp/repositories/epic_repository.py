"""
Repository layer for Epic data access operations.
"""

import uuid
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.epic import Epic


class EpicRepository:
    """Repository class for Epic entity database operations."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def create_epic(self, title: str, description: str, project_id: str) -> Epic:
        """
        Create a new epic with default "Draft" status.

        Args:
            title: The name of the epic
            description: A detailed explanation of the epic's goal
            project_id: The ID of the project this epic belongs to

        Returns:
            Epic: The created epic instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            epic = Epic(
                id=str(uuid.uuid4()),
                title=title,
                description=description,
                project_id=project_id,
                status="Draft",
            )

            self.db_session.add(epic)
            self.db_session.commit()
            self.db_session.refresh(epic)

            return epic

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def find_all_epics(self) -> List[Epic]:
        """
        Retrieve all epics from the database.

        Returns:
            List[Epic]: List of all epic instances

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db_session.query(Epic).all()
        except SQLAlchemyError as e:
            raise e

    def find_epic_by_id(self, epic_id: str) -> Optional[Epic]:
        """
        Find an epic by its ID.

        Args:
            epic_id: The unique identifier of the epic

        Returns:
            Optional[Epic]: The epic instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db_session.query(Epic).filter(Epic.id == epic_id).first()
        except SQLAlchemyError as e:
            raise e

    def update_epic_status(self, epic_id: str, status: str) -> Optional[Epic]:
        """
        Update the status of an epic.

        Args:
            epic_id: The unique identifier of the epic
            status: The new status value

        Returns:
            Optional[Epic]: The updated epic instance if found, None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            epic = self.db_session.query(Epic).filter(Epic.id == epic_id).first()
            if epic is None:
                return None

            epic.status = status
            self.db_session.commit()
            self.db_session.refresh(epic)

            return epic

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
