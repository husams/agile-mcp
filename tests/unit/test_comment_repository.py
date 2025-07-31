"""
Unit tests for CommentRepository.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.comment import Comment
from src.agile_mcp.models.epic import Base, Epic
from src.agile_mcp.models.project import Project
from src.agile_mcp.models.story import Story
from src.agile_mcp.repositories.comment_repository import CommentRepository
from src.agile_mcp.services.exceptions import CommentNotFoundError, DatabaseError


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test project
    project = Project(
        id="test-project-1",
        name="Test Project",
        description="Test project for comment repository",
    )
    session.add(project)

    # Create test epic
    epic = Epic(
        id="test-epic-1",
        title="Test Epic",
        description="Test epic for comment repository",
        project_id="test-project-1",
        status="Draft",
    )
    session.add(epic)

    # Create test story
    story = Story(
        id="test-story-1",
        title="Test Story",
        description="Test story for comment repository",
        acceptance_criteria=["Test AC 1"],
        epic_id="test-epic-1",
    )
    session.add(story)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def comment_repository(in_memory_db):
    """Create a CommentRepository instance."""
    return CommentRepository(in_memory_db)


def test_create_comment(comment_repository):
    """Test creating a comment."""
    comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
    )

    assert comment.id is not None
    assert comment.story_id == "test-story-1"
    assert comment.author_role == "Developer Agent"
    assert comment.content == "This is a test comment"
    assert comment.reply_to_id is None
    assert comment.timestamp is not None


def test_create_comment_with_reply(comment_repository):
    """Test creating a comment with reply_to_id."""
    # Create parent comment first
    parent_comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="Parent comment",
    )

    # Create reply comment
    reply_comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="QA Agent",
        content="Reply comment",
        reply_to_id=parent_comment.id,
    )

    assert reply_comment.reply_to_id == parent_comment.id


def test_get_comment_by_id(comment_repository):
    """Test retrieving a comment by ID."""
    # Create a comment first
    created_comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="Test comment",
    )

    # Retrieve it
    retrieved_comment = comment_repository.get_comment_by_id(created_comment.id)

    assert retrieved_comment.id == created_comment.id
    assert retrieved_comment.story_id == "test-story-1"
    assert retrieved_comment.author_role == "Developer Agent"
    assert retrieved_comment.content == "Test comment"


def test_get_comment_by_id_not_found(comment_repository):
    """Test retrieving a non-existent comment raises CommentNotFoundError."""
    with pytest.raises(CommentNotFoundError, match="Comment with id 'non-existent' not found"):
        comment_repository.get_comment_by_id("non-existent")


def test_get_comments_by_story_id(comment_repository):
    """Test retrieving all comments for a story."""
    # Create multiple comments
    comment1 = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="First comment",
    )
    comment2 = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="QA Agent",
        content="Second comment", 
    )

    # Retrieve comments for the story
    comments = comment_repository.get_comments_by_story_id("test-story-1")

    assert len(comments) == 2
    # Should be ordered by timestamp (ascending)
    assert comments[0].id == comment1.id
    assert comments[1].id == comment2.id


def test_get_comments_by_story_id_empty(comment_repository):
    """Test retrieving comments for a story with no comments."""
    comments = comment_repository.get_comments_by_story_id("test-story-1")
    assert len(comments) == 0


def test_update_comment(comment_repository):
    """Test updating a comment's content."""
    # Create a comment
    comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="Original content",
    )

    # Update the comment
    updated_comment = comment_repository.update_comment(
        comment_id=comment.id,
        content="Updated content",
    )

    assert updated_comment.id == comment.id
    assert updated_comment.content == "Updated content"
    assert updated_comment.author_role == "Developer Agent"  # Unchanged


def test_update_comment_not_found(comment_repository):
    """Test updating a non-existent comment raises CommentNotFoundError."""
    with pytest.raises(CommentNotFoundError):
        comment_repository.update_comment(
            comment_id="non-existent",
            content="New content",
        )


def test_delete_comment(comment_repository):
    """Test deleting a comment."""
    # Create a comment
    comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="Comment to delete",
    )

    # Delete the comment
    comment_repository.delete_comment(comment.id)

    # Verify it's deleted
    with pytest.raises(CommentNotFoundError):
        comment_repository.get_comment_by_id(comment.id)


def test_delete_comment_not_found(comment_repository):
    """Test deleting a non-existent comment raises CommentNotFoundError."""
    with pytest.raises(CommentNotFoundError):
        comment_repository.delete_comment("non-existent")


def test_get_comment_replies(comment_repository):
    """Test retrieving direct replies to a comment."""
    # Create parent comment
    parent_comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="Parent comment",
    )

    # Create reply comments
    reply1 = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="QA Agent",
        content="First reply",
        reply_to_id=parent_comment.id,
    )
    reply2 = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Human Reviewer",
        content="Second reply",
        reply_to_id=parent_comment.id,
    )

    # Create unrelated comment
    comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Scrum Master",
        content="Unrelated comment",
    )

    # Get replies
    replies = comment_repository.get_comment_replies(parent_comment.id)

    assert len(replies) == 2
    reply_ids = [reply.id for reply in replies]
    assert reply1.id in reply_ids
    assert reply2.id in reply_ids


def test_get_comment_replies_empty(comment_repository):
    """Test retrieving replies for a comment with no replies."""
    # Create a comment with no replies
    comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="Comment with no replies",
    )

    replies = comment_repository.get_comment_replies(comment.id)
    assert len(replies) == 0


def test_get_comment_thread(comment_repository):
    """Test retrieving a complete comment thread."""
    # Create parent comment
    parent_comment = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Developer Agent",
        content="Parent comment",
    )

    # Create first-level replies
    reply1 = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="QA Agent",
        content="First reply",
        reply_to_id=parent_comment.id,
    )
    reply2 = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Human Reviewer",
        content="Second reply",
        reply_to_id=parent_comment.id,
    )

    # Create second-level reply (reply to reply1)
    nested_reply = comment_repository.create_comment(
        story_id="test-story-1",
        author_role="Scrum Master",
        content="Nested reply",
        reply_to_id=reply1.id,
    )

    # Get complete thread
    thread = comment_repository.get_comment_thread(parent_comment.id)

    assert len(thread) == 4  # Parent + 2 replies + 1 nested reply
    thread_ids = [comment.id for comment in thread]
    assert parent_comment.id in thread_ids
    assert reply1.id in thread_ids
    assert reply2.id in thread_ids
    assert nested_reply.id in thread_ids


def test_get_comment_thread_not_found(comment_repository):
    """Test retrieving thread for non-existent comment raises CommentNotFoundError."""
    with pytest.raises(CommentNotFoundError):
        comment_repository.get_comment_thread("non-existent")