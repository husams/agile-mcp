"""FastMCP tools for Epic management operations."""

import uuid
from typing import Any, Dict, List

from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import create_tables, get_db
from ..models.response import EpicResponse
from ..repositories.epic_repository import EpicRepository
from ..services.epic_service import EpicService
from ..services.exceptions import (
    DatabaseError,
    EpicNotFoundError,
    EpicValidationError,
    InvalidEpicStatusError,
)
from ..utils.logging_config import (
    create_entity_context,
    create_request_context,
    get_logger,
)


def register_epic_tools(mcp: FastMCP) -> None:
    """Register epic management tools with the FastMCP server."""
    logger = get_logger(__name__)

    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(
            "Failed to create database tables",
            error=str(e),
            operation="register_epic_tools",
        )
        raise

    @mcp.tool("backlog.createEpic")
    def create_epic(title: str, description: str) -> Dict[str, Any]:
        """
        Create a new epic with the specified title and description.

        Args:
            title: The name of the epic (max 200 characters)
            description: A detailed explanation of the epic's goal (max 2000 characters)

        Returns:
            Dict containing the created epic's id, title, description, and status

        Raises:
            McpError: If validation fails or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing create epic request",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createEpic"
                ),
                title=title[:50] if title else None,
            )

            db_session = get_db()
            try:
                epic_repository = EpicRepository(db_session)
                epic_service = EpicService(epic_repository)

                epic_dict = epic_service.create_epic(title, description)
                epic_response = EpicResponse(**epic_dict)

                logger.info(
                    "Create epic request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="backlog.createEpic"
                    ),
                    **create_entity_context(epic_id=epic_dict["id"]),
                )

                return epic_response.model_dump()

            finally:
                db_session.close()

        except EpicValidationError as e:
            logger.error(
                "Epic validation error in create epic",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createEpic"
                ),
                error_type="EpicValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except DatabaseError as e:
            logger.error(
                "Database error in create epic",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createEpic"
                ),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in create epic",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createEpic"
                ),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("backlog.findEpics")
    def find_epics() -> List[Dict[str, Any]]:
        """
        Retrieve a list of all existing epics.

        Returns:
            List of dictionaries, each containing an epic's id, title,
            description, and status

        Raises:
            McpError: If database operation fails
        """
        try:
            db_session = get_db()
            try:
                epic_repository = EpicRepository(db_session)
                epic_service = EpicService(epic_repository)

                epics_list = epic_service.find_epics()
                epics_responses = [
                    EpicResponse(**epic_dict).model_dump() for epic_dict in epics_list
                ]
                return epics_responses

            finally:
                db_session.close()

        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("backlog.updateEpicStatus")
    def update_epic_status(epic_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of an epic to reflect its current stage in the project plan.

        Args:
            epic_id: The unique identifier of the epic to update
            status: The new status value (must be one of: "Draft", "Ready",
                "In Progress", "Done", "On Hold")

        Returns:
            Dict containing the updated epic's id, title, description, and status

        Raises:
            McpError: If epic is not found, status is invalid, or database
                operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing update epic status request",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateEpicStatus"
                ),
                **create_entity_context(epic_id=epic_id),
                new_status=status,
            )

            db_session = get_db()
            try:
                epic_repository = EpicRepository(db_session)
                epic_service = EpicService(epic_repository)

                epic_dict = epic_service.update_epic_status(epic_id, status)
                epic_response = EpicResponse(**epic_dict)

                logger.info(
                    "Update epic status request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="backlog.updateEpicStatus"
                    ),
                    **create_entity_context(epic_id=epic_id),
                    new_status=status,
                )

                return epic_response.model_dump()

            finally:
                db_session.close()

        except EpicNotFoundError as e:
            logger.error(
                "Epic not found error in update epic status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateEpicStatus"
                ),
                **create_entity_context(epic_id=epic_id),
                new_status=status,
                error_type="EpicNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=str(e)))
        except InvalidEpicStatusError as e:
            logger.error(
                "Invalid epic status error in update epic status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateEpicStatus"
                ),
                **create_entity_context(epic_id=epic_id),
                new_status=status,
                error_type="InvalidEpicStatusError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=str(e)))
        except DatabaseError as e:
            logger.error(
                "Database error in update epic status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateEpicStatus"
                ),
                **create_entity_context(epic_id=epic_id),
                new_status=status,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in update epic status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateEpicStatus"
                ),
                **create_entity_context(epic_id=epic_id),
                new_status=status,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )
