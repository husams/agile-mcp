"""FastMCP tools for Project management operations."""

import uuid
from typing import Any, Dict, List

from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import create_tables, get_db
from ..models.response import ProjectResponse
from ..repositories.project_repository import ProjectRepository
from ..services.exceptions import DatabaseError, ProjectValidationError
from ..services.project_service import ProjectService
from ..utils.logging_config import (
    create_entity_context,
    create_request_context,
    get_logger,
)


def register_project_tools(mcp: FastMCP) -> None:
    """Register project management tools with the FastMCP server."""
    logger = get_logger(__name__)

    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(
            "Failed to create database tables",
            error=str(e),
            operation="register_project_tools",
        )
        raise

    @mcp.tool("create_project")
    def create_project(name: str, description: str) -> Dict[str, Any]:
        """
        Create a new project with the specified name and description.

        Args:
            name: The name of the project (max 200 characters)
            description: A detailed explanation of the project's purpose
            (max 2000 characters)

        Returns:
            Dict containing the created project's id, name, and description

        Raises:
            McpError: If validation fails or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing create project request",
                **create_request_context(
                    request_id=request_id, tool_name="create_project"
                ),
                name=name[:50] if name else None,
            )

            db_session = get_db()
            try:
                project_repository = ProjectRepository(db_session)
                project_service = ProjectService(project_repository)

                project_dict = project_service.create_project(name, description)
                project_response = ProjectResponse(**project_dict)

                logger.info(
                    "Create project request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="projects.create"
                    ),
                    **create_entity_context(project_id=project_dict["id"]),
                )

                return project_response.model_dump()

            finally:
                db_session.close()

        except ProjectValidationError as e:
            logger.error(
                "Project validation error in create project",
                **create_request_context(
                    request_id=request_id, tool_name="create_project"
                ),
                error_type="ProjectValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except DatabaseError as e:
            logger.error(
                "Database error in create project",
                **create_request_context(
                    request_id=request_id, tool_name="create_project"
                ),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in create project",
                **create_request_context(
                    request_id=request_id, tool_name="create_project"
                ),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("find_projects")
    def find_projects() -> List[Dict[str, Any]]:
        """
        Retrieve a list of all existing projects.

        Returns:
            List of dictionaries, each containing a project's id, name, and description

        Raises:
            McpError: If database operation fails
        """
        try:
            db_session = get_db()
            try:
                project_repository = ProjectRepository(db_session)
                project_service = ProjectService(project_repository)

                projects_list = project_service.find_projects()
                projects_responses = [
                    ProjectResponse(**project_dict).model_dump()
                    for project_dict in projects_list
                ]
                return projects_responses

            finally:
                db_session.close()

        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )
