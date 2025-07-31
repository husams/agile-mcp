"""
Repository layer for Project data access operations.
"""

import uuid
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.project import Project


class ProjectRepository:
    """Repository class for Project entity database operations."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def create_project(self, name: str, description: str) -> Project:
        """
        Create a new project.

        Args:
            name: The name of the project
            description: A detailed explanation of the project's purpose

        Returns:
            Project: The created project instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            project = Project(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
            )

            self.db_session.add(project)
            self.db_session.commit()
            self.db_session.refresh(project)

            return project

        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def find_all_projects(self) -> List[Project]:
        """
        Retrieve all projects from the database.

        Returns:
            List[Project]: List of all project instances

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return self.db_session.query(Project).all()
        except SQLAlchemyError as e:
            raise e

    def find_project_by_id(self, project_id: str) -> Optional[Project]:
        """
        Find a project by its ID.

        Args:
            project_id: The unique identifier of the project

        Returns:
            Optional[Project]: The project instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                self.db_session.query(Project).filter(Project.id == project_id).first()
            )
        except SQLAlchemyError as e:
            raise e
