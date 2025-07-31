"""Service layer for Comment business logic operations."""

from typing import Any, Dict, List, Optional

from ..models.comment import AuthorRole
from ..repositories.comment_repository import CommentRepository
from ..repositories.story_repository import StoryRepository
from .exceptions import (
    CommentNotFoundError,
    CommentValidationError,
    DatabaseError,
    StoryNotFoundError,
)


class CommentService:
    """Service for managing comment business logic."""

    def __init__(
        self, comment_repository: CommentRepository, story_repository: StoryRepository
    ):
        """Initialize the service with required repositories."""
        self.comment_repository = comment_repository
        self.story_repository = story_repository

    def create_comment(
        self,
        story_id: str,
        author_role: str,
        content: str,
        reply_to_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new comment with validation.

        Args:
            story_id: The ID of the story this comment belongs to
            author_role: The role of the comment author
            content: The comment content
            reply_to_id: Optional ID of the comment this is replying to

        Returns:
            Dict: The created comment data

        Raises:
            StoryNotFoundError: If the story doesn't exist
            CommentNotFoundError: If reply_to_id is provided but doesn't exist
            CommentValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Validate that the story exists
            story = self.story_repository.find_story_by_id(story_id)
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            # Validate author role
            if not AuthorRole.is_valid_role(author_role):
                valid_roles = ", ".join(AuthorRole.get_valid_roles())
                raise CommentValidationError(
                    f"Invalid author role '{author_role}'. "
                    f"Valid roles are: {valid_roles}"
                )

            # Validate reply_to_id if provided
            if reply_to_id:
                parent_comment = self.comment_repository.get_comment_by_id(reply_to_id)
                # Ensure the parent comment belongs to the same story
                if parent_comment.story_id != story_id:
                    raise CommentValidationError(
                        "Reply comment must belong to the same story as parent comment"
                    )

            # Create the comment
            comment = self.comment_repository.create_comment(
                story_id=story_id,
                author_role=author_role,
                content=content,
                reply_to_id=reply_to_id,
            )

            return comment.to_dict()

        except StoryNotFoundError:
            raise
        except CommentNotFoundError:
            raise
        except CommentValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Unexpected error creating comment: {str(e)}")

    def get_comment(self, comment_id: str) -> Dict[str, Any]:
        """
        Retrieve a comment by ID.

        Args:
            comment_id: The unique identifier of the comment

        Returns:
            Dict: The comment data

        Raises:
            CommentNotFoundError: If comment is not found
            DatabaseError: If database operation fails
        """
        try:
            comment = self.comment_repository.get_comment_by_id(comment_id)
            return comment.to_dict()

        except CommentNotFoundError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Unexpected error retrieving comment: {str(e)}")

    def get_story_comments(self, story_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all comments for a story, ordered chronologically.

        Args:
            story_id: The unique identifier of the story

        Returns:
            List[Dict]: List of comment data ordered by timestamp

        Raises:
            StoryNotFoundError: If the story doesn't exist
            DatabaseError: If database operation fails
        """
        try:
            # Validate that the story exists
            story = self.story_repository.find_story_by_id(story_id)
            if not story:
                raise StoryNotFoundError(f"Story with ID '{story_id}' not found")

            comments = self.comment_repository.get_comments_by_story_id(story_id)
            return [comment.to_dict() for comment in comments]

        except StoryNotFoundError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Unexpected error retrieving story comments: {str(e)}")

    def update_comment(self, comment_id: str, content: str) -> Dict[str, Any]:
        """
        Update comment content.

        Args:
            comment_id: The unique identifier of the comment
            content: New comment content

        Returns:
            Dict: The updated comment data

        Raises:
            CommentNotFoundError: If comment is not found
            CommentValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            if not content or not content.strip():
                raise CommentValidationError("Comment content cannot be empty")

            comment = self.comment_repository.update_comment(
                comment_id=comment_id, content=content.strip()
            )
            return comment.to_dict()

        except CommentNotFoundError:
            raise
        except CommentValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Unexpected error updating comment: {str(e)}")

    def delete_comment(self, comment_id: str) -> Dict[str, str]:
        """
        Delete a comment.

        Args:
            comment_id: The unique identifier of the comment

        Returns:
            Dict: Success message

        Raises:
            CommentNotFoundError: If comment is not found
            DatabaseError: If database operation fails
        """
        try:
            self.comment_repository.delete_comment(comment_id)
            return {"status": "success", "message": f"Comment {comment_id} deleted"}

        except CommentNotFoundError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Unexpected error deleting comment: {str(e)}")

    def get_comment_thread(self, comment_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete thread starting from a root comment.

        Args:
            comment_id: The unique identifier of the root comment

        Returns:
            List[Dict]: List of all comments in the thread

        Raises:
            CommentNotFoundError: If root comment is not found
            DatabaseError: If database operation fails
        """
        try:
            comments = self.comment_repository.get_comment_thread(comment_id)
            return [comment.to_dict() for comment in comments]

        except CommentNotFoundError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Unexpected error retrieving comment thread: {str(e)}")

    def get_comment_replies(self, comment_id: str) -> List[Dict[str, Any]]:
        """
        Get all direct replies to a comment.

        Args:
            comment_id: The unique identifier of the parent comment

        Returns:
            List[Dict]: List of reply comments

        Raises:
            CommentNotFoundError: If parent comment is not found
            DatabaseError: If database operation fails
        """
        try:
            # Validate parent comment exists
            self.comment_repository.get_comment_by_id(comment_id)

            replies = self.comment_repository.get_comment_replies(comment_id)
            return [reply.to_dict() for reply in replies]

        except CommentNotFoundError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(
                f"Unexpected error retrieving comment replies: {str(e)}"
            )
