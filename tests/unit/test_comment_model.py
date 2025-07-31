"""
Unit tests for Comment model.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.comment import AuthorRole, Comment
from src.agile_mcp.models.epic import Base, Epic
from src.agile_mcp.models.project import Project
from src.agile_mcp.models.story import Story


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
        description="Test project for comment relationships",
    )
    session.add(project)

    # Create test epic for foreign key relationships
    epic = Epic(
        id="test-epic-1",
        title="Test Epic",
        description="Test epic for comment relationships",
        project_id="test-project-1",
        status="Draft",
    )
    session.add(epic)

    # Create test story for foreign key relationships
    story = Story(
        id="test-story-1",
        title="Test Story",
        description="Test story for comment relationships",
        acceptance_criteria=["Test AC 1"],
        epic_id="test-epic-1",
    )
    session.add(story)
    session.commit()

    yield session
    session.close()


def test_comment_creation():
    """Test Comment model creation with valid data."""
    comment = Comment(
        id="test-comment-1",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
    )

    assert comment.id == "test-comment-1"
    assert comment.story_id == "test-story-1"
    assert comment.author_role == "Developer Agent"
    assert comment.content == "This is a test comment"
    assert comment.reply_to_id is None
    assert isinstance(comment.timestamp, datetime)


def test_comment_with_reply():
    """Test Comment model creation with reply_to_id."""
    comment = Comment(
        id="test-comment-2",
        story_id="test-story-1",
        author_role="QA Agent",
        content="This is a reply comment",
        reply_to_id="test-comment-1",
    )

    assert comment.reply_to_id == "test-comment-1"


def test_comment_to_dict():
    """Test Comment model to_dict method."""
    test_time = datetime.now(timezone.utc)
    comment = Comment(
        id="test-comment-1",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
        timestamp=test_time,
    )

    result = comment.to_dict()

    assert result["id"] == "test-comment-1"
    assert result["story_id"] == "test-story-1"
    assert result["author_role"] == "Developer Agent"
    assert result["content"] == "This is a test comment"
    assert result["timestamp"] == test_time.isoformat()
    assert result["reply_to_id"] is None


def test_comment_author_role_validation():
    """Test Comment model author role validation."""
    # Valid role should work
    comment = Comment(
        id="test-comment-1",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
    )
    assert comment.author_role == "Developer Agent"

    # Invalid role should raise ValueError
    with pytest.raises(ValueError, match="Author role must be one of"):
        Comment(
            id="test-comment-2",
            story_id="test-story-1",
            author_role="Invalid Role",
            content="This is a test comment",
        )


def test_comment_content_validation():
    """Test Comment model content validation."""
    # Empty content should raise ValueError
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        Comment(
            id="test-comment-1",
            story_id="test-story-1",
            author_role="Developer Agent",
            content="",
        )

    # Whitespace-only content should raise ValueError
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        Comment(
            id="test-comment-2",
            story_id="test-story-1",
            author_role="Developer Agent",
            content="   ",
        )

    # Very long content should raise ValueError
    long_content = "x" * 10001
    with pytest.raises(ValueError, match="Comment content cannot exceed"):
        Comment(
            id="test-comment-3",
            story_id="test-story-1",
            author_role="Developer Agent",
            content=long_content,
        )


def test_comment_reply_to_validation():
    """Test Comment model reply_to_id validation."""
    # None should be valid
    comment = Comment(
        id="test-comment-1",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
        reply_to_id=None,
    )
    assert comment.reply_to_id is None

    # Valid string should work
    comment = Comment(
        id="test-comment-2",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
        reply_to_id="parent-comment-id",
    )
    assert comment.reply_to_id == "parent-comment-id"

    # Empty string should raise ValueError
    with pytest.raises(ValueError, match="reply_to_id must be None or a non-empty string"):
        Comment(
            id="test-comment-3",
            story_id="test-story-1",
            author_role="Developer Agent",
            content="This is a test comment",
            reply_to_id="",
        )

    # Self-reference should raise ValueError
    with pytest.raises(ValueError, match="Comment cannot reply to itself"):
        comment = Comment(
            id="test-comment-4",
            story_id="test-story-1",
            author_role="Developer Agent",
            content="This is a test comment",
        )
        comment.reply_to_id = "test-comment-4"


def test_comment_database_persistence(in_memory_db):
    """Test Comment model database persistence."""
    comment = Comment(
        id="test-comment-1",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
    )

    in_memory_db.add(comment)
    in_memory_db.commit()

    # Retrieve and verify
    retrieved = in_memory_db.query(Comment).filter(Comment.id == "test-comment-1").first()
    assert retrieved is not None
    assert retrieved.id == "test-comment-1"
    assert retrieved.story_id == "test-story-1"
    assert retrieved.author_role == "Developer Agent"
    assert retrieved.content == "This is a test comment"


def test_comment_story_relationship(in_memory_db):
    """Test Comment-Story relationship."""
    comment = Comment(
        id="test-comment-1",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a test comment",
    )

    in_memory_db.add(comment)
    in_memory_db.commit()

    # Test relationship
    retrieved_comment = in_memory_db.query(Comment).filter(Comment.id == "test-comment-1").first()
    assert retrieved_comment.story is not None
    assert retrieved_comment.story.id == "test-story-1"

    # Test reverse relationship
    retrieved_story = in_memory_db.query(Story).filter(Story.id == "test-story-1").first()
    assert len(retrieved_story.story_comments) == 1
    assert retrieved_story.story_comments[0].id == "test-comment-1"


def test_comment_threading_relationship(in_memory_db):
    """Test Comment threading (self-referential) relationship."""
    # Create parent comment
    parent_comment = Comment(
        id="parent-comment-1",
        story_id="test-story-1",
        author_role="Developer Agent",
        content="This is a parent comment",
    )
    in_memory_db.add(parent_comment)
    in_memory_db.commit()

    # Create reply comment
    reply_comment = Comment(
        id="reply-comment-1",
        story_id="test-story-1",
        author_role="QA Agent",
        content="This is a reply comment",
        reply_to_id="parent-comment-1",
    )
    in_memory_db.add(reply_comment)
    in_memory_db.commit()

    # Test that reply_to_id is properly set (basic functionality)
    retrieved_reply = in_memory_db.query(Comment).filter(Comment.id == "reply-comment-1").first()
    assert retrieved_reply.reply_to_id == "parent-comment-1"
    
    # Test that we can find the parent by querying
    parent_from_db = in_memory_db.query(Comment).filter(Comment.id == retrieved_reply.reply_to_id).first()
    assert parent_from_db is not None
    assert parent_from_db.id == "parent-comment-1"
    
    # Test that we can find replies by querying
    replies = in_memory_db.query(Comment).filter(Comment.reply_to_id == "parent-comment-1").all()
    assert len(replies) == 1
    assert replies[0].id == "reply-comment-1"


def test_author_role_enum():
    """Test AuthorRole enumeration functionality."""
    # Test enum values
    assert AuthorRole.DEVELOPER_AGENT.value == "Developer Agent"
    assert AuthorRole.QA_AGENT.value == "QA Agent"
    assert AuthorRole.SCRUM_MASTER.value == "Scrum Master"
    assert AuthorRole.PRODUCT_OWNER.value == "Product Owner"
    assert AuthorRole.HUMAN_REVIEWER.value == "Human Reviewer"
    assert AuthorRole.SYSTEM.value == "System"

    # Test get_valid_roles
    valid_roles = AuthorRole.get_valid_roles()
    assert "Developer Agent" in valid_roles
    assert "QA Agent" in valid_roles
    assert "Invalid Role" not in valid_roles

    # Test is_valid_role
    assert AuthorRole.is_valid_role("Developer Agent")
    assert AuthorRole.is_valid_role("QA Agent")
    assert not AuthorRole.is_valid_role("Invalid Role")

    # Test string representation
    assert str(AuthorRole.DEVELOPER_AGENT) == "Developer Agent"