"""
Unit tests for Epic service layer.
"""

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.agile_mcp.models.epic import Epic
from src.agile_mcp.services.epic_service import EpicService
from src.agile_mcp.services.exceptions import (
    DatabaseError,
    EpicNotFoundError,
    EpicValidationError,
    InvalidEpicStatusError,
)


@pytest.fixture
def mock_repository():
    """Create a mock Epic repository."""
    return Mock()


@pytest.fixture
def epic_service(mock_repository):
    """Create Epic service with mock repository."""
    return EpicService(mock_repository)


def test_create_epic_success(epic_service, mock_repository):
    """Test successful epic creation."""
    # Setup mock
    mock_epic = Epic(
        id="test-id",
        title="Test Epic",
        description="Test description",
        project_id="test-project-id",
        status="Draft",
    )
    mock_repository.create_epic.return_value = mock_epic

    # Call service method
    result = epic_service.create_epic(
        "Test Epic", "Test description", "test-project-id"
    )

    # Verify result
    expected = {
        "id": "test-id",
        "title": "Test Epic",
        "description": "Test description",
        "status": "Draft",
        "project_id": "test-project-id",
    }
    assert result == expected
    mock_repository.create_epic.assert_called_once_with(
        "Test Epic", "Test description", "test-project-id"
    )


def test_create_epic_empty_title(epic_service):
    """Test epic creation with empty title."""
    with pytest.raises(EpicValidationError, match="Epic title cannot be empty"):
        epic_service.create_epic("", "Valid description", "test-project-id")

    with pytest.raises(EpicValidationError, match="Epic title cannot be empty"):
        epic_service.create_epic("   ", "Valid description", "test-project-id")


def test_create_epic_empty_description(epic_service):
    """Test epic creation with empty description."""
    with pytest.raises(EpicValidationError, match="Epic description cannot be empty"):
        epic_service.create_epic("Valid title", "", "test-project-id")

    with pytest.raises(EpicValidationError, match="Epic description cannot be empty"):
        epic_service.create_epic("Valid title", "   ", "test-project-id")


def test_create_epic_empty_project_id(epic_service):
    """Test epic creation with empty project_id."""
    with pytest.raises(EpicValidationError, match="Epic project_id cannot be empty"):
        epic_service.create_epic("Valid title", "Valid description", "")

    with pytest.raises(EpicValidationError, match="Epic project_id cannot be empty"):
        epic_service.create_epic("Valid title", "Valid description", "   ")


def test_create_epic_title_too_long(epic_service):
    """Test epic creation with title too long."""
    long_title = "x" * 201  # Exceeds 200 character limit

    with pytest.raises(
        EpicValidationError, match="Epic title cannot exceed 200 characters"
    ):
        epic_service.create_epic(long_title, "Valid description", "test-project-id")


def test_create_epic_description_too_long(epic_service):
    """Test epic creation with description too long."""
    long_description = "x" * 2001  # Exceeds 2000 character limit

    with pytest.raises(
        EpicValidationError, match="Epic description cannot exceed 2000 characters"
    ):
        epic_service.create_epic("Valid title", long_description, "test-project-id")


def test_create_epic_database_error(epic_service, mock_repository):
    """Test epic creation with database error."""
    # Setup mock to raise SQLAlchemy error
    mock_repository.create_epic.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    with pytest.raises(
        DatabaseError, match="Database operation failed: Database connection failed"
    ):
        epic_service.create_epic("Valid title", "Valid description", "test-project-id")


def test_create_epic_strips_whitespace(epic_service, mock_repository):
    """Test that epic creation strips whitespace from inputs."""
    mock_epic = Epic(
        id="test-id",
        title="Test Epic",
        description="Test description",
        project_id="test-project-id",
        status="Draft",
    )
    mock_repository.create_epic.return_value = mock_epic

    epic_service.create_epic(
        "  Test Epic  ", "  Test description  ", "  test-project-id  "
    )

    mock_repository.create_epic.assert_called_once_with(
        "Test Epic", "Test description", "test-project-id"
    )


def test_find_epics_success(epic_service, mock_repository):
    """Test successful epic retrieval."""
    # Setup mock
    mock_epics = [
        Epic(
            id="1",
            title="Epic 1",
            description="Desc 1",
            project_id="test-project-1",
            status="Draft",
        ),
        Epic(
            id="2",
            title="Epic 2",
            description="Desc 2",
            project_id="test-project-2",
            status="Ready",
        ),
    ]
    mock_repository.find_all_epics.return_value = mock_epics

    # Call service method
    result = epic_service.find_epics()

    # Verify result
    expected = [
        {
            "id": "1",
            "title": "Epic 1",
            "description": "Desc 1",
            "status": "Draft",
            "project_id": "test-project-1",
        },
        {
            "id": "2",
            "title": "Epic 2",
            "description": "Desc 2",
            "status": "Ready",
            "project_id": "test-project-2",
        },
    ]
    assert result == expected
    mock_repository.find_all_epics.assert_called_once()


def test_find_epics_empty(epic_service, mock_repository):
    """Test epic retrieval when no epics exist."""
    mock_repository.find_all_epics.return_value = []

    result = epic_service.find_epics()

    assert result == []
    mock_repository.find_all_epics.assert_called_once()


def test_find_epics_database_error(epic_service, mock_repository):
    """Test epic retrieval with database error."""
    mock_repository.find_all_epics.side_effect = SQLAlchemyError("Connection lost")

    with pytest.raises(
        DatabaseError,
        match="Database operation failed while retrieving epics: Connection lost",
    ):
        epic_service.find_epics()


def test_update_epic_status_success(epic_service, mock_repository):
    """Test successful epic status update."""
    # Setup mock
    mock_epic = Epic(
        id="test-id",
        title="Test Epic",
        description="Test description",
        project_id="test-project-id",
        status="Ready",
    )
    mock_repository.update_epic_status.return_value = mock_epic

    # Call service method
    result = epic_service.update_epic_status("test-id", "Ready")

    # Verify result
    expected = {
        "id": "test-id",
        "title": "Test Epic",
        "description": "Test description",
        "status": "Ready",
        "project_id": "test-project-id",
    }
    assert result == expected
    mock_repository.update_epic_status.assert_called_once_with("test-id", "Ready")


def test_update_epic_status_valid_statuses(epic_service, mock_repository):
    """Test epic status update with all valid status values."""
    valid_statuses = ["Draft", "Ready", "In Progress", "Done", "On Hold"]

    for status in valid_statuses:
        mock_epic = Epic(
            id="test-id",
            title="Test",
            description="Test",
            project_id="test-project-id",
            status=status,
        )
        mock_repository.update_epic_status.return_value = mock_epic

        result = epic_service.update_epic_status("test-id", status)

        assert result["status"] == status


def test_update_epic_status_empty_epic_id(epic_service):
    """Test epic status update with empty epic ID."""
    with pytest.raises(EpicNotFoundError, match="Epic ID cannot be empty"):
        epic_service.update_epic_status("", "Ready")

    with pytest.raises(EpicNotFoundError, match="Epic ID cannot be empty"):
        epic_service.update_epic_status("   ", "Ready")


def test_update_epic_status_empty_status(epic_service):
    """Test epic status update with empty status."""
    with pytest.raises(InvalidEpicStatusError, match="Epic status cannot be empty"):
        epic_service.update_epic_status("test-id", "")

    with pytest.raises(InvalidEpicStatusError, match="Epic status cannot be empty"):
        epic_service.update_epic_status("test-id", "   ")


def test_update_epic_status_invalid_status(epic_service):
    """Test epic status update with invalid status values."""
    invalid_statuses = [
        "InvalidStatus",
        "DRAFT",
        "draft",
        "Complete",
        "Finished",
        "123",
    ]

    for invalid_status in invalid_statuses:
        with pytest.raises(InvalidEpicStatusError, match="Epic status must be one of"):
            epic_service.update_epic_status("test-id", invalid_status)


def test_update_epic_status_not_found(epic_service, mock_repository):
    """Test epic status update when epic is not found."""
    mock_repository.update_epic_status.return_value = None

    with pytest.raises(
        EpicNotFoundError, match="Epic with ID 'nonexistent-id' not found"
    ):
        epic_service.update_epic_status("nonexistent-id", "Ready")


def test_update_epic_status_strips_whitespace(epic_service, mock_repository):
    """Test that epic status update strips whitespace from inputs."""
    mock_epic = Epic(
        id="test-id",
        title="Test",
        description="Test",
        project_id="test-project-id",
        status="Ready",
    )
    mock_repository.update_epic_status.return_value = mock_epic

    epic_service.update_epic_status("  test-id  ", "  Ready  ")

    mock_repository.update_epic_status.assert_called_once_with("test-id", "Ready")


def test_update_epic_status_database_error(epic_service, mock_repository):
    """Test epic status update with database error."""
    mock_repository.update_epic_status.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    with pytest.raises(
        DatabaseError, match="Database operation failed: Database connection failed"
    ):
        epic_service.update_epic_status("test-id", "Ready")


def test_update_epic_status_model_validation_error(epic_service, mock_repository):
    """Test epic status update with model validation error."""
    mock_repository.update_epic_status.side_effect = ValueError("Invalid status value")

    with pytest.raises(InvalidEpicStatusError, match="Invalid status value"):
        epic_service.update_epic_status("test-id", "Ready")
