"""
FastMCP tools for Artifact management operations.
"""

import uuid
from typing import Any, Dict, List

from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import create_tables, get_db
from ..models.response import ArtifactResponse
from ..repositories.artifact_repository import ArtifactRepository
from ..services.artifact_service import ArtifactService
from ..services.exceptions import (
    ArtifactValidationError,
    DatabaseError,
    InvalidRelationTypeError,
    StoryNotFoundError,
)
from ..utils.logging_config import (
    create_entity_context,
    create_request_context,
    get_logger,
)


def register_artifact_tools(mcp: FastMCP) -> None:
    """Register artifact management tools with the FastMCP server."""

    logger = get_logger(__name__)

    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(
            "Failed to create database tables",
            error=str(e),
            operation="register_artifact_tools",
        )
        raise

    @mcp.tool("artifacts.linkToStory")
    def link_artifact_to_story(
        story_id: str, uri: str, relation: str
    ) -> Dict[str, Any]:
        """
        Links a generated artifact to a user story for traceability.

        Args:
            story_id: The unique identifier of the story to link the
                artifact to
            uri: The Uniform Resource Identifier for the artifact
                (e.g., file:///path/to/code.js)
            relation: The relationship type between artifact and story
                ("implementation", "design", "test")

        Returns:
            Dict containing the created artifact's id, uri, relation,
            and story_id

        Raises:
            McpError: If validation fails, story not found, or database
                operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing link artifact to story request",
                **create_request_context(
                    request_id=request_id, tool_name="artifacts.linkToStory"
                ),
                **create_entity_context(story_id=story_id),
                uri=uri[:100],
                relation=relation,
            )

            db_session = get_db()
            try:
                artifact_repository = ArtifactRepository(db_session)
                artifact_service = ArtifactService(artifact_repository)

                artifact_dict = artifact_service.link_artifact_to_story(
                    story_id, uri, relation
                )
                artifact_response = ArtifactResponse(**artifact_dict)

                logger.info(
                    "Link artifact to story request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="artifacts.linkToStory"
                    ),
                    **create_entity_context(
                        story_id=story_id, artifact_id=artifact_dict["id"]
                    ),
                    uri=uri[:100],
                    relation=relation,
                )

                return artifact_response.model_dump()

            finally:
                db_session.close()

        except ArtifactValidationError as e:
            logger.error(
                "Artifact validation error in link artifact to story",
                **create_request_context(
                    request_id=request_id, tool_name="artifacts.linkToStory"
                ),
                **create_entity_context(story_id=story_id),
                uri=uri[:100],
                relation=relation,
                error_type="ArtifactValidationError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Artifact validation error: {str(e)}",
                    data={"story_id": story_id, "uri": uri, "relation": relation},
                )
            )
        except InvalidRelationTypeError as e:
            logger.error(
                "Invalid relation type error in link artifact to story",
                **create_request_context(
                    request_id=request_id, tool_name="artifacts.linkToStory"
                ),
                **create_entity_context(story_id=story_id),
                uri=uri[:100],
                relation=relation,
                error_type="InvalidRelationTypeError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Invalid relation type: {str(e)}",
                    data={"story_id": story_id, "uri": uri, "relation": relation},
                )
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in link artifact to story",
                **create_request_context(
                    request_id=request_id, tool_name="artifacts.linkToStory"
                ),
                **create_entity_context(story_id=story_id),
                uri=uri[:100],
                relation=relation,
                error_type="StoryNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Story not found: {str(e)}",
                    data={"story_id": story_id, "uri": uri, "relation": relation},
                )
            )
        except DatabaseError as e:
            logger.error(
                "Database error in link artifact to story",
                **create_request_context(
                    request_id=request_id, tool_name="artifacts.linkToStory"
                ),
                **create_entity_context(story_id=story_id),
                uri=uri[:100],
                relation=relation,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Database error: {str(e)}",
                    data={"story_id": story_id, "uri": uri, "relation": relation},
                )
            )
        except Exception as e:
            logger.error(
                "Unexpected error in link artifact to story",
                **create_request_context(
                    request_id=request_id, tool_name="artifacts.linkToStory"
                ),
                **create_entity_context(story_id=story_id),
                uri=uri[:100],
                relation=relation,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Unexpected error: {str(e)}",
                    data={"story_id": story_id, "uri": uri, "relation": relation},
                )
            )

    @mcp.tool("artifacts.listForStory")
    def list_artifacts_for_story(story_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all artifacts linked to a specific story.

        Args:
            story_id: The unique identifier of the story

        Returns:
            List of dicts, each containing an artifact's id, uri, relation,
            and story_id

        Raises:
            McpError: If validation fails or database operation fails
        """
        try:
            db_session = get_db()
            try:
                artifact_repository = ArtifactRepository(db_session)
                artifact_service = ArtifactService(artifact_repository)

                artifacts_list = artifact_service.get_artifacts_for_story(story_id)
                artifacts_responses = [
                    ArtifactResponse(**artifact_dict).model_dump()
                    for artifact_dict in artifacts_list
                ]
                return artifacts_responses

            finally:
                db_session.close()

        except ArtifactValidationError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Artifact validation error: {str(e)}",
                    data={"story_id": story_id},
                )
            )
        except DatabaseError as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Database error: {str(e)}",
                    data={"story_id": story_id},
                )
            )
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Unexpected error: {str(e)}",
                    data={"story_id": story_id},
                )
            )
