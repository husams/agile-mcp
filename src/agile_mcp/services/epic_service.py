"""
Service layer for Epic business logic operations.
"""

from typing import Any, Dict, List

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..repositories.epic_repository import EpicRepository
from ..utils.logging_config import create_entity_context, get_logger
from .exceptions import (
    DatabaseError,
    EpicNotFoundError,
    EpicValidationError,
    InvalidEpicStatusError,
)


class EpicService:
    """Service class for Epic business logic operations."""

    # Constants for validation
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 2000
    DEFAULT_STATUS = "Draft"
    VALID_STATUSES = {"Draft", "Ready", "In Progress", "Done", "On Hold"}

    def __init__(self, epic_repository: EpicRepository):
        """Initialize service with repository dependency."""
        self.epic_repository = epic_repository
        self.logger = get_logger(__name__)

    def create_epic(self, title: str, description: str) -> Dict[str, Any]:
        """
        Create a new epic with validation.

        Args:
            title: The name of the epic
            description: A detailed explanation of the epic's goal

        Returns:
            Dict[str, Any]: Dictionary representation of the created epic

        Raises:
            EpicValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate input parameters
        if not title or not title.strip():
            raise EpicValidationError("Epic title cannot be empty")

        if not description or not description.strip():
            raise EpicValidationError("Epic description cannot be empty")

        if len(title.strip()) > self.MAX_TITLE_LENGTH:
            raise EpicValidationError(
                f"Epic title cannot exceed {self.MAX_TITLE_LENGTH} characters"
            )

        if len(description.strip()) > self.MAX_DESCRIPTION_LENGTH:
            raise EpicValidationError(
                f"Epic description cannot exceed "
                f"{self.MAX_DESCRIPTION_LENGTH} characters"
            )

        try:
            self.logger.info(
                "Creating epic",
                title=title.strip()[:50],  # Truncate for logging
                operation="create_epic",
            )

            epic = self.epic_repository.create_epic(title.strip(), description.strip())

            self.logger.info(
                "Epic created successfully",
                **create_entity_context(epic_id=epic.id),
                title=title.strip()[:50],
                status=epic.status,
                operation="create_epic",
            )

            return epic.to_dict()
        except ValueError as e:
            # Handle SQLAlchemy model validation errors
            raise EpicValidationError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations
            raise DatabaseError(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def find_epics(self) -> List[Dict[str, Any]]:
        """
        Retrieve all epics.

        Returns:
            List[Dict[str, Any]]: List of epic dictionaries

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            epics = self.epic_repository.find_all_epics()
            return [epic.to_dict() for epic in epics]
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database operation failed while retrieving epics: {str(e)}"
            )

    def update_epic_status(self, epic_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of an epic.

        Args:
            epic_id: The unique identifier of the epic
            status: The new status value

        Returns:
            Dict[str, Any]: Dictionary representation of the updated epic

        Raises:
            EpicNotFoundError: If epic is not found
            InvalidEpicStatusError: If status is invalid
            DatabaseError: If database operation fails
        """
        # Validate epic_id parameter
        if not epic_id or not epic_id.strip():
            raise EpicNotFoundError("Epic ID cannot be empty")

        # Validate status parameter
        if not status or not status.strip():
            raise InvalidEpicStatusError("Epic status cannot be empty")

        status = status.strip()
        if status not in self.VALID_STATUSES:
            raise InvalidEpicStatusError(
                f"Epic status must be one of: "
                f"{', '.join(sorted(self.VALID_STATUSES))}"
            )

        try:
            self.logger.info(
                "Updating epic status",
                **create_entity_context(epic_id=epic_id.strip()),
                new_status=status,
                operation="update_epic_status",
            )

            epic = self.epic_repository.update_epic_status(epic_id.strip(), status)
            if epic is None:
                raise EpicNotFoundError(f"Epic with ID '{epic_id}' not found")

            self.logger.info(
                "Epic status updated successfully",
                **create_entity_context(epic_id=epic_id.strip()),
                new_status=status,
                operation="update_epic_status",
            )

            return epic.to_dict()
        except ValueError as e:
            # Handle SQLAlchemy model validation errors
            raise InvalidEpicStatusError(str(e))
        except IntegrityError as e:
            # Handle database constraint violations
            raise DatabaseError(f"Data integrity error: {str(e)}")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database operation failed: {str(e)}")
