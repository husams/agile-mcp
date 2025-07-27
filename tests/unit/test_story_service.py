"""
Unit tests for Story service layer.
"""

from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.agile_mcp.models.story import Story
from src.agile_mcp.services.exceptions import (
    DatabaseError,
    EpicNotFoundError,
    InvalidStoryStatusError,
    StoryNotFoundError,
    StoryValidationError,
)
from src.agile_mcp.services.story_service import StoryService


@pytest.fixture
def mock_repository():
    """Create a mock Story repository."""
    return Mock()


@pytest.fixture
def story_service(mock_repository):
    """Create Story service with mock repository."""
    return StoryService(mock_repository)


def test_create_story_success(story_service, mock_repository):
    """Test successful story creation."""
    # Setup mock
    mock_story = Story(
        id="test-story-id",
        title="Test Story",
        description="As a user, I want to test",
        acceptance_criteria=["Should work", "Should pass tests"],
        epic_id="test-epic-id",
        status="ToDo",
    )
    mock_repository.create_story.return_value = mock_story

    # Call service method
    result = story_service.create_story(
        title="Test Story",
        description="As a user, I want to test",
        acceptance_criteria=["Should work", "Should pass tests"],
        epic_id="test-epic-id",
    )

    # Verify result contains all expected fields
    assert result["id"] == "test-story-id"
    assert result["title"] == "Test Story"
    assert result["description"] == "As a user, I want to test"
    assert result["acceptance_criteria"] == ["Should work", "Should pass tests"]
    assert result["epic_id"] == "test-epic-id"
    assert result["status"] == "ToDo"
    assert result["priority"] == 0
    assert "created_at" in result
    mock_repository.create_story.assert_called_once_with(
        "Test Story",
        "As a user, I want to test",
        ["Should work", "Should pass tests"],
        "test-epic-id",
    )


def test_create_story_empty_title(story_service, mock_repository):
    """Test story creation with empty title."""
    with pytest.raises(StoryValidationError, match="Story title cannot be empty"):
        story_service.create_story(
            title="",
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_whitespace_only_title(story_service, mock_repository):
    """Test story creation with whitespace-only title."""
    with pytest.raises(StoryValidationError, match="Story title cannot be empty"):
        story_service.create_story(
            title="   ",
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_title_too_long(story_service, mock_repository):
    """Test story creation with title too long."""
    long_title = "x" * 201
    with pytest.raises(
        StoryValidationError, match="Story title cannot exceed 200 characters"
    ):
        story_service.create_story(
            title=long_title,
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_empty_description(story_service, mock_repository):
    """Test story creation with empty description."""
    with pytest.raises(StoryValidationError, match="Story description cannot be empty"):
        story_service.create_story(
            title="Valid title",
            description="",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_description_too_long(story_service, mock_repository):
    """Test story creation with description too long."""
    long_description = "x" * 2001
    with pytest.raises(
        StoryValidationError, match="Story description cannot exceed 2000 characters"
    ):
        story_service.create_story(
            title="Valid title",
            description=long_description,
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_empty_acceptance_criteria(story_service, mock_repository):
    """Test story creation with empty acceptance criteria."""
    with pytest.raises(
        StoryValidationError, match="At least one acceptance criterion is required"
    ):
        story_service.create_story(
            title="Valid title",
            description="Valid description",
            acceptance_criteria=[],
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_non_list_acceptance_criteria(story_service, mock_repository):
    """Test story creation with non-list acceptance criteria."""
    with pytest.raises(
        StoryValidationError, match="Acceptance criteria must be a non-empty list"
    ):
        story_service.create_story(
            title="Valid title",
            description="Valid description",
            acceptance_criteria="not a list",
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_empty_acceptance_criterion(story_service, mock_repository):
    """Test story creation with empty string in acceptance criteria."""
    with pytest.raises(
        StoryValidationError,
        match="Each acceptance criterion must be a non-empty string",
    ):
        story_service.create_story(
            title="Valid title",
            description="Valid description",
            acceptance_criteria=["Valid AC", ""],
            epic_id="test-epic-id",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_empty_epic_id(story_service, mock_repository):
    """Test story creation with empty epic ID."""
    with pytest.raises(StoryValidationError, match="Epic ID cannot be empty"):
        story_service.create_story(
            title="Valid title",
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="",
        )
    mock_repository.create_story.assert_not_called()


def test_create_story_epic_not_found(story_service, mock_repository):
    """Test story creation when epic doesn't exist."""
    mock_repository.create_story.side_effect = IntegrityError(
        statement="INSERT",
        params={},
        orig=Exception("Epic with id 'non-existent' does not exist"),
    )

    with pytest.raises(
        EpicNotFoundError, match="Epic with ID 'test-epic-id' not found"
    ):
        story_service.create_story(
            title="Valid title",
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-id",
        )


def test_create_story_database_error(story_service, mock_repository):
    """Test story creation with database error."""
    mock_repository.create_story.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    with pytest.raises(DatabaseError, match="Database operation failed"):
        story_service.create_story(
            title="Valid title",
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-id",
        )


def test_get_story_success(story_service, mock_repository):
    """Test successful story retrieval."""
    mock_story = Story(
        id="test-story-id",
        title="Found Story",
        description="This story was found",
        acceptance_criteria=["Should be found"],
        epic_id="test-epic-id",
        status="InProgress",
    )
    mock_repository.find_story_by_id.return_value = mock_story

    result = story_service.get_story("test-story-id")

    # Verify result contains all expected fields
    assert result["id"] == "test-story-id"
    assert result["title"] == "Found Story"
    assert result["description"] == "This story was found"
    assert result["acceptance_criteria"] == ["Should be found"]
    assert result["epic_id"] == "test-epic-id"
    assert result["status"] == "InProgress"
    assert result["priority"] == 0
    assert "created_at" in result
    mock_repository.find_story_by_id.assert_called_once_with("test-story-id")


def test_get_story_not_found(story_service, mock_repository):
    """Test story retrieval when story doesn't exist."""
    mock_repository.find_story_by_id.return_value = None

    with pytest.raises(
        StoryNotFoundError, match="Story with ID 'non-existent' not found"
    ):
        story_service.get_story("non-existent")


def test_get_story_empty_id(story_service, mock_repository):
    """Test story retrieval with empty ID."""
    with pytest.raises(StoryValidationError, match="Story ID cannot be empty"):
        story_service.get_story("")
    mock_repository.find_story_by_id.assert_not_called()


def test_get_story_database_error(story_service, mock_repository):
    """Test story retrieval with database error."""
    mock_repository.find_story_by_id.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    with pytest.raises(
        DatabaseError, match="Database operation failed while retrieving story"
    ):
        story_service.get_story("test-story-id")


def test_find_stories_by_epic_success(story_service, mock_repository):
    """Test successful stories retrieval by epic."""
    mock_stories = [
        Story(
            id="story-1",
            title="Story 1",
            description="First story",
            acceptance_criteria=["AC1"],
            epic_id="test-epic-id",
            status="ToDo",
        ),
        Story(
            id="story-2",
            title="Story 2",
            description="Second story",
            acceptance_criteria=["AC2"],
            epic_id="test-epic-id",
            status="Done",
        ),
    ]
    mock_repository.find_stories_by_epic_id.return_value = mock_stories

    result = story_service.find_stories_by_epic("test-epic-id")

    # Verify result structure and content
    assert len(result) == 2

    # Check first story
    assert result[0]["id"] == "story-1"
    assert result[0]["title"] == "Story 1"
    assert result[0]["description"] == "First story"
    assert result[0]["acceptance_criteria"] == ["AC1"]
    assert result[0]["epic_id"] == "test-epic-id"
    assert result[0]["status"] == "ToDo"
    assert result[0]["priority"] == 0
    assert "created_at" in result[0]

    # Check second story
    assert result[1]["id"] == "story-2"
    assert result[1]["title"] == "Story 2"
    assert result[1]["description"] == "Second story"
    assert result[1]["acceptance_criteria"] == ["AC2"]
    assert result[1]["epic_id"] == "test-epic-id"
    assert result[1]["status"] == "Done"
    assert result[1]["priority"] == 0
    assert "created_at" in result[1]
    mock_repository.find_stories_by_epic_id.assert_called_once_with("test-epic-id")


def test_find_stories_by_epic_empty_epic_id(story_service, mock_repository):
    """Test finding stories with empty epic ID."""
    with pytest.raises(StoryValidationError, match="Epic ID cannot be empty"):
        story_service.find_stories_by_epic("")
    mock_repository.find_stories_by_epic_id.assert_not_called()


def test_find_stories_by_epic_database_error(story_service, mock_repository):
    """Test finding stories with database error."""
    mock_repository.find_stories_by_epic_id.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    with pytest.raises(
        DatabaseError, match="Database operation failed while retrieving stories"
    ):
        story_service.find_stories_by_epic("test-epic-id")


def test_create_story_strips_whitespace(story_service, mock_repository):
    """Test that create_story strips whitespace from inputs."""
    mock_story = Story(
        id="test-story-id",
        title="Test Story",
        description="Test description",
        acceptance_criteria=["AC1", "AC2"],
        epic_id="test-epic-id",
        status="ToDo",
    )
    mock_repository.create_story.return_value = mock_story

    story_service.create_story(
        title="  Test Story  ",
        description="  Test description  ",
        acceptance_criteria=["  AC1  ", "  AC2  "],
        epic_id="  test-epic-id  ",
    )

    mock_repository.create_story.assert_called_once_with(
        "Test Story", "Test description", ["AC1", "AC2"], "test-epic-id"
    )


def test_update_story_status_success(story_service, mock_repository):
    """Test successful story status update."""
    mock_story = Story(
        id="test-story-id",
        title="Test Story",
        description="Test description",
        acceptance_criteria=["AC1"],
        epic_id="test-epic-id",
        status="InProgress",
    )
    mock_repository.update_story_status.return_value = mock_story

    result = story_service.update_story_status("test-story-id", "InProgress")

    # Verify result contains all expected fields
    assert result["id"] == "test-story-id"
    assert result["title"] == "Test Story"
    assert result["description"] == "Test description"
    assert result["acceptance_criteria"] == ["AC1"]
    assert result["epic_id"] == "test-epic-id"
    assert result["status"] == "InProgress"
    assert result["priority"] == 0
    assert "created_at" in result
    mock_repository.update_story_status.assert_called_once_with(
        "test-story-id", "InProgress"
    )


def test_update_story_status_empty_story_id(story_service, mock_repository):
    """Test story status update with empty story ID."""
    with pytest.raises(StoryValidationError, match="Story ID cannot be empty"):
        story_service.update_story_status("", "InProgress")
    mock_repository.update_story_status.assert_not_called()


def test_update_story_status_whitespace_story_id(story_service, mock_repository):
    """Test story status update with whitespace-only story ID."""
    with pytest.raises(StoryValidationError, match="Story ID cannot be empty"):
        story_service.update_story_status("   ", "InProgress")
    mock_repository.update_story_status.assert_not_called()


def test_update_story_status_empty_status(story_service, mock_repository):
    """Test story status update with empty status."""
    with pytest.raises(
        InvalidStoryStatusError, match="Status must be a non-empty string"
    ):
        story_service.update_story_status("test-story-id", "")
    mock_repository.update_story_status.assert_not_called()


def test_update_story_status_non_string_status(story_service, mock_repository):
    """Test story status update with non-string status."""
    with pytest.raises(
        InvalidStoryStatusError, match="Status must be a non-empty string"
    ):
        story_service.update_story_status("test-story-id", None)
    mock_repository.update_story_status.assert_not_called()


def test_update_story_status_invalid_status(story_service, mock_repository):
    """Test story status update with invalid status."""
    with pytest.raises(
        InvalidStoryStatusError,
        match="Status must be one of: Done, InProgress, Review, ToDo",
    ):
        story_service.update_story_status("test-story-id", "InvalidStatus")
    mock_repository.update_story_status.assert_not_called()


def test_update_story_status_story_not_found(story_service, mock_repository):
    """Test story status update when story doesn't exist."""
    mock_repository.update_story_status.return_value = None

    with pytest.raises(
        StoryNotFoundError, match="Story with ID 'non-existent' not found"
    ):
        story_service.update_story_status("non-existent", "InProgress")


def test_update_story_status_model_validation_error(story_service, mock_repository):
    """Test story status update with model validation error from repository."""
    mock_story = Mock()
    mock_repository.update_story_status.return_value = mock_story
    mock_repository.update_story_status.side_effect = ValueError(
        "Invalid status from model"
    )

    with pytest.raises(InvalidStoryStatusError, match="Invalid status from model"):
        story_service.update_story_status(
            "test-story-id", "InProgress"
        )  # Use valid status to bypass service validation


def test_update_story_status_database_error(story_service, mock_repository):
    """Test story status update with database error."""
    mock_repository.update_story_status.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    with pytest.raises(
        DatabaseError, match="Database operation failed while updating story status"
    ):
        story_service.update_story_status("test-story-id", "InProgress")


def test_update_story_status_valid_statuses(story_service, mock_repository):
    """Test story status update with all valid status values."""
    valid_statuses = ["ToDo", "InProgress", "Review", "Done"]

    for status in valid_statuses:
        mock_story = Story(
            id="test-story-id",
            title="Test Story",
            description="Test description",
            acceptance_criteria=["AC1"],
            epic_id="test-epic-id",
            status=status,
        )
        mock_repository.update_story_status.return_value = mock_story

        result = story_service.update_story_status("test-story-id", status)
        assert result["status"] == status


def test_update_story_status_strips_whitespace(story_service, mock_repository):
    """Test that update_story_status strips whitespace from story_id."""
    mock_story = Story(
        id="test-story-id",
        title="Test Story",
        description="Test description",
        acceptance_criteria=["AC1"],
        epic_id="test-epic-id",
        status="InProgress",
    )
    mock_repository.update_story_status.return_value = mock_story

    story_service.update_story_status("  test-story-id  ", "InProgress")

    mock_repository.update_story_status.assert_called_once_with(
        "test-story-id", "InProgress"
    )


# Tests for get_next_ready_story method


@pytest.fixture
def mock_dependency_repository():
    """Create a mock Dependency repository."""
    return Mock()


@pytest.fixture
def story_service_with_dependencies(mock_repository, mock_dependency_repository):
    """Create Story service with both repository mocks."""
    return StoryService(mock_repository, mock_dependency_repository)


def test_get_next_ready_story_no_dependency_repository(story_service):
    """Test get_next_ready_story raises error when dependency repository is not provided."""
    with pytest.raises(StoryValidationError, match="Dependency repository required"):
        story_service.get_next_ready_story()


def test_get_next_ready_story_no_stories(
    story_service_with_dependencies, mock_repository, mock_dependency_repository
):
    """Test get_next_ready_story returns None when no ToDo stories exist."""
    # Setup mocks - no ToDo stories
    mock_repository.find_stories_by_status_ordered.return_value = []

    result = story_service_with_dependencies.get_next_ready_story()

    assert result is None
    mock_repository.find_stories_by_status_ordered.assert_called_once_with("ToDo")


def test_get_next_ready_story_all_have_dependencies(
    story_service_with_dependencies, mock_repository, mock_dependency_repository
):
    """Test get_next_ready_story returns None when all stories have incomplete dependencies."""
    from datetime import datetime

    # Setup mock stories - all have incomplete dependencies
    story1 = Story(
        id="story-1",
        title="Story 1",
        description="Description 1",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
        priority=1,
        created_at=datetime(2023, 1, 1),
    )
    story2 = Story(
        id="story-2",
        title="Story 2",
        description="Description 2",
        acceptance_criteria=["AC2"],
        epic_id="epic-1",
        status="ToDo",
        priority=2,
        created_at=datetime(2023, 1, 2),
    )

    mock_repository.find_stories_by_status_ordered.return_value = [
        story2,
        story1,
    ]  # Ordered by priority
    mock_dependency_repository.has_incomplete_dependencies.side_effect = [
        True,
        True,
    ]  # Both have dependencies

    result = story_service_with_dependencies.get_next_ready_story()

    assert result is None
    mock_repository.find_stories_by_status_ordered.assert_called_once_with("ToDo")
    assert mock_dependency_repository.has_incomplete_dependencies.call_count == 2


def test_get_next_ready_story_first_story_ready(
    story_service_with_dependencies, mock_repository, mock_dependency_repository
):
    """Test get_next_ready_story returns first story when it has no dependencies."""
    from datetime import datetime

    # Setup mock stories
    story1 = Story(
        id="story-1",
        title="Story 1",
        description="Description 1",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
        priority=5,
        created_at=datetime(2023, 1, 1),
    )
    story2 = Story(
        id="story-2",
        title="Story 2",
        description="Description 2",
        acceptance_criteria=["AC2"],
        epic_id="epic-1",
        status="ToDo",
        priority=3,
        created_at=datetime(2023, 1, 2),
    )

    # Updated story after status change
    updated_story1 = Story(
        id="story-1",
        title="Story 1",
        description="Description 1",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="InProgress",
        priority=5,
        created_at=datetime(2023, 1, 1),
    )

    mock_repository.find_stories_by_status_ordered.return_value = [
        story1,
        story2,
    ]  # Ordered by priority
    mock_dependency_repository.has_incomplete_dependencies.return_value = (
        False  # First story is ready
    )
    mock_repository.update_story_status.return_value = updated_story1

    result = story_service_with_dependencies.get_next_ready_story()

    # Verify result
    assert result is not None
    assert result["id"] == "story-1"
    assert result["status"] == "InProgress"

    # Verify calls
    mock_repository.find_stories_by_status_ordered.assert_called_once_with("ToDo")
    mock_dependency_repository.has_incomplete_dependencies.assert_called_once_with(
        "story-1"
    )
    mock_repository.update_story_status.assert_called_once_with("story-1", "InProgress")


def test_get_next_ready_story_second_story_ready(
    story_service_with_dependencies, mock_repository, mock_dependency_repository
):
    """Test get_next_ready_story returns second story when first has dependencies."""
    from datetime import datetime

    # Setup mock stories
    story1 = Story(
        id="story-1",
        title="Story 1",
        description="Description 1",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
        priority=5,
        created_at=datetime(2023, 1, 1),
    )
    story2 = Story(
        id="story-2",
        title="Story 2",
        description="Description 2",
        acceptance_criteria=["AC2"],
        epic_id="epic-1",
        status="ToDo",
        priority=3,
        created_at=datetime(2023, 1, 2),
    )

    # Updated story after status change
    updated_story2 = Story(
        id="story-2",
        title="Story 2",
        description="Description 2",
        acceptance_criteria=["AC2"],
        epic_id="epic-1",
        status="InProgress",
        priority=3,
        created_at=datetime(2023, 1, 2),
    )

    mock_repository.find_stories_by_status_ordered.return_value = [
        story1,
        story2,
    ]  # Ordered by priority
    mock_dependency_repository.has_incomplete_dependencies.side_effect = [
        True,
        False,
    ]  # First has deps, second doesn't
    mock_repository.update_story_status.return_value = updated_story2

    result = story_service_with_dependencies.get_next_ready_story()

    # Verify result
    assert result is not None
    assert result["id"] == "story-2"
    assert result["status"] == "InProgress"

    # Verify calls
    mock_repository.find_stories_by_status_ordered.assert_called_once_with("ToDo")
    assert mock_dependency_repository.has_incomplete_dependencies.call_count == 2
    mock_repository.update_story_status.assert_called_once_with("story-2", "InProgress")


def test_get_next_ready_story_status_update_fails(
    story_service_with_dependencies, mock_repository, mock_dependency_repository
):
    """Test get_next_ready_story handles status update failure gracefully."""
    from datetime import datetime

    story1 = Story(
        id="story-1",
        title="Story 1",
        description="Description 1",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
        priority=1,
        created_at=datetime(2023, 1, 1),
    )

    mock_repository.find_stories_by_status_ordered.return_value = [story1]
    mock_dependency_repository.has_incomplete_dependencies.return_value = False
    mock_repository.update_story_status.return_value = None  # Update fails

    result = story_service_with_dependencies.get_next_ready_story()

    assert result is None  # Should return None when update fails


def test_get_next_ready_story_database_error(
    story_service_with_dependencies, mock_repository, mock_dependency_repository
):
    """Test get_next_ready_story raises DatabaseError on SQLAlchemy exception."""
    mock_repository.find_stories_by_status_ordered.side_effect = SQLAlchemyError(
        "Database error"
    )

    with pytest.raises(DatabaseError, match="Database operation failed"):
        story_service_with_dependencies.get_next_ready_story()


def test_get_next_ready_story_dependency_check_error(
    story_service_with_dependencies, mock_repository, mock_dependency_repository
):
    """Test get_next_ready_story handles dependency check errors."""
    from datetime import datetime

    story1 = Story(
        id="story-1",
        title="Story 1",
        description="Description 1",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
        priority=1,
        created_at=datetime(2023, 1, 1),
    )

    mock_repository.find_stories_by_status_ordered.return_value = [story1]
    mock_dependency_repository.has_incomplete_dependencies.side_effect = (
        SQLAlchemyError("Dependency check failed")
    )

    with pytest.raises(DatabaseError, match="Database operation failed"):
        story_service_with_dependencies.get_next_ready_story()
