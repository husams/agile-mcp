"""
Unit tests for CommentService.
"""

from unittest.mock import Mock

import pytest

from src.agile_mcp.repositories.comment_repository import CommentRepository
from src.agile_mcp.repositories.story_repository import StoryRepository
from src.agile_mcp.services.comment_service import CommentService
from src.agile_mcp.services.exceptions import (
    CommentNotFoundError,
    CommentValidationError,
    StoryNotFoundError,
)


@pytest.fixture
def mock_comment_repository():
    """Create a mock CommentRepository."""
    return Mock(spec=CommentRepository)


@pytest.fixture
def mock_story_repository():
    """Create a mock StoryRepository."""
    return Mock(spec=StoryRepository)


@pytest.fixture
def comment_service(mock_comment_repository, mock_story_repository):
    """Create a CommentService instance with mocked repositories."""
    return CommentService(mock_comment_repository, mock_story_repository)


def test_create_comment_success(
    comment_service, mock_story_repository, mock_comment_repository
):
    """Test successful comment creation."""
    # Mock story exists
    mock_story_repository.find_story_by_id.return_value = Mock()

    # Mock comment creation
    mock_comment = Mock()
    mock_comment.to_dict.return_value = {
        "id": "comment-1",
        "story_id": "story-1",
        "author_role": "Developer Agent",
        "content": "Test comment",
        "timestamp": "2025-07-31T12:00:00Z",
        "reply_to_id": None,
    }
    mock_comment_repository.create_comment.return_value = mock_comment

    result = comment_service.create_comment(
        story_id="story-1",
        author_role="Developer Agent",
        content="Test comment",
    )

    assert result["id"] == "comment-1"
    assert result["story_id"] == "story-1"
    assert result["author_role"] == "Developer Agent"
    assert result["content"] == "Test comment"

    mock_story_repository.find_story_by_id.assert_called_once_with("story-1")
    mock_comment_repository.create_comment.assert_called_once_with(
        story_id="story-1",
        author_role="Developer Agent",
        content="Test comment",
        reply_to_id=None,
    )


def test_create_comment_invalid_author_role(comment_service, mock_story_repository):
    """Test comment creation with invalid author role."""
    mock_story_repository.find_story_by_id.return_value = Mock()

    with pytest.raises(CommentValidationError, match="Invalid author role"):
        comment_service.create_comment(
            story_id="story-1",
            author_role="Invalid Role",
            content="Test comment",
        )


def test_create_comment_story_not_found(comment_service, mock_story_repository):
    """Test comment creation when story doesn't exist."""
    mock_story_repository.find_story_by_id.return_value = None

    with pytest.raises(StoryNotFoundError):
        comment_service.create_comment(
            story_id="non-existent-story",
            author_role="Developer Agent",
            content="Test comment",
        )


def test_create_comment_with_reply_success(
    comment_service, mock_story_repository, mock_comment_repository
):
    """Test successful comment creation with reply_to_id."""
    # Mock story exists
    mock_story_repository.find_story_by_id.return_value = Mock()

    # Mock parent comment exists and belongs to same story
    mock_parent_comment = Mock()
    mock_parent_comment.story_id = "story-1"
    mock_comment_repository.get_comment_by_id.return_value = mock_parent_comment

    # Mock comment creation
    mock_comment = Mock()
    mock_comment.to_dict.return_value = {
        "id": "comment-2",
        "story_id": "story-1",
        "author_role": "QA Agent",
        "content": "Reply comment",
        "timestamp": "2025-07-31T12:00:00Z",
        "reply_to_id": "comment-1",
    }
    mock_comment_repository.create_comment.return_value = mock_comment

    result = comment_service.create_comment(
        story_id="story-1",
        author_role="QA Agent",
        content="Reply comment",
        reply_to_id="comment-1",
    )

    assert result["reply_to_id"] == "comment-1"
    mock_comment_repository.get_comment_by_id.assert_called_once_with("comment-1")


def test_create_comment_reply_different_story(
    comment_service, mock_story_repository, mock_comment_repository
):
    """Test comment creation fails when reply_to_id belongs to different story."""
    mock_story_repository.find_story_by_id.return_value = Mock()

    # Mock parent comment belongs to different story
    mock_parent_comment = Mock()
    mock_parent_comment.story_id = "different-story"
    mock_comment_repository.get_comment_by_id.return_value = mock_parent_comment

    with pytest.raises(
        CommentValidationError, match="Reply comment must belong to the same story"
    ):
        comment_service.create_comment(
            story_id="story-1",
            author_role="QA Agent",
            content="Reply comment",
            reply_to_id="comment-1",
        )


def test_create_comment_reply_not_found(
    comment_service, mock_story_repository, mock_comment_repository
):
    """Test comment creation fails when reply_to_id doesn't exist."""
    mock_story_repository.find_story_by_id.return_value = Mock()
    mock_comment_repository.get_comment_by_id.side_effect = CommentNotFoundError(
        "Comment not found"
    )

    with pytest.raises(CommentNotFoundError):
        comment_service.create_comment(
            story_id="story-1",
            author_role="QA Agent",
            content="Reply comment",
            reply_to_id="non-existent",
        )


def test_get_comment_success(comment_service, mock_comment_repository):
    """Test successful comment retrieval."""
    mock_comment = Mock()
    mock_comment.to_dict.return_value = {
        "id": "comment-1",
        "story_id": "story-1",
        "author_role": "Developer Agent",
        "content": "Test comment",
        "timestamp": "2025-07-31T12:00:00Z",
        "reply_to_id": None,
    }
    mock_comment_repository.get_comment_by_id.return_value = mock_comment

    result = comment_service.get_comment("comment-1")

    assert result["id"] == "comment-1"
    mock_comment_repository.get_comment_by_id.assert_called_once_with("comment-1")


def test_get_comment_not_found(comment_service, mock_comment_repository):
    """Test comment retrieval when comment doesn't exist."""
    mock_comment_repository.get_comment_by_id.side_effect = CommentNotFoundError(
        "Comment not found"
    )

    with pytest.raises(CommentNotFoundError):
        comment_service.get_comment("non-existent")


def test_get_story_comments_success(
    comment_service, mock_story_repository, mock_comment_repository
):
    """Test successful story comments retrieval."""
    mock_story_repository.find_story_by_id.return_value = Mock()

    mock_comments = [Mock(), Mock()]
    mock_comments[0].to_dict.return_value = {
        "id": "comment-1",
        "content": "First comment",
    }
    mock_comments[1].to_dict.return_value = {
        "id": "comment-2",
        "content": "Second comment",
    }
    mock_comment_repository.get_comments_by_story_id.return_value = mock_comments

    result = comment_service.get_story_comments("story-1")

    assert len(result) == 2
    assert result[0]["id"] == "comment-1"
    assert result[1]["id"] == "comment-2"
    mock_story_repository.find_story_by_id.assert_called_once_with("story-1")
    mock_comment_repository.get_comments_by_story_id.assert_called_once_with("story-1")


def test_get_story_comments_story_not_found(comment_service, mock_story_repository):
    """Test story comments retrieval when story doesn't exist."""
    mock_story_repository.find_story_by_id.return_value = None

    with pytest.raises(StoryNotFoundError):
        comment_service.get_story_comments("non-existent")


def test_update_comment_success(comment_service, mock_comment_repository):
    """Test successful comment update."""
    mock_comment = Mock()
    mock_comment.to_dict.return_value = {
        "id": "comment-1",
        "story_id": "story-1",
        "author_role": "Developer Agent",
        "content": "Updated content",
        "timestamp": "2025-07-31T12:00:00Z",
        "reply_to_id": None,
    }
    mock_comment_repository.update_comment.return_value = mock_comment

    result = comment_service.update_comment("comment-1", "Updated content")

    assert result["content"] == "Updated content"
    mock_comment_repository.update_comment.assert_called_once_with(
        comment_id="comment-1", content="Updated content"
    )


def test_update_comment_empty_content(comment_service):
    """Test comment update with empty content."""
    with pytest.raises(CommentValidationError, match="Comment content cannot be empty"):
        comment_service.update_comment("comment-1", "")

    with pytest.raises(CommentValidationError, match="Comment content cannot be empty"):
        comment_service.update_comment("comment-1", "   ")


def test_update_comment_not_found(comment_service, mock_comment_repository):
    """Test comment update when comment doesn't exist."""
    mock_comment_repository.update_comment.side_effect = CommentNotFoundError(
        "Comment not found"
    )

    with pytest.raises(CommentNotFoundError):
        comment_service.update_comment("non-existent", "New content")


def test_delete_comment_success(comment_service, mock_comment_repository):
    """Test successful comment deletion."""
    result = comment_service.delete_comment("comment-1")

    assert result["status"] == "success"
    assert "Comment comment-1 deleted" in result["message"]
    mock_comment_repository.delete_comment.assert_called_once_with("comment-1")


def test_delete_comment_not_found(comment_service, mock_comment_repository):
    """Test comment deletion when comment doesn't exist."""
    mock_comment_repository.delete_comment.side_effect = CommentNotFoundError(
        "Comment not found"
    )

    with pytest.raises(CommentNotFoundError):
        comment_service.delete_comment("non-existent")


def test_get_comment_thread_success(comment_service, mock_comment_repository):
    """Test successful comment thread retrieval."""
    mock_comments = [Mock(), Mock(), Mock()]
    mock_comments[0].to_dict.return_value = {"id": "comment-1", "content": "Parent"}
    mock_comments[1].to_dict.return_value = {"id": "comment-2", "content": "Reply 1"}
    mock_comments[2].to_dict.return_value = {"id": "comment-3", "content": "Reply 2"}
    mock_comment_repository.get_comment_thread.return_value = mock_comments

    result = comment_service.get_comment_thread("comment-1")

    assert len(result) == 3
    assert result[0]["id"] == "comment-1"
    assert result[1]["id"] == "comment-2"
    assert result[2]["id"] == "comment-3"
    mock_comment_repository.get_comment_thread.assert_called_once_with("comment-1")


def test_get_comment_thread_not_found(comment_service, mock_comment_repository):
    """Test comment thread retrieval when root comment doesn't exist."""
    mock_comment_repository.get_comment_thread.side_effect = CommentNotFoundError(
        "Comment not found"
    )

    with pytest.raises(CommentNotFoundError):
        comment_service.get_comment_thread("non-existent")


def test_get_comment_replies_success(comment_service, mock_comment_repository):
    """Test successful comment replies retrieval."""
    # Mock parent comment exists
    mock_comment_repository.get_comment_by_id.return_value = Mock()

    mock_replies = [Mock(), Mock()]
    mock_replies[0].to_dict.return_value = {"id": "reply-1", "content": "First reply"}
    mock_replies[1].to_dict.return_value = {"id": "reply-2", "content": "Second reply"}
    mock_comment_repository.get_comment_replies.return_value = mock_replies

    result = comment_service.get_comment_replies("comment-1")

    assert len(result) == 2
    assert result[0]["id"] == "reply-1"
    assert result[1]["id"] == "reply-2"
    mock_comment_repository.get_comment_by_id.assert_called_once_with("comment-1")
    mock_comment_repository.get_comment_replies.assert_called_once_with("comment-1")


def test_get_comment_replies_parent_not_found(comment_service, mock_comment_repository):
    """Test comment replies retrieval when parent comment doesn't exist."""
    mock_comment_repository.get_comment_by_id.side_effect = CommentNotFoundError(
        "Comment not found"
    )

    with pytest.raises(CommentNotFoundError):
        comment_service.get_comment_replies("non-existent")
