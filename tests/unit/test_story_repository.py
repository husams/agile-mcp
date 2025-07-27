"""
Unit tests for Story repository.
"""

import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.agile_mcp.models.epic import Epic, Base
from src.agile_mcp.models.story import Story
from src.agile_mcp.repositories.story_repository import StoryRepository


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create a test epic for foreign key relationships
    epic = Epic(
        id="test-epic-1",
        title="Test Epic",
        description="Test epic for story relationships",
        status="Draft"
    )
    session.add(epic)
    session.commit()
    
    yield session
    session.close()


@pytest.fixture
def story_repository(in_memory_db):
    """Create Story repository with test database session."""
    return StoryRepository(in_memory_db)


def test_create_story(story_repository):
    """Test story creation through repository."""
    story = story_repository.create_story(
        title="Test Story",
        description="As a user, I want to test the story repository",
        acceptance_criteria=["Should create successfully", "Should have valid ID"],
        epic_id="test-epic-1"
    )
    
    assert story.id is not None
    assert story.title == "Test Story"
    assert story.description == "As a user, I want to test the story repository"
    assert story.acceptance_criteria == ["Should create successfully", "Should have valid ID"]
    assert story.epic_id == "test-epic-1"
    assert story.status == "ToDo"
    
    # Verify UUID format
    uuid.UUID(story.id)  # This will raise ValueError if not valid UUID


def test_create_story_with_invalid_epic_id(story_repository):
    """Test story creation with non-existent epic ID."""
    with pytest.raises(IntegrityError):
        story_repository.create_story(
            title="Test Story",
            description="This should fail",
            acceptance_criteria=["Should fail"],
            epic_id="non-existent-epic"
        )


def test_find_story_by_id_exists(story_repository):
    """Test finding story by ID when it exists."""
    # Create a story first
    created_story = story_repository.create_story(
        title="Findable Story",
        description="This story can be found",
        acceptance_criteria=["Should be findable"],
        epic_id="test-epic-1"
    )
    
    # Find the story
    found_story = story_repository.find_story_by_id(created_story.id)
    
    assert found_story is not None
    assert found_story.id == created_story.id
    assert found_story.title == "Findable Story"
    assert found_story.description == "This story can be found"
    assert found_story.acceptance_criteria == ["Should be findable"]
    assert found_story.epic_id == "test-epic-1"
    assert found_story.status == "ToDo"


def test_find_story_by_id_not_exists(story_repository):
    """Test finding story by ID when it doesn't exist."""
    found_story = story_repository.find_story_by_id("non-existent-id")
    assert found_story is None


def test_find_stories_by_epic_id_with_stories(story_repository):
    """Test finding stories by epic ID when stories exist."""
    # Create multiple stories for the same epic
    story1 = story_repository.create_story(
        title="First Story",
        description="First story description",
        acceptance_criteria=["AC1"],
        epic_id="test-epic-1"
    )
    
    story2 = story_repository.create_story(
        title="Second Story",
        description="Second story description", 
        acceptance_criteria=["AC2"],
        epic_id="test-epic-1"
    )
    
    # Find stories by epic ID
    stories = story_repository.find_stories_by_epic_id("test-epic-1")
    
    assert len(stories) == 2
    story_ids = [story.id for story in stories]
    assert story1.id in story_ids
    assert story2.id in story_ids


def test_find_stories_by_epic_id_empty(story_repository):
    """Test finding stories by epic ID when no stories exist."""
    stories = story_repository.find_stories_by_epic_id("test-epic-1")
    assert stories == []


def test_find_stories_by_epic_id_non_existent_epic(story_repository):
    """Test finding stories by non-existent epic ID."""
    stories = story_repository.find_stories_by_epic_id("non-existent-epic")
    assert stories == []


def test_create_multiple_stories_same_epic(story_repository):
    """Test creating multiple stories for the same epic."""
    story1 = story_repository.create_story(
        title="Story 1",
        description="First story",
        acceptance_criteria=["AC1"],
        epic_id="test-epic-1"
    )
    
    story2 = story_repository.create_story(
        title="Story 2", 
        description="Second story",
        acceptance_criteria=["AC2"],
        epic_id="test-epic-1"
    )
    
    # Both should have different IDs
    assert story1.id != story2.id
    assert story1.epic_id == story2.epic_id == "test-epic-1"
    
    # Both should be findable
    found_story1 = story_repository.find_story_by_id(story1.id)
    found_story2 = story_repository.find_story_by_id(story2.id)
    
    assert found_story1 is not None
    assert found_story2 is not None
    assert found_story1.title == "Story 1"
    assert found_story2.title == "Story 2"


def test_story_repository_handles_database_session(story_repository):
    """Test that repository properly manages database session operations."""
    # Create story (involves commit)
    story = story_repository.create_story(
        title="Session Test Story",
        description="Testing session management",
        acceptance_criteria=["Should handle sessions"],
        epic_id="test-epic-1"
    )
    
    # Immediately find it (should be committed)
    found_story = story_repository.find_story_by_id(story.id)
    assert found_story is not None
    assert found_story.title == "Session Test Story"


def test_create_story_with_complex_acceptance_criteria(story_repository):
    """Test creating story with complex acceptance criteria."""
    complex_criteria = [
        "Given I am a user",
        "When I perform an action", 
        "Then I should see expected result",
        "And the system should log the event",
        "But it should not expose sensitive data"
    ]
    
    story = story_repository.create_story(
        title="Complex Story",
        description="Story with detailed acceptance criteria",
        acceptance_criteria=complex_criteria,
        epic_id="test-epic-1"
    )
    
    assert story.acceptance_criteria == complex_criteria
    
    # Verify it persists correctly
    found_story = story_repository.find_story_by_id(story.id)
    assert found_story.acceptance_criteria == complex_criteria


def test_update_story_status_success(story_repository):
    """Test successful story status update."""
    # Create a story first
    story = story_repository.create_story(
        title="Status Update Story",
        description="Story to test status updates",
        acceptance_criteria=["Should update status"],
        epic_id="test-epic-1"
    )
    assert story.status == "ToDo"
    
    # Update the status
    updated_story = story_repository.update_story_status(story.id, "InProgress")
    
    assert updated_story is not None
    assert updated_story.id == story.id
    assert updated_story.status == "InProgress"
    assert updated_story.title == "Status Update Story"
    
    # Verify persistence
    found_story = story_repository.find_story_by_id(story.id)
    assert found_story.status == "InProgress"


def test_update_story_status_all_valid_statuses(story_repository):
    """Test updating story to all valid status values."""
    # Create a story
    story = story_repository.create_story(
        title="Multi-Status Story",
        description="Story to test all status transitions",
        acceptance_criteria=["Should work with all statuses"],
        epic_id="test-epic-1"
    )
    
    valid_statuses = ["ToDo", "InProgress", "Review", "Done"]
    
    for status in valid_statuses:
        updated_story = story_repository.update_story_status(story.id, status)
        assert updated_story is not None
        assert updated_story.status == status
        
        # Verify persistence after each update
        found_story = story_repository.find_story_by_id(story.id)
        assert found_story.status == status


def test_update_story_status_nonexistent_story(story_repository):
    """Test updating status of non-existent story."""
    updated_story = story_repository.update_story_status("non-existent-id", "InProgress")
    assert updated_story is None


def test_update_story_status_invalid_status_raises_error(story_repository):
    """Test that invalid status raises validation error."""
    # Create a story first
    story = story_repository.create_story(
        title="Validation Test Story",
        description="Story to test validation",
        acceptance_criteria=["Should validate status"],
        epic_id="test-epic-1"
    )
    
    # Try to update with invalid status - this should trigger model validation
    with pytest.raises(ValueError, match="Story status must be one of"):
        story_repository.update_story_status(story.id, "InvalidStatus")


def test_update_story_status_atomic_transaction(story_repository):
    """Test that status update is atomic."""
    # Create a story
    story = story_repository.create_story(
        title="Transaction Test Story",
        description="Story to test transaction atomicity",
        acceptance_criteria=["Should handle transactions properly"],
        epic_id="test-epic-1"
    )
    original_status = story.status
    
    # Try to update with invalid status (should rollback)
    try:
        story_repository.update_story_status(story.id, "InvalidStatus")
    except ValueError:
        pass  # Expected to fail
    
    # Verify original status is preserved
    found_story = story_repository.find_story_by_id(story.id)
    assert found_story.status == original_status


def test_update_story_status_multiple_stories(story_repository):
    """Test updating status of multiple different stories."""
    # Create multiple stories
    story1 = story_repository.create_story(
        title="Story 1",
        description="First story",
        acceptance_criteria=["AC1"],
        epic_id="test-epic-1"
    )
    
    story2 = story_repository.create_story(
        title="Story 2", 
        description="Second story",
        acceptance_criteria=["AC2"],
        epic_id="test-epic-1"
    )
    
    # Update different statuses
    updated_story1 = story_repository.update_story_status(story1.id, "InProgress")
    updated_story2 = story_repository.update_story_status(story2.id, "Review")
    
    assert updated_story1.status == "InProgress"
    assert updated_story2.status == "Review"
    
    # Verify persistence and that they don't affect each other
    found_story1 = story_repository.find_story_by_id(story1.id)
    found_story2 = story_repository.find_story_by_id(story2.id)
    
    assert found_story1.status == "InProgress"
    assert found_story2.status == "Review"