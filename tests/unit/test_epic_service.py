"""
Unit tests for Epic service layer.
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.agile_mcp.services.epic_service import EpicService
from src.agile_mcp.services.exceptions import EpicValidationError, DatabaseError
from src.agile_mcp.models.epic import Epic


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
        status="Draft"
    )
    mock_repository.create_epic.return_value = mock_epic
    
    # Call service method
    result = epic_service.create_epic("Test Epic", "Test description")
    
    # Verify result
    expected = {
        "id": "test-id",
        "title": "Test Epic",
        "description": "Test description",
        "status": "Draft"
    }
    assert result == expected
    mock_repository.create_epic.assert_called_once_with("Test Epic", "Test description")


def test_create_epic_empty_title(epic_service):
    """Test epic creation with empty title."""
    with pytest.raises(EpicValidationError, match="Epic title cannot be empty"):
        epic_service.create_epic("", "Valid description")
    
    with pytest.raises(EpicValidationError, match="Epic title cannot be empty"):
        epic_service.create_epic("   ", "Valid description")


def test_create_epic_empty_description(epic_service):
    """Test epic creation with empty description."""
    with pytest.raises(EpicValidationError, match="Epic description cannot be empty"):
        epic_service.create_epic("Valid title", "")
    
    with pytest.raises(EpicValidationError, match="Epic description cannot be empty"):
        epic_service.create_epic("Valid title", "   ")


def test_create_epic_title_too_long(epic_service):
    """Test epic creation with title too long."""
    long_title = "x" * 201  # Exceeds 200 character limit
    
    with pytest.raises(EpicValidationError, match="Epic title cannot exceed 200 characters"):
        epic_service.create_epic(long_title, "Valid description")


def test_create_epic_description_too_long(epic_service):
    """Test epic creation with description too long."""
    long_description = "x" * 2001  # Exceeds 2000 character limit
    
    with pytest.raises(EpicValidationError, match="Epic description cannot exceed 2000 characters"):
        epic_service.create_epic("Valid title", long_description)


def test_create_epic_database_error(epic_service, mock_repository):
    """Test epic creation with database error."""
    # Setup mock to raise SQLAlchemy error
    mock_repository.create_epic.side_effect = SQLAlchemyError("Database connection failed")
    
    with pytest.raises(DatabaseError, match="Failed to create epic: Database connection failed"):
        epic_service.create_epic("Valid title", "Valid description")


def test_create_epic_strips_whitespace(epic_service, mock_repository):
    """Test that epic creation strips whitespace from inputs."""
    mock_epic = Epic(
        id="test-id",
        title="Test Epic",
        description="Test description",
        status="Draft"
    )
    mock_repository.create_epic.return_value = mock_epic
    
    epic_service.create_epic("  Test Epic  ", "  Test description  ")
    
    mock_repository.create_epic.assert_called_once_with("Test Epic", "Test description")


def test_find_epics_success(epic_service, mock_repository):
    """Test successful epic retrieval."""
    # Setup mock
    mock_epics = [
        Epic(id="1", title="Epic 1", description="Desc 1", status="Draft"),
        Epic(id="2", title="Epic 2", description="Desc 2", status="Ready"),
    ]
    mock_repository.find_all_epics.return_value = mock_epics
    
    # Call service method
    result = epic_service.find_epics()
    
    # Verify result
    expected = [
        {"id": "1", "title": "Epic 1", "description": "Desc 1", "status": "Draft"},
        {"id": "2", "title": "Epic 2", "description": "Desc 2", "status": "Ready"},
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
    
    with pytest.raises(DatabaseError, match="Failed to retrieve epics: Connection lost"):
        epic_service.find_epics()