"""
Unit tests for Comment tools.
"""

from unittest.mock import Mock, patch

import pytest

from src.agile_mcp.api.comment_tools import register_comment_tools


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    return Mock()


def test_register_comment_tools(mock_mcp):
    """Test that comment tools are registered properly."""
    with patch("src.agile_mcp.api.comment_tools.create_tables"):
        register_comment_tools(mock_mcp)

    # Verify that tools were registered
    assert mock_mcp.tool.call_count >= 4  # At least 4 tools should be registered

    # Get all registered tool names
    registered_tools = []
    for call_args in mock_mcp.tool.call_args_list:
        if len(call_args[0]) > 0:
            registered_tools.append(call_args[0][0])

    # Verify expected tools are registered
    expected_tools = [
        "story.addComment",
        "story.getComments",
        "story.updateComment",
        "story.deleteComment",
    ]

    for tool in expected_tools:
        assert tool in registered_tools


@patch("src.agile_mcp.api.comment_tools.create_tables")
def test_register_comment_tools_database_creation(mock_create_tables, mock_mcp):
    """Test that database tables are created during tool registration."""
    register_comment_tools(mock_mcp)

    # Verify create_tables was called
    mock_create_tables.assert_called_once()


@patch("src.agile_mcp.api.comment_tools.create_tables")
def test_register_comment_tools_database_error_handling(mock_create_tables, mock_mcp):
    """Test error handling during database table creation."""
    mock_create_tables.side_effect = Exception("Database connection failed")

    # Should raise the exception
    with pytest.raises(Exception, match="Database connection failed"):
        register_comment_tools(mock_mcp)
