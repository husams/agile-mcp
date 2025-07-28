"""
Unit tests for Epic API/Tool layer.
"""

from unittest.mock import Mock

import pytest

from src.agile_mcp.services.epic_service import EpicService
from src.agile_mcp.services.exceptions import (
    DatabaseError,
    EpicNotFoundError,
    InvalidEpicStatusError,
)


def test_epic_service_integration_update_status():
    """Test epic service layer with mocked repository for update status."""
    # Create mock repository
    mock_repository = Mock()
    service = EpicService(mock_repository)

    # Setup mock epic
    from src.agile_mcp.models.epic import Epic

    mock_epic = Epic(
        id="test-id", title="Test Epic", description="Test description", status="Ready"
    )
    mock_repository.update_epic_status.return_value = mock_epic

    # Test successful update
    result = service.update_epic_status("test-id", "Ready")

    expected = {
        "id": "test-id",
        "title": "Test Epic",
        "description": "Test description",
        "status": "Ready",
    }
    assert result == expected
    mock_repository.update_epic_status.assert_called_once_with("test-id", "Ready")


def test_epic_service_update_status_not_found():
    """Test epic service when epic is not found."""
    mock_repository = Mock()
    service = EpicService(mock_repository)

    # Setup mock to return None (epic not found)
    mock_repository.update_epic_status.return_value = None

    # Test that service raises appropriate exception
    with pytest.raises(EpicNotFoundError, match="Epic with ID 'nonexistent' not found"):
        service.update_epic_status("nonexistent", "Ready")


def test_epic_service_update_status_validation():
    """Test epic service status validation."""
    mock_repository = Mock()
    service = EpicService(mock_repository)

    # Test empty epic_id
    with pytest.raises(EpicNotFoundError, match="Epic ID cannot be empty"):
        service.update_epic_status("", "Ready")

    # Test empty status
    with pytest.raises(InvalidEpicStatusError, match="Epic status cannot be empty"):
        service.update_epic_status("test-id", "")

    # Test invalid status
    with pytest.raises(InvalidEpicStatusError, match="Epic status must be one of"):
        service.update_epic_status("test-id", "InvalidStatus")


def test_epic_service_update_status_valid_statuses():
    """Test epic service with all valid status values."""
    mock_repository = Mock()
    service = EpicService(mock_repository)

    valid_statuses = ["Draft", "Ready", "In Progress", "Done", "On Hold"]

    for status in valid_statuses:
        from src.agile_mcp.models.epic import Epic

        mock_epic = Epic(id="test-id", title="Test", description="Test", status=status)
        mock_repository.update_epic_status.return_value = mock_epic

        result = service.update_epic_status("test-id", status)
        assert result["status"] == status


def test_tool_registration_includes_update_epic_status():
    """Test that updateEpicStatus tool is registered."""
    from src.agile_mcp.api.epic_tools import register_epic_tools

    mock_mcp = Mock()

    register_epic_tools(mock_mcp)

    # Verify that updateEpicStatus tool was registered
    tool_calls = mock_mcp.tool.call_args_list
    tool_names = [call[0][0] for call in tool_calls]

    assert "backlog.updateEpicStatus" in tool_names
    assert "backlog.createEpic" in tool_names
    assert "backlog.findEpics" in tool_names


def test_service_layer_error_handling():
    """Test that service layer properly handles repository errors."""
    mock_repository = Mock()
    service = EpicService(mock_repository)

    # Test repository raising SQLAlchemy error
    from sqlalchemy.exc import SQLAlchemyError

    mock_repository.update_epic_status.side_effect = SQLAlchemyError("Database error")

    with pytest.raises(DatabaseError, match="Database operation failed"):
        service.update_epic_status("test-id", "Ready")

    # Test repository raising ValueError (model validation)
    mock_repository.update_epic_status.side_effect = ValueError("Invalid value")

    with pytest.raises(InvalidEpicStatusError, match="Invalid value"):
        service.update_epic_status("test-id", "Ready")
