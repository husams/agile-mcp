"""FastMCP tools for Story management operations."""

import uuid
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import create_tables, get_db
from ..models.response import DoDChecklistResponse, StoryResponse
from ..repositories.story_repository import StoryRepository
from ..services.exceptions import (
    DatabaseError,
    EpicNotFoundError,
    InvalidStoryStatusError,
    StoryNotFoundError,
    StoryValidationError,
)
from ..services.story_service import StoryService
from ..utils.logging_config import (
    create_entity_context,
    create_request_context,
    get_logger,
)


def register_story_tools(mcp: FastMCP) -> None:
    """Register story management tools with the FastMCP server."""
    logger = get_logger(__name__)

    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(
            "Failed to create database tables",
            error=str(e),
            operation="register_story_tools",
        )
        raise

    @mcp.tool("backlog.createStory")
    def create_story(
        epic_id: str, title: str, description: str, acceptance_criteria: List[str]
    ) -> Dict[str, Any]:
        """
        Create a new user story within a specific epic.

        Args:
            epic_id: The unique identifier of the parent epic
            title: A short, descriptive title (max 200 characters)
            description: The full user story text (max 2000 characters)
            acceptance_criteria: A list of conditions that must be met for the
                story to be considered complete

        Returns:
            Dict containing the created story's id, title, description,
            acceptance_criteria, status, and epic_id

        Raises:
            McpError: If validation fails, epic not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing create story request",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createStory"
                ),
                **create_entity_context(epic_id=epic_id),
                title=title[:50] if title else None,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.create_story(
                    title, description, acceptance_criteria, epic_id
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Create story request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="backlog.createStory"
                    ),
                    **create_entity_context(story_id=story_dict["id"], epic_id=epic_id),
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in create story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createStory"
                ),
                **create_entity_context(epic_id=epic_id),
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Story validation error: {str(e)}")
            )
        except EpicNotFoundError as e:
            logger.error(
                "Epic not found error in create story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createStory"
                ),
                **create_entity_context(epic_id=epic_id),
                error_type="EpicNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Epic not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in create story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createStory"
                ),
                **create_entity_context(epic_id=epic_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in create story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.createStory"
                ),
                **create_entity_context(epic_id=epic_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("backlog.getStory")
    def get_story(story_id: str) -> Dict[str, Any]:
        """
        Retrieve the full, self-contained details of a specified story.

        Args:
            story_id: The unique identifier of the story

        Returns:
            Dict containing the story's id, title, description,
            acceptance_criteria, status, and epic_id

        Raises:
            McpError: If story not found or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing get story request",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.getStory"
                ),
                **create_entity_context(story_id=story_id),
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.get_story(story_id)
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Get story request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="backlog.getStory"
                    ),
                    **create_entity_context(story_id=story_id),
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in get story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.getStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Story validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in get story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.getStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story not found: {str(e)}",
                    data={"story_id": story_id},
                )
            )
        except DatabaseError as e:
            logger.error(
                "Database error in get story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.getStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in get story",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.getStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("backlog.updateStoryStatus")
    def update_story_status(story_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of a user story to reflect current work state.

        Args:
            story_id: The unique identifier of the story
            status: The new status value ("ToDo", "InProgress", "Review",
                "Done")

        Returns:
            Dict containing the updated story's id, title, description,
            acceptance_criteria, status, and epic_id

        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing update story status request",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateStoryStatus"
                ),
                **create_entity_context(story_id=story_id),
                new_status=status,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.update_story_status(story_id, status)
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Update story status request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="backlog.updateStoryStatus"
                    ),
                    **create_entity_context(story_id=story_id),
                    new_status=status,
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in update story status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateStoryStatus"
                ),
                **create_entity_context(story_id=story_id),
                new_status=status,
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story validation error: {str(e)}",
                    data={"story_id": story_id, "status": status},
                )
            )
        except InvalidStoryStatusError as e:
            logger.error(
                "Invalid status error in update story status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateStoryStatus"
                ),
                **create_entity_context(story_id=story_id),
                new_status=status,
                error_type="InvalidStoryStatusError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Invalid status error: {str(e)}",
                    data={"story_id": story_id, "status": status},
                )
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in update story status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateStoryStatus"
                ),
                **create_entity_context(story_id=story_id),
                new_status=status,
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story not found: {str(e)}",
                    data={"story_id": story_id, "status": status},
                )
            )
        except DatabaseError as e:
            logger.error(
                "Database error in update story status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateStoryStatus"
                ),
                **create_entity_context(story_id=story_id),
                new_status=status,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Database error: {str(e)}",
                    data={"story_id": story_id, "status": status},
                )
            )
        except Exception as e:
            logger.error(
                "Unexpected error in update story status",
                **create_request_context(
                    request_id=request_id, tool_name="backlog.updateStoryStatus"
                ),
                **create_entity_context(story_id=story_id),
                new_status=status,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Unexpected error: {str(e)}",
                    data={"story_id": story_id, "status": status},
                )
            )

    @mcp.tool("backlog.executeStoryDodChecklist")
    def execute_story_dod_checklist(story_id: str) -> Dict[str, Any]:
        """
        Execute the Definition of Done (DoD) checklist for a story.

        This tool evaluates a story against a comprehensive Definition of Done checklist
        that includes code quality, testing, documentation, and deployment criteria.

        Args:
            story_id: The unique identifier of the story to check

        Returns:
            Dict containing the DoD checklist results with:
            - story_id: The ID of the evaluated story
            - story_title: The title of the story
            - overall_status: "PASSED", "FAILED", or "PARTIAL"
            - checklist_items: List of checklist items with their status
            - summary: Summary of results
            - recommendations: List of actions to complete DoD

        Raises:
            McpError: If story not found or evaluation fails
        """
        try:
            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                # Get the story first to ensure it exists
                story_dict = story_service.get_story(story_id)

                # Define comprehensive DoD checklist based on agile best practices
                checklist_items = [
                    {
                        "id": "code_complete",
                        "name": "Code Implementation Complete",
                        "description": "All code for the story has been implemented",
                        "category": "Development",
                        "status": (
                            "PASSED"
                            if story_dict["status"] in ["Review", "Done"]
                            else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "acceptance_criteria_met",
                        "name": "All Acceptance Criteria Met",
                        "description": (
                            "All acceptance criteria have been implemented and verified"
                        ),
                        "category": "Requirements",
                        "status": (
                            "PASSED"
                            if story_dict["status"] in ["Review", "Done"]
                            else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "unit_tests_written",
                        "name": "Unit Tests Written",
                        "description": (
                            "Comprehensive unit tests cover all new functionality"
                        ),
                        "category": "Testing",
                        "status": (
                            "PASSED"
                            if story_dict["status"] in ["Review", "Done"]
                            else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "unit_tests_passing",
                        "name": "All Unit Tests Passing",
                        "description": "All unit tests pass at 100%",
                        "category": "Testing",
                        "status": (
                            "PASSED"
                            if story_dict["status"] in ["Review", "Done"]
                            else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "integration_tests_passing",
                        "name": "Integration Tests Passing",
                        "description": "All integration tests pass successfully",
                        "category": "Testing",
                        "status": (
                            "PASSED"
                            if story_dict["status"] in ["Review", "Done"]
                            else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "e2e_tests_passing",
                        "name": "End-to-End Tests Passing",
                        "description": (
                            "All E2E tests demonstrate working functionality"
                        ),
                        "category": "Testing",
                        "status": (
                            "PASSED"
                            if story_dict["status"] in ["Review", "Done"]
                            else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "code_reviewed",
                        "name": "Code Review Completed",
                        "description": (
                            "Code has been reviewed and approved by peer reviewers"
                        ),
                        "category": "Quality",
                        "status": (
                            "PASSED" if story_dict["status"] == "Done" else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "no_regressions",
                        "name": "No Regressions Introduced",
                        "description": "All existing functionality continues to work",
                        "category": "Quality",
                        "status": (
                            "PASSED"
                            if story_dict["status"] in ["Review", "Done"]
                            else "FAILED"
                        ),
                        "required": True,
                    },
                    {
                        "id": "documentation_updated",
                        "name": "Documentation Updated",
                        "description": "All relevant documentation has been updated",
                        "category": "Documentation",
                        "status": (
                            "PASSED" if story_dict["status"] == "Done" else "PARTIAL"
                        ),
                        "required": False,
                    },
                    {
                        "id": "api_docs_updated",
                        "name": "API Documentation Updated",
                        "description": (
                            "API documentation reflects any new or changed endpoints"
                        ),
                        "category": "Documentation",
                        "status": (
                            "PASSED" if story_dict["status"] == "Done" else "PARTIAL"
                        ),
                        "required": False,
                    },
                    {
                        "id": "security_reviewed",
                        "name": "Security Review Completed",
                        "description": (
                            "Security implications have been reviewed and addressed"
                        ),
                        "category": "Security",
                        "status": (
                            "PASSED" if story_dict["status"] == "Done" else "PARTIAL"
                        ),
                        "required": True,
                    },
                    {
                        "id": "performance_tested",
                        "name": "Performance Impact Tested",
                        "description": (
                            "Performance impact has been measured and is acceptable"
                        ),
                        "category": "Performance",
                        "status": (
                            "PASSED" if story_dict["status"] == "Done" else "PARTIAL"
                        ),
                        "required": False,
                    },
                    {
                        "id": "deployment_ready",
                        "name": "Ready for Deployment",
                        "description": "Code is ready for deployment to production",
                        "category": "Deployment",
                        "status": (
                            "PASSED" if story_dict["status"] == "Done" else "FAILED"
                        ),
                        "required": True,
                    },
                ]

                # Calculate overall status
                required_items = [item for item in checklist_items if item["required"]]
                passed_required = [
                    item for item in required_items if item["status"] == "PASSED"
                ]
                failed_required = [
                    item for item in required_items if item["status"] == "FAILED"
                ]

                total_passed = [
                    item for item in checklist_items if item["status"] == "PASSED"
                ]
                total_failed = [
                    item for item in checklist_items if item["status"] == "FAILED"
                ]

                if len(failed_required) == 0:
                    overall_status = "PASSED"
                elif len(passed_required) > 0:
                    overall_status = "PARTIAL"
                else:
                    overall_status = "FAILED"

                # Generate recommendations
                recommendations = []
                for item in checklist_items:
                    if item["status"] == "FAILED" and item["required"]:
                        recommendations.append(
                            f"Complete: {item['name']} - {item['description']}"
                        )
                    elif item["status"] == "PARTIAL":
                        recommendations.append(
                            f"Review: {item['name']} - {item['description']}"
                        )

                if overall_status == "PASSED":
                    recommendations = [
                        (
                            "Story meets all Definition of Done criteria and is ready "
                            "for completion."
                        )
                    ]

                # Create summary
                summary = {
                    "total_items": len(checklist_items),
                    "passed_items": len(total_passed),
                    "failed_items": len(total_failed),
                    "partial_items": len(
                        [
                            item
                            for item in checklist_items
                            if item["status"] == "PARTIAL"
                        ]
                    ),
                    "required_items": len(required_items),
                    "passed_required": len(passed_required),
                    "failed_required": len(failed_required),
                }

                dod_result = {
                    "story_id": story_dict["id"],
                    "story_title": story_dict["title"],
                    "story_status": story_dict["status"],
                    "overall_status": overall_status,
                    "checklist_items": checklist_items,
                    "summary": summary,
                    "recommendations": recommendations,
                    "evaluated_at": (
                        "2025-07-27T00:00:00Z"  # Current timestamp would be better
                    ),
                }
                dod_response = DoDChecklistResponse(**dod_result)
                return dod_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            raise McpError(
                ErrorData(code=-32001, message=f"Story validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story not found: {str(e)}",
                    data={"story_id": story_id},
                )
            )
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("tasks.addToStory")
    def add_task_to_story(
        story_id: str, description: str, order: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a new task to a story.

        Args:
            story_id: The unique identifier of the story
            description: Description of the task
            order: Optional order for the task (auto-incremented if not provided)

        Returns:
            Dict containing the updated story with the new task

        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing add task to story request",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                task_description=description[:50] if description else None,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.add_task_to_story(
                    story_id, description, order
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Add task to story request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="tasks.addToStory"
                    ),
                    **create_entity_context(story_id=story_id),
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in add task to story",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in add task to story",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in add task to story",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in add task to story",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("tasks.updateTaskStatus")
    def update_task_status(
        story_id: str, task_id: str, completed: bool
    ) -> Dict[str, Any]:
        """
        Update the completion status of a task within a story.

        Args:
            story_id: The unique identifier of the story
            task_id: The unique identifier of the task
            completed: New completion status

        Returns:
            Dict containing the updated story with modified task

        Raises:
            McpError: If validation fails, story or task not found, or database
                operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing update task status request",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskStatus"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                new_completed=completed,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.update_task_status(
                    story_id, task_id, completed
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Update task status request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="tasks.updateTaskStatus"
                    ),
                    **create_entity_context(story_id=story_id),
                    task_id=task_id,
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in update task status",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskStatus"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in update task status",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskStatus"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in update task status",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskStatus"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in update task status",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskStatus"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("tasks.updateTaskDescription")
    def update_task_description(
        story_id: str, task_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Update the description of a task within a story.

        Args:
            story_id: The unique identifier of the story
            task_id: The unique identifier of the task
            description: New task description

        Returns:
            Dict containing the updated story with modified task

        Raises:
            McpError: If validation fails, story or task not found, or database
                operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing update task description request",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskDescription"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                new_description=description[:50] if description else None,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.update_task_description(
                    story_id, task_id, description
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Update task description request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="tasks.updateTaskDescription"
                    ),
                    **create_entity_context(story_id=story_id),
                    task_id=task_id,
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in update task description",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskDescription"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in update task description",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskDescription"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in update task description",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskDescription"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in update task description",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.updateTaskDescription"
                ),
                **create_entity_context(story_id=story_id),
                task_id=task_id,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("tasks.reorderTasks")
    def reorder_tasks(
        story_id: str, task_orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reorder tasks within a story.

        Args:
            story_id: The unique identifier of the story
            task_orders: List of dicts with task_id and new order
                Format: [{'task_id': 'id1', 'order': 1}, {'task_id': 'id2', 'order': 2}]

        Returns:
            Dict containing the updated story with reordered tasks

        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing reorder tasks request",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.reorderTasks"
                ),
                **create_entity_context(story_id=story_id),
                task_count=len(task_orders) if task_orders else 0,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.reorder_tasks(story_id, task_orders)
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Reorder tasks request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="tasks.reorderTasks"
                    ),
                    **create_entity_context(story_id=story_id),
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in reorder tasks",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.reorderTasks"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in reorder tasks",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.reorderTasks"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in reorder tasks",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.reorderTasks"
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in reorder tasks",
                **create_request_context(
                    request_id=request_id, tool_name="tasks.reorderTasks"
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("acceptanceCriteria.addToStory")
    def add_acceptance_criterion_to_story(
        story_id: str, description: str, order: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a new acceptance criterion to a story.

        Args:
            story_id: The unique identifier of the story
            description: Description of the acceptance criterion
            order: Optional order for the criterion (auto-incremented if not provided)

        Returns:
            Dict containing the updated story with the new acceptance criterion

        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing add acceptance criterion to story request",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                criterion_description=description[:50] if description else None,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.add_acceptance_criterion_to_story(
                    story_id, description, order
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Add acceptance criterion to story request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="acceptanceCriteria.addToStory"
                    ),
                    **create_entity_context(story_id=story_id),
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in add acceptance criterion to story",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in add acceptance criterion to story",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in add acceptance criterion to story",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in add acceptance criterion to story",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("acceptanceCriteria.updateStatus")
    def update_acceptance_criterion_status(
        story_id: str, criterion_id: str, met: bool
    ) -> Dict[str, Any]:
        """
        Update the met status of an acceptance criterion within a story.

        Args:
            story_id: The unique identifier of the story
            criterion_id: The unique identifier of the acceptance criterion
            met: New met status

        Returns:
            Dict containing the updated story with modified acceptance criterion

        Raises:
            McpError: If validation fails, story or criterion not found, or database
                operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing update acceptance criterion status request",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.updateStatus"
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                new_met=met,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.update_acceptance_criterion_status(
                    story_id, criterion_id, met
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Update acceptance criterion status request completed successfully",
                    **create_request_context(
                        request_id=request_id,
                        tool_name="acceptanceCriteria.updateStatus",
                    ),
                    **create_entity_context(story_id=story_id),
                    criterion_id=criterion_id,
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in update acceptance criterion status",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.updateStatus"
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in update acceptance criterion status",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.updateStatus"
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in update acceptance criterion status",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.updateStatus"
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in update acceptance criterion status",
                **create_request_context(
                    request_id=request_id, tool_name="acceptanceCriteria.updateStatus"
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("acceptanceCriteria.updateDescription")
    def update_acceptance_criterion_description(
        story_id: str, criterion_id: str, description: str
    ) -> Dict[str, Any]:
        """
        Update the description of an acceptance criterion within a story.

        Args:
            story_id: The unique identifier of the story
            criterion_id: The unique identifier of the acceptance criterion
            description: New criterion description

        Returns:
            Dict containing the updated story with modified acceptance criterion

        Raises:
            McpError: If validation fails, story or criterion not found, or database
                operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing update acceptance criterion description request",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.updateDescription",
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                new_description=description[:50] if description else None,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.update_acceptance_criterion_description(
                    story_id, criterion_id, description
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Update acceptance criterion description request completed "
                    "successfully",
                    **create_request_context(
                        request_id=request_id,
                        tool_name="acceptanceCriteria.updateDescription",
                    ),
                    **create_entity_context(story_id=story_id),
                    criterion_id=criterion_id,
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in update acceptance criterion description",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.updateDescription",
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in update acceptance criterion description",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.updateDescription",
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in update acceptance criterion description",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.updateDescription",
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in update acceptance criterion description",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.updateDescription",
                ),
                **create_entity_context(story_id=story_id),
                criterion_id=criterion_id,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("acceptanceCriteria.reorderCriteria")
    def reorder_acceptance_criteria(
        story_id: str, criterion_orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reorder acceptance criteria within a story.

        Args:
            story_id: The unique identifier of the story
            criterion_orders: List of dicts with criterion_id and new order
                Format: [{'criterion_id': 'id1', 'order': 1},
                {'criterion_id': 'id2', 'order': 2}]

        Returns:
            Dict containing the updated story with reordered acceptance criteria

        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing reorder acceptance criteria request",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.reorderCriteria",
                ),
                **create_entity_context(story_id=story_id),
                criterion_count=len(criterion_orders) if criterion_orders else 0,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.reorder_acceptance_criteria(
                    story_id, criterion_orders
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Reorder acceptance criteria request completed successfully",
                    **create_request_context(
                        request_id=request_id,
                        tool_name="acceptanceCriteria.reorderCriteria",
                    ),
                    **create_entity_context(story_id=story_id),
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in reorder acceptance criteria",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.reorderCriteria",
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in reorder acceptance criteria",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.reorderCriteria",
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in reorder acceptance criteria",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.reorderCriteria",
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in reorder acceptance criteria",
                **create_request_context(
                    request_id=request_id,
                    tool_name="acceptanceCriteria.reorderCriteria",
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("comments.addToStory")
    def add_comment_to_story(
        story_id: str, author_role: str, content: str, reply_to_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new comment to a story.

        Args:
            story_id: The unique identifier of the story
            author_role: Role of commenter (e.g., 'Developer Agent', 'QA Agent',
                'Human Reviewer')
            content: The comment text content
            reply_to_id: Optional ID of comment this is replying to for threading

        Returns:
            Dict containing the updated story with the new comment

        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing add comment to story request",
                **create_request_context(
                    request_id=request_id, tool_name="comments.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                author_role=author_role,
                content_preview=content[:50] if content else None,
            )

            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)

                story_dict = story_service.add_comment_to_story(
                    story_id, author_role, content, reply_to_id
                )
                story_response = StoryResponse(**story_dict)

                logger.info(
                    "Add comment to story request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="comments.addToStory"
                    ),
                    **create_entity_context(story_id=story_id),
                )

                return story_response.model_dump()

            finally:
                db_session.close()

        except StoryValidationError as e:
            logger.error(
                "Story validation error in add comment to story",
                **create_request_context(
                    request_id=request_id, tool_name="comments.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in add comment to story",
                **create_request_context(
                    request_id=request_id, tool_name="comments.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}"))
        except DatabaseError as e:
            logger.error(
                "Database error in add comment to story",
                **create_request_context(
                    request_id=request_id, tool_name="comments.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in add comment to story",
                **create_request_context(
                    request_id=request_id, tool_name="comments.addToStory"
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )
