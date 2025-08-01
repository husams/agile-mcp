"""FastMCP tools for backlog management operations."""

import uuid
from typing import Any, Dict

from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import create_tables, get_db
from ..models.response import DependencyAddResponse, StoryResponse, StorySectionResponse
from ..repositories.dependency_repository import DependencyRepository
from ..repositories.story_repository import StoryRepository
from ..services.dependency_service import DependencyService
from ..services.exceptions import (
    CircularDependencyError,
    DatabaseError,
    DependencyValidationError,
    DuplicateDependencyError,
    SectionNotFoundError,
    StoryNotFoundError,
    StoryValidationError,
)
from ..services.story_service import StoryService
from ..utils.logging_config import (
    create_entity_context,
    create_request_context,
    get_logger,
)


def register_backlog_tools(mcp: FastMCP) -> None:
    """Register backlog management tools with the FastMCP server."""
    logger = get_logger(__name__)

    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(
            "Failed to create database tables",
            error=str(e),
            operation="register_backlog_tools",
        )
        raise

    @mcp.tool("get_story_section")
    def get_story_section(story_id: str, section_name: str) -> Dict[str, Any]:
        """
        Retrieve a specific section from a story by its unique ID and section name.

        Args:
            story_id: The unique identifier of the story
            section_name: The name of the section to extract (e.g.,
                "Acceptance Criteria", "Story", "Tasks / Subtasks")

        Returns:
            Dict containing the story_id, section_name, and content of the
            requested section

        Raises:
            McpError: If validation fails, story not found, section not found,
                or file operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing get story section request",
                **create_request_context(
                    request_id=request_id, tool_name="get_story_section"
                ),
                **create_entity_context(story_id=story_id),
                section_name=section_name,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                section_content = story_service.get_story_section(
                    story_id, section_name
                )

                logger.info(
                    "Get story section request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="backlog.getStorySection"
                    ),
                    **create_entity_context(story_id=story_id),
                    section_name=section_name,
                    content_length=len(section_content) if section_content else 0,
                )

                section_result = {
                    "story_id": story_id,
                    "section_name": section_name,
                    "content": section_content,
                }
                section_response = StorySectionResponse(**section_result)
                return section_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in get story section",
                **create_request_context(
                    request_id=request_id, tool_name="get_story_section"
                ),
                **create_entity_context(story_id=story_id),
                section_name=section_name,
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story validation error: {str(e)}",
                    data={"story_id": story_id, "section_name": section_name},
                )
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in get story section",
                **create_request_context(
                    request_id=request_id, tool_name="get_story_section"
                ),
                **create_entity_context(story_id=story_id),
                section_name=section_name,
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story not found: {str(e)}",
                    data={"story_id": story_id, "section_name": section_name},
                )
            )
        except SectionNotFoundError as e:
            logger.error(
                "Section not found error in get story section",
                **create_request_context(
                    request_id=request_id, tool_name="get_story_section"
                ),
                **create_entity_context(story_id=story_id),
                section_name=section_name,
                error_type="SectionNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Section not found: {str(e)}",
                    data={"story_id": story_id, "section_name": section_name},
                )
            )
        except DatabaseError as e:
            logger.error(
                "Database error in get story section",
                **create_request_context(
                    request_id=request_id, tool_name="get_story_section"
                ),
                **create_entity_context(story_id=story_id),
                section_name=section_name,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Database error: {str(e)}",
                    data={"story_id": story_id, "section_name": section_name},
                )
            )
        except Exception as e:
            logger.error(
                "Unexpected error in get story section",
                **create_request_context(
                    request_id=request_id, tool_name="get_story_section"
                ),
                **create_entity_context(story_id=story_id),
                section_name=section_name,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Unexpected error: {str(e)}",
                    data={"story_id": story_id, "section_name": section_name},
                )
            )

    @mcp.tool("add_story_dependency")
    def add_dependency(story_id: str, depends_on_story_id: str) -> str:
        """
        Add a dependency relationship between two stories.

        A dependency means that 'depends_on_story_id' must be completed before
        'story_id' can be started.
        This tool prevents the creation of circular dependencies (e.g., Story A
        depends on B, and B depends on A).

        Args:
            story_id: The unique identifier of the story that will have the dependency
            depends_on_story_id: The unique identifier of the story that must be
                completed first

        Returns:
            JSON string containing success/error response
        """
        try:
            db_session = get_db()
            try:
                dependency_repository = DependencyRepository(db_session)
                dependency_service = DependencyService(dependency_repository)

                dependency_service.add_story_dependency(story_id, depends_on_story_id)

                # Return standardized success response using DependencyAddResponse model
                response_data = DependencyAddResponse(
                    status="success",
                    story_id=story_id,
                    depends_on_story_id=depends_on_story_id,
                    message="Dependency added successfully",
                )
                return response_data.model_dump_json()

            finally:
                db_session.close()

        except CircularDependencyError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Circular dependency error: {str(e)}",
                    data={
                        "story_id": story_id,
                        "depends_on_story_id": depends_on_story_id,
                    },
                )
            )
        except StoryNotFoundError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story not found: {str(e)}",
                    data={
                        "story_id": story_id,
                        "depends_on_story_id": depends_on_story_id,
                    },
                )
            )
        except DuplicateDependencyError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Duplicate dependency error: {str(e)}",
                    data={
                        "story_id": story_id,
                        "depends_on_story_id": depends_on_story_id,
                    },
                )
            )
        except DependencyValidationError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Dependency validation error: {str(e)}",
                    data={
                        "story_id": story_id,
                        "depends_on_story_id": depends_on_story_id,
                    },
                )
            )
        except DatabaseError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Database error: {str(e)}",
                    data={
                        "story_id": story_id,
                        "depends_on_story_id": depends_on_story_id,
                    },
                )
            )
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Unexpected error: {str(e)}",
                    data={
                        "story_id": story_id,
                        "depends_on_story_id": depends_on_story_id,
                    },
                )
            )

    @mcp.tool("get_next_ready_story")
    def get_next_ready_story() -> Dict[str, Any]:
        """Get the next story that is ready for implementation.

        Returns the highest-priority ToDo story with no incomplete dependencies.
        Automatically updates the story status to InProgress.

        A story is ready if:
        - Status is "ToDo"
        - All stories it depends on have status "Done"

        Stories are ordered by:
        1. Priority (highest first)
        2. Created date (earliest first) for same priority

        Returns:
            Dict containing the story details if one is found, or empty dict if
            no stories are ready

        Raises:
            McpError: If database operation fails or service error occurs
        """
        try:
            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                dependency_repository = DependencyRepository(db_session)
                story_service = StoryService(story_repository, dependency_repository)

                story = story_service.get_next_ready_story()

                if story:
                    story_response = StoryResponse(**story)
                    return story_response.model_dump()
                else:
                    return {}  # Empty dict when no stories ready

            finally:
                db_session.close()

        except StoryValidationError as e:
            raise McpError(
                ErrorData(
                    code=-32001, message=f"Story validation error: {str(e)}", data={}
                )
            )
        except DatabaseError as e:
            raise McpError(
                ErrorData(code=-32001, message=f"Database error: {str(e)}", data={})
            )
        except Exception as e:
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}", data={})
            )
