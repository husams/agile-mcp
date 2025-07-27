"""
Unit tests for Dependency service layer.
"""

from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.agile_mcp.models.story import Story
from src.agile_mcp.services.dependency_service import DependencyService
from src.agile_mcp.services.exceptions import (
    CircularDependencyError,
    DatabaseError,
    DependencyValidationError,
    DuplicateDependencyError,
    StoryNotFoundError,
)


@pytest.fixture
def mock_dependency_repository():
    """Create a mock Dependency repository."""
    return Mock()


@pytest.fixture
def dependency_service(mock_dependency_repository):
    """Create Dependency service with mock repository."""
    return DependencyService(mock_dependency_repository)


def test_add_story_dependency_success(dependency_service, mock_dependency_repository):
    """Test successful dependency addition."""
    # Setup mocks
    mock_dependency_repository.story_exists.side_effect = lambda story_id: True
    mock_dependency_repository.has_circular_dependency.return_value = False
    mock_dependency_repository.add_dependency.return_value = True

    # Test service call
    result = dependency_service.add_story_dependency("story-1", "story-2")

    # Verify result and repository calls
    assert result["status"] == "success"
    assert result["story_id"] == "story-1"
    assert result["depends_on_story_id"] == "story-2"
    assert "Dependency added" in result["message"]

    mock_dependency_repository.story_exists.assert_any_call("story-1")
    mock_dependency_repository.story_exists.assert_any_call("story-2")
    mock_dependency_repository.has_circular_dependency.assert_called_once_with(
        "story-1", "story-2"
    )
    mock_dependency_repository.add_dependency.assert_called_once_with(
        "story-1", "story-2"
    )


def test_add_story_dependency_circular_detection(
    dependency_service, mock_dependency_repository
):
    """Test circular dependency prevention."""
    # Setup circular dependency scenario
    mock_dependency_repository.story_exists.side_effect = lambda story_id: True
    mock_dependency_repository.has_circular_dependency.return_value = True

    # Test service call raises exception
    with pytest.raises(CircularDependencyError) as exc_info:
        dependency_service.add_story_dependency("story-1", "story-2")

    assert "circular dependency" in str(exc_info.value).lower()
    mock_dependency_repository.add_dependency.assert_not_called()


def test_add_story_dependency_story_not_found(
    dependency_service, mock_dependency_repository
):
    """Test story not found error."""
    # Setup first story doesn't exist
    mock_dependency_repository.story_exists.side_effect = (
        lambda story_id: story_id != "story-1"
    )

    # Test service call raises exception
    with pytest.raises(StoryNotFoundError) as exc_info:
        dependency_service.add_story_dependency("story-1", "story-2")

    assert "story-1" in str(exc_info.value)
    mock_dependency_repository.add_dependency.assert_not_called()


def test_add_story_dependency_depends_on_story_not_found(
    dependency_service, mock_dependency_repository
):
    """Test dependency story not found error."""
    # Setup second story doesn't exist
    mock_dependency_repository.story_exists.side_effect = (
        lambda story_id: story_id != "story-2"
    )

    # Test service call raises exception
    with pytest.raises(StoryNotFoundError) as exc_info:
        dependency_service.add_story_dependency("story-1", "story-2")

    assert "story-2" in str(exc_info.value)
    mock_dependency_repository.add_dependency.assert_not_called()


def test_add_story_dependency_self_dependency(
    dependency_service, mock_dependency_repository
):
    """Test prevention of self-dependency."""
    # Test service call raises exception
    with pytest.raises(DependencyValidationError) as exc_info:
        dependency_service.add_story_dependency("story-1", "story-1")

    assert "cannot depend on itself" in str(exc_info.value).lower()
    mock_dependency_repository.story_exists.assert_not_called()


def test_add_story_dependency_duplicate_dependency(
    dependency_service, mock_dependency_repository
):
    """Test duplicate dependency handling."""
    # Setup mocks
    mock_dependency_repository.story_exists.side_effect = lambda story_id: True
    mock_dependency_repository.has_circular_dependency.return_value = False
    mock_dependency_repository.add_dependency.return_value = (
        False  # Dependency already exists
    )

    # Test service call raises exception
    with pytest.raises(DuplicateDependencyError) as exc_info:
        dependency_service.add_story_dependency("story-1", "story-2")

    assert "already exists" in str(exc_info.value).lower()


def test_add_story_dependency_empty_story_id(
    dependency_service, mock_dependency_repository
):
    """Test validation of empty story ID."""
    with pytest.raises(DependencyValidationError) as exc_info:
        dependency_service.add_story_dependency("", "story-2")

    assert "Story ID cannot be empty" in str(exc_info.value)


def test_add_story_dependency_empty_depends_on_story_id(
    dependency_service, mock_dependency_repository
):
    """Test validation of empty dependency story ID."""
    with pytest.raises(DependencyValidationError) as exc_info:
        dependency_service.add_story_dependency("story-1", "")

    assert "Dependency story ID cannot be empty" in str(exc_info.value)


def test_add_story_dependency_whitespace_story_ids(
    dependency_service, mock_dependency_repository
):
    """Test handling of whitespace in story IDs."""
    # Setup mocks
    mock_dependency_repository.story_exists.side_effect = lambda story_id: True
    mock_dependency_repository.has_circular_dependency.return_value = False
    mock_dependency_repository.add_dependency.return_value = True

    # Test service call with whitespace
    result = dependency_service.add_story_dependency("  story-1  ", "  story-2  ")

    # Verify result and that IDs were trimmed
    assert result["story_id"] == "story-1"
    assert result["depends_on_story_id"] == "story-2"

    mock_dependency_repository.story_exists.assert_any_call("story-1")
    mock_dependency_repository.story_exists.assert_any_call("story-2")
    mock_dependency_repository.add_dependency.assert_called_once_with(
        "story-1", "story-2"
    )


def test_add_story_dependency_database_error(
    dependency_service, mock_dependency_repository
):
    """Test database error handling."""
    # Setup database error
    mock_dependency_repository.story_exists.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    # Test service call raises exception
    with pytest.raises(DatabaseError) as exc_info:
        dependency_service.add_story_dependency("story-1", "story-2")

    assert "Database operation failed" in str(exc_info.value)


def test_get_story_dependencies_success(dependency_service, mock_dependency_repository):
    """Test successful retrieval of story dependencies."""
    # Setup mock dependencies
    mock_story_1 = Story(
        id="dependency-1",
        title="Dependency Story 1",
        description="First dependency",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
    )
    mock_story_2 = Story(
        id="dependency-2",
        title="Dependency Story 2",
        description="Second dependency",
        acceptance_criteria=["AC2"],
        epic_id="epic-1",
        status="Done",
    )

    mock_dependency_repository.story_exists.return_value = True
    mock_dependency_repository.get_story_dependencies.return_value = [
        mock_story_1,
        mock_story_2,
    ]

    # Test service call
    result = dependency_service.get_story_dependencies("story-1")

    # Verify result
    assert len(result) == 2
    assert result[0]["id"] == "dependency-1"
    assert result[0]["title"] == "Dependency Story 1"
    assert result[1]["id"] == "dependency-2"
    assert result[1]["title"] == "Dependency Story 2"

    mock_dependency_repository.story_exists.assert_called_once_with("story-1")
    mock_dependency_repository.get_story_dependencies.assert_called_once_with("story-1")


def test_get_story_dependencies_empty_list(
    dependency_service, mock_dependency_repository
):
    """Test retrieval when story has no dependencies."""
    mock_dependency_repository.story_exists.return_value = True
    mock_dependency_repository.get_story_dependencies.return_value = []

    # Test service call
    result = dependency_service.get_story_dependencies("story-1")

    # Verify result
    assert result == []


def test_get_story_dependencies_story_not_found(
    dependency_service, mock_dependency_repository
):
    """Test story not found error in get dependencies."""
    mock_dependency_repository.story_exists.return_value = False

    # Test service call raises exception
    with pytest.raises(StoryNotFoundError) as exc_info:
        dependency_service.get_story_dependencies("nonexistent-story")

    assert "nonexistent-story" in str(exc_info.value)
    mock_dependency_repository.get_story_dependencies.assert_not_called()


def test_get_story_dependents_success(dependency_service, mock_dependency_repository):
    """Test successful retrieval of story dependents."""
    # Setup mock dependents
    mock_story = Story(
        id="dependent-1",
        title="Dependent Story",
        description="Story that depends on this one",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
    )

    mock_dependency_repository.story_exists.return_value = True
    mock_dependency_repository.get_story_dependents.return_value = [mock_story]

    # Test service call
    result = dependency_service.get_story_dependents("story-1")

    # Verify result
    assert len(result) == 1
    assert result[0]["id"] == "dependent-1"
    assert result[0]["title"] == "Dependent Story"

    mock_dependency_repository.story_exists.assert_called_once_with("story-1")
    mock_dependency_repository.get_story_dependents.assert_called_once_with("story-1")


def test_remove_story_dependency_success(
    dependency_service, mock_dependency_repository
):
    """Test successful dependency removal."""
    mock_dependency_repository.remove_dependency.return_value = True

    # Test service call
    result = dependency_service.remove_story_dependency("story-1", "story-2")

    # Verify result
    assert result["status"] == "success"
    assert result["story_id"] == "story-1"
    assert result["depends_on_story_id"] == "story-2"
    assert "no longer depends" in result["message"]

    mock_dependency_repository.remove_dependency.assert_called_once_with(
        "story-1", "story-2"
    )


def test_remove_story_dependency_not_found(
    dependency_service, mock_dependency_repository
):
    """Test removal of non-existent dependency."""
    mock_dependency_repository.remove_dependency.return_value = False

    # Test service call raises exception
    with pytest.raises(StoryNotFoundError) as exc_info:
        dependency_service.remove_story_dependency("story-1", "story-2")

    assert "does not exist" in str(exc_info.value)


def test_validate_dependency_graph_success(
    dependency_service, mock_dependency_repository
):
    """Test successful dependency graph validation."""
    # Setup mock dependencies
    mock_story = Story(
        id="dependency-1",
        title="Dependency Story",
        description="A dependency",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
    )

    mock_dependency_repository.story_exists.return_value = True
    mock_dependency_repository.get_story_dependencies.return_value = [mock_story]
    mock_dependency_repository.has_circular_dependency.return_value = False

    # Test service call
    result = dependency_service.validate_dependency_graph("story-1")

    # Verify result
    assert result["status"] == "valid"
    assert result["story_id"] == "story-1"
    assert result["total_dependencies"] == 1
    assert result["dependency_chain"] == ["dependency-1"]
    assert result["issues"] == []


def test_validate_dependency_graph_with_circular_dependency(
    dependency_service, mock_dependency_repository
):
    """Test dependency graph validation with circular dependency."""
    # Setup mock dependencies with circular reference
    mock_story = Story(
        id="dependency-1",
        title="Dependency Story",
        description="A dependency",
        acceptance_criteria=["AC1"],
        epic_id="epic-1",
        status="ToDo",
    )

    mock_dependency_repository.story_exists.return_value = True
    mock_dependency_repository.get_story_dependencies.return_value = [mock_story]
    mock_dependency_repository.has_circular_dependency.return_value = True

    # Test service call
    result = dependency_service.validate_dependency_graph("story-1")

    # Verify result
    assert result["status"] == "invalid"
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "circular_dependency"
    assert "dependency-1" in result["issues"][0]["description"]
