"""
Service layer for Project business logic operations.
"""

from typing import Any, Dict, List

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..repositories.project_repository import ProjectRepository
from ..utils.logging_config import create_entity_context, get_logger
from .exceptions import (
    DatabaseError,
    ProjectValidationError,
)


class ProjectService:
    """Service class for Project business logic operations."""

    # Constants for validation
    MAX_NAME_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 2000

    def __init__(self, project_repository: ProjectRepository):
        """Initialize service with repository dependency."""
        self.project_repository = project_repository
        self.logger = get_logger(__name__)

    def create_project(self, name: str, description: str) -> Dict[str, Any]:
        """
        Create a new project with validation.

        Args:
            name: The name of the project
            description: A detailed explanation of the project's purpose

        Returns:
            Dict[str, Any]: Dictionary representation of the created project

        Raises:
            ProjectValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not name or not name.strip():
            raise ProjectValidationError("Project name cannot be empty")

        if not description or not description.strip():
            raise ProjectValidationError("Project description cannot be empty")

        if len(name.strip()) > self.MAX_NAME_LENGTH:
            raise ProjectValidationError(
                f"Project name cannot exceed {self.MAX_NAME_LENGTH} characters"
            )

        if len(description.strip()) > self.MAX_DESCRIPTION_LENGTH:
            raise ProjectValidationError(
                f"Project description cannot exceed "
                f"{self.MAX_DESCRIPTION_LENGTH} characters"
            )

        try:
            self.logger.info(
                "Creating project",
                name=name.strip()[:50],  # Truncate for logging
                operation="create_project",
            )

            project = self.project_repository.create_project(
                name.strip(), description.strip()
            )

            self.logger.info(
                "Project created successfully",
                **create_entity_context(project_id=project.id),
                name=name.strip()[:50],
                operation="create_project",
            )

            return project.to_dict()
        except ValueError as e:
            # Handle SQLAlchemy model validation errors
            raise ProjectValidationError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations
            raise DatabaseError(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def find_projects(self) -> List[Dict[str, Any]]:
        """
        Retrieve all projects.

        Returns:
            List[Dict[str, Any]]: List of project dictionaries

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            projects = self.project_repository.find_all_projects()
            return [project.to_dict() for project in projects]
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while retrieving projects: {str(e)}"
            )
