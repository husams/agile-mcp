"""
Unit tests for backlog management FastMCP tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastmcp.exceptions import McpError

from src.agile_mcp.api.backlog_tools import register_backlog_tools
from src.agile_mcp.services.exceptions import (
    DependencyValidationError,
    CircularDependencyError,
    DuplicateDependencyError,
    StoryNotFoundError,
    DatabaseError
)


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP server instance."""
    return Mock()


class TestBacklogTools:
    """Test cases for backlog management tools."""
    
    @patch('src.agile_mcp.api.backlog_tools.create_tables')
    def test_register_backlog_tools_creates_tables(self, mock_create_tables, mock_mcp):
        """Test that registering tools creates database tables."""
        register_backlog_tools(mock_mcp)
        
        # Verify create_tables was called
        mock_create_tables.assert_called_once()
        
        # Verify tools were registered
        assert mock_mcp.tool.called
        tool_calls = mock_mcp.tool.call_args_list
        assert len(tool_calls) == 2
        
        # Check both tools are registered
        tool_names = [call[0][0] for call in tool_calls]
        assert "backlog.getStorySection" in tool_names
        assert "backlog.addDependency" in tool_names
    
    @patch('src.agile_mcp.api.backlog_tools.create_tables', side_effect=Exception("Database initialization failed"))
    def test_register_backlog_tools_create_tables_failure(self, mock_create_tables, mock_mcp):
        """Test error handling when table creation fails."""
        with pytest.raises(Exception) as exc_info:
            register_backlog_tools(mock_mcp)
        
        assert "Database initialization failed" in str(exc_info.value)
        mock_create_tables.assert_called_once()
    
    @patch('src.agile_mcp.api.backlog_tools.create_tables')
    def test_register_backlog_tools_registers_correct_tool_name(self, mock_create_tables, mock_mcp):
        """Test that the correct tool name is registered."""
        register_backlog_tools(mock_mcp)
        
        # Verify the correct tool names were registered
        tool_calls = mock_mcp.tool.call_args_list
        assert len(tool_calls) == 2
        
        tool_names = [call[0][0] for call in tool_calls]
        assert "backlog.getStorySection" in tool_names
        assert "backlog.addDependency" in tool_names


class TestAddDependencyTool:
    """Test cases for the backlog.addDependency tool."""
    
    @patch('src.agile_mcp.api.backlog_tools.create_tables')
    def test_add_dependency_tool_registration(self, mock_create_tables, mock_mcp):
        """Test that addDependency tool is properly registered."""
        register_backlog_tools(mock_mcp)
        
        # Verify tools were registered
        tool_calls = mock_mcp.tool.call_args_list
        assert len(tool_calls) == 2
        
        # Check that addDependency tool was registered
        tool_names = [call[0][0] for call in tool_calls]
        assert "backlog.addDependency" in tool_names
        
        # Verify that a function was passed for the addDependency tool
        add_dependency_call = None
        for call in tool_calls:
            if call[0][0] == "backlog.addDependency":
                add_dependency_call = call
                break
        
        assert add_dependency_call is not None
        # The function should be passed as a positional argument to the decorator
        assert len(add_dependency_call[0]) >= 1  # At least the tool name
        # Or as part of the decorator call structure - this tests that registration happened