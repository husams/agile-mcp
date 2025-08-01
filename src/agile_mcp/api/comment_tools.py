"""FastMCP tools for Comment management operations."""

import uuid
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import create_tables, get_db
from ..models.response import CommentResponse
from ..repositories.comment_repository import CommentRepository
from ..repositories.story_repository import StoryRepository
from ..services.comment_service import CommentService
from ..services.exceptions import (
    CommentNotFoundError,
    CommentValidationError,
    DatabaseError,
    StoryNotFoundError,
)
from ..utils.logging_config import (
    create_entity_context,
    create_request_context,
    get_logger,
)


def register_comment_tools(mcp: FastMCP) -> None:
    """Register comment management tools with the FastMCP server."""
    logger = get_logger(__name__)

    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(
            "Failed to create database tables",
            error=str(e),
            operation="register_comment_tools",
        )
        raise

    @mcp.tool("add_story_comment")
    def add_comment(
        story_id: str, author_role: str, content: str, reply_to_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a structured comment to a story with role and timestamp.

        Args:
            story_id: The unique identifier of the story
            author_role: The role of the comment author (must be from predefined
                roles: 'Developer Agent', 'QA Agent', 'Scrum Master',
                'Product Owner', 'Human Reviewer', 'System')
            content: The comment text content
            reply_to_id: Optional ID of comment this is replying to for threading

        Returns:
            Dict containing the created comment with id, story_id, author_role,
            content, timestamp, and reply_to_id

        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing add comment request",
                **create_request_context(
                    request_id=request_id, tool_name="story.addComment"
                ),
                **create_entity_context(story_id=story_id),
                author_role=author_role,
                content_preview=content[:50] if content else None,
                reply_to_id=reply_to_id,
            )

            db_session = get_db()
            try:
                comment_repository = CommentRepository(db_session)
                story_repository = StoryRepository(db_session)
                comment_service = CommentService(comment_repository, story_repository)

                comment_dict = comment_service.create_comment(
                    story_id=story_id,
                    author_role=author_role,
                    content=content,
                    reply_to_id=reply_to_id,
                )
                comment_response = CommentResponse(**comment_dict)

                logger.info(
                    "Add comment request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="story.addComment"
                    ),
                    **create_entity_context(
                        story_id=story_id, comment_id=comment_dict["id"]
                    ),
                )

                return comment_response.model_dump()

            finally:
                db_session.close()

        except CommentValidationError as e:
            logger.error(
                "Comment validation error in add comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.addComment"
                ),
                **create_entity_context(story_id=story_id),
                error_type="CommentValidationError",
                error_message=str(e),
                mcp_error_code=-32602,
            )
            raise McpError(
                ErrorData(
                    code=-32602,
                    message=f"Comment validation error: {str(e)}",
                    data={"story_id": story_id, "author_role": author_role},
                )
            )
        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in add comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.addComment"
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
        except CommentNotFoundError as e:
            logger.error(
                "Comment not found error in add comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.addComment"
                ),
                **create_entity_context(story_id=story_id),
                error_type="CommentNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Parent comment not found: {str(e)}",
                    data={"story_id": story_id, "reply_to_id": reply_to_id},
                )
            )
        except DatabaseError as e:
            logger.error(
                "Database error in add comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.addComment"
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in add comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.addComment"
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("get_story_comments")
    def get_story_comments(story_id: str) -> Dict[str, Any]:
        """
        Retrieve all comments for a story, ordered chronologically.

        Args:
            story_id: The unique identifier of the story

        Returns:
            Dict containing story_id and list of comments with their details

        Raises:
            McpError: If story not found or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing get story comments request",
                **create_request_context(
                    request_id=request_id, tool_name="story.getComments"
                ),
                **create_entity_context(story_id=story_id),
            )

            db_session = get_db()
            try:
                comment_repository = CommentRepository(db_session)
                story_repository = StoryRepository(db_session)
                comment_service = CommentService(comment_repository, story_repository)

                comments = comment_service.get_story_comments(story_id)

                logger.info(
                    "Get story comments request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="story.getComments"
                    ),
                    **create_entity_context(story_id=story_id),
                    comment_count=len(comments),
                )

                return {"story_id": story_id, "comments": comments}

            finally:
                db_session.close()

        except StoryNotFoundError as e:
            logger.error(
                "Story not found error in get story comments",
                **create_request_context(
                    request_id=request_id, tool_name="story.getComments"
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
                "Database error in get story comments",
                **create_request_context(
                    request_id=request_id, tool_name="story.getComments"
                ),
                **create_entity_context(story_id=story_id),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in get story comments",
                **create_request_context(
                    request_id=request_id, tool_name="story.getComments"
                ),
                **create_entity_context(story_id=story_id),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("update_story_comment")
    def update_comment(comment_id: str, content: str) -> Dict[str, Any]:
        """
        Update the content of an existing comment.

        Args:
            comment_id: The unique identifier of the comment
            content: New comment content

        Returns:
            Dict containing the updated comment details

        Raises:
            McpError: If validation fails, comment not found, or database
                operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing update comment request",
                **create_request_context(
                    request_id=request_id, tool_name="story.updateComment"
                ),
                comment_id=comment_id,
                content_preview=content[:50] if content else None,
            )

            db_session = get_db()
            try:
                comment_repository = CommentRepository(db_session)
                story_repository = StoryRepository(db_session)
                comment_service = CommentService(comment_repository, story_repository)

                comment_dict = comment_service.update_comment(
                    comment_id=comment_id, content=content
                )
                comment_response = CommentResponse(**comment_dict)

                logger.info(
                    "Update comment request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="story.updateComment"
                    ),
                    comment_id=comment_id,
                )

                return comment_response.model_dump()

            finally:
                db_session.close()

        except CommentValidationError as e:
            logger.error(
                "Comment validation error in update comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.updateComment"
                ),
                comment_id=comment_id,
                error_type="CommentValidationError",
                error_message=str(e),
                mcp_error_code=-32602,
            )
            raise McpError(
                ErrorData(
                    code=-32602,
                    message=f"Comment validation error: {str(e)}",
                    data={"comment_id": comment_id},
                )
            )
        except CommentNotFoundError as e:
            logger.error(
                "Comment not found error in update comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.updateComment"
                ),
                comment_id=comment_id,
                error_type="CommentNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Comment not found: {str(e)}",
                    data={"comment_id": comment_id},
                )
            )
        except DatabaseError as e:
            logger.error(
                "Database error in update comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.updateComment"
                ),
                comment_id=comment_id,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in update comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.updateComment"
                ),
                comment_id=comment_id,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )

    @mcp.tool("delete_story_comment")
    def delete_comment(comment_id: str) -> Dict[str, Any]:
        """
        Delete a comment.

        Args:
            comment_id: The unique identifier of the comment

        Returns:
            Dict containing success status and message

        Raises:
            McpError: If comment not found or database operation fails
        """
        request_id = str(uuid.uuid4())
        try:
            logger.info(
                "Processing delete comment request",
                **create_request_context(
                    request_id=request_id, tool_name="story.deleteComment"
                ),
                comment_id=comment_id,
            )

            db_session = get_db()
            try:
                comment_repository = CommentRepository(db_session)
                story_repository = StoryRepository(db_session)
                comment_service = CommentService(comment_repository, story_repository)

                result = comment_service.delete_comment(comment_id)

                logger.info(
                    "Delete comment request completed successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="story.deleteComment"
                    ),
                    comment_id=comment_id,
                )

                return result

            finally:
                db_session.close()

        except CommentNotFoundError as e:
            logger.error(
                "Comment not found error in delete comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.deleteComment"
                ),
                comment_id=comment_id,
                error_type="CommentNotFoundError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(
                    code=-32001,
                    message=f"Comment not found: {str(e)}",
                    data={"comment_id": comment_id},
                )
            )
        except DatabaseError as e:
            logger.error(
                "Database error in delete comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.deleteComment"
                ),
                comment_id=comment_id,
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            logger.error(
                "Unexpected error in delete comment",
                **create_request_context(
                    request_id=request_id, tool_name="story.deleteComment"
                ),
                comment_id=comment_id,
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Unexpected error: {str(e)}")
            )
