"""Repository for Comment entity operations."""

import uuid
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.comment import Comment
from ..services.exceptions import CommentNotFoundError, DatabaseError


class CommentRepository:
    """Repository for managing Comment data access operations."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create_comment(
        self,
        story_id: str,
        author_role: str,
        content: str,
        reply_to_id: Optional[str] = None,
    ) -> Comment:
        """
        Create a new comment.

        Args:
            story_id: The ID of the story this comment belongs to
            author_role: The role of the comment author
            content: The comment content
            reply_to_id: Optional ID of the comment this is replying to

        Returns:
            Comment: The created comment instance

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            comment_id = str(uuid.uuid4())
            comment = Comment(
                id=comment_id,
                story_id=story_id,
                author_role=author_role,
                content=content,
                reply_to_id=reply_to_id,
            )

            self.db_session.add(comment)
            self.db_session.commit()
            self.db_session.refresh(comment)

            return comment

        except IntegrityError as e:
            self.db_session.rollback()
            raise DatabaseError(f"Integrity constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise DatabaseError(f"Database error creating comment: {str(e)}")

    def get_comment_by_id(self, comment_id: str) -> Comment:
        """
        Retrieve a comment by its ID.

        Args:
            comment_id: The unique identifier of the comment

        Returns:
            Comment: The comment instance

        Raises:
            CommentNotFoundError: If comment is not found
            DatabaseError: If database operation fails
        """
        try:
            comment = (
                self.db_session.query(Comment).filter(Comment.id == comment_id).first()
            )

            if not comment:
                raise CommentNotFoundError(f"Comment with id '{comment_id}' not found")

            return comment

        except CommentNotFoundError:
            raise
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error retrieving comment: {str(e)}")

    def get_comments_by_story_id(self, story_id: str) -> List[Comment]:
        """
        Retrieve all comments for a specific story, ordered chronologically.

        Args:
            story_id: The unique identifier of the story

        Returns:
            List[Comment]: List of comments ordered by timestamp

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            comments = (
                self.db_session.query(Comment)
                .filter(Comment.story_id == story_id)
                .order_by(Comment.timestamp.asc())
                .all()
            )

            return comments

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error retrieving story comments: {str(e)}")

    def update_comment(
        self, comment_id: str, content: Optional[str] = None
    ) -> Comment:
        """
        Update comment content.

        Args:
            comment_id: The unique identifier of the comment
            content: New comment content

        Returns:
            Comment: The updated comment instance

        Raises:
            CommentNotFoundError: If comment is not found
            DatabaseError: If database operation fails
        """
        try:
            comment = self.get_comment_by_id(comment_id)

            if content is not None:
                comment.content = content

            self.db_session.commit()
            self.db_session.refresh(comment)

            return comment

        except CommentNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise DatabaseError(f"Database error updating comment: {str(e)}")

    def delete_comment(self, comment_id: str) -> None:
        """
        Delete a comment.

        Args:
            comment_id: The unique identifier of the comment

        Raises:
            CommentNotFoundError: If comment is not found
            DatabaseError: If database operation fails
        """
        try:
            comment = self.get_comment_by_id(comment_id)

            self.db_session.delete(comment)
            self.db_session.commit()

        except CommentNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise DatabaseError(f"Database error deleting comment: {str(e)}")

    def get_comment_replies(self, comment_id: str) -> List[Comment]:
        """
        Get all direct replies to a comment.

        Args:
            comment_id: The unique identifier of the parent comment

        Returns:
            List[Comment]: List of reply comments ordered by timestamp

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            replies = (
                self.db_session.query(Comment)
                .filter(Comment.reply_to_id == comment_id)
                .order_by(Comment.timestamp.asc())
                .all()
            )

            return replies

        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error retrieving comment replies: {str(e)}")

    def get_comment_thread(self, comment_id: str) -> List[Comment]:
        """
        Get the complete thread starting from a root comment.

        Args:
            comment_id: The unique identifier of the root comment

        Returns:
            List[Comment]: List of all comments in the thread

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Get the root comment
            root_comment = self.get_comment_by_id(comment_id)
            thread = [root_comment]

            # Get all replies recursively
            def get_all_replies(parent_id: str) -> List[Comment]:
                replies = self.get_comment_replies(parent_id)
                all_replies = []
                for reply in replies:
                    all_replies.append(reply)
                    all_replies.extend(get_all_replies(reply.id))
                return all_replies

            thread.extend(get_all_replies(comment_id))
            return thread

        except CommentNotFoundError:
            raise
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error retrieving comment thread: {str(e)}")