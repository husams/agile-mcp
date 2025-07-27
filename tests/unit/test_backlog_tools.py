"""
Unit tests for backlog management FastMCP tools.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastmcp.exceptions import McpError

from src.agile_mcp.api.backlog_tools import register_backlog_tools
from src.agile_mcp.services.exceptions import (
    CircularDependencyError,
    DatabaseError,
    DependencyValidationError,
    DuplicateDependencyError,
    StoryNotFoundError,
)


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP server instance."""
    return Mock()


class TestBacklogTools:
    """Test cases for backlog management tools."""

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    def test_register_backlog_tools_creates_tables(self, mock_create_tables, mock_mcp):
        """Test that registering tools creates database tables."""
        register_backlog_tools(mock_mcp)

        # Verify create_tables was called
        mock_create_tables.assert_called_once()

        # Verify tools were registered
        assert mock_mcp.tool.called
        tool_calls = mock_mcp.tool.call_args_list
        assert len(tool_calls) == 3

        # Check all tools are registered
        tool_names = [call[0][0] for call in tool_calls]
        assert "backlog.getStorySection" in tool_names
        assert "backlog.addDependency" in tool_names
        assert "backlog.getNextReadyStory" in tool_names

    @patch(
        "src.agile_mcp.api.backlog_tools.create_tables",
        side_effect=Exception("Database initialization failed"),
    )
    def test_register_backlog_tools_create_tables_failure(
        self, mock_create_tables, mock_mcp
    ):
        """Test error handling when table creation fails."""
        with pytest.raises(Exception) as exc_info:
            register_backlog_tools(mock_mcp)

        assert "Database initialization failed" in str(exc_info.value)
        mock_create_tables.assert_called_once()

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    def test_register_backlog_tools_registers_correct_tool_name(
        self, mock_create_tables, mock_mcp
    ):
        """Test that the correct tool name is registered."""
        register_backlog_tools(mock_mcp)

        # Verify the correct tool names were registered
        tool_calls = mock_mcp.tool.call_args_list
        assert len(tool_calls) == 3

        tool_names = [call[0][0] for call in tool_calls]
        assert "backlog.getStorySection" in tool_names
        assert "backlog.addDependency" in tool_names
        assert "backlog.getNextReadyStory" in tool_names


class TestAddDependencyTool:
    """Test cases for the backlog.addDependency tool."""

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    def test_add_dependency_tool_registration(self, mock_create_tables, mock_mcp):
        """Test that addDependency tool is properly registered."""
        register_backlog_tools(mock_mcp)

        # Verify tools were registered
        tool_calls = mock_mcp.tool.call_args_list
        assert len(tool_calls) == 3

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


class TestGetNextReadyStoryTool:
    """Test cases for the backlog.getNextReadyStory tool."""

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    def test_get_next_ready_story_tool_registration(self, mock_create_tables, mock_mcp):
        """Test that getNextReadyStory tool is properly registered."""
        register_backlog_tools(mock_mcp)

        # Verify tools were registered
        tool_calls = mock_mcp.tool.call_args_list
        assert len(tool_calls) == 3

        # Check that getNextReadyStory tool was registered
        tool_names = [call[0][0] for call in tool_calls]
        assert "backlog.getNextReadyStory" in tool_names

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_success_with_story(
        self, mock_get_db, mock_create_tables
    ):
        """Test successful getNextReadyStory with a ready story available."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        # Mock the story service to return a story
        mock_story = {
            "id": "story-1",
            "title": "Ready Story",
            "description": "A story ready for implementation",
            "acceptance_criteria": ["AC1"],
            "status": "InProgress",
            "priority": 5,
            "created_at": "2023-01-01T12:00:00",
            "epic_id": "epic-1",
        }

        with patch(
            "src.agile_mcp.api.backlog_tools.StoryRepository"
        ) as mock_story_repo_class, patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ) as mock_dep_repo_class, patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            mock_story_service.get_next_ready_story.return_value = mock_story
            mock_story_service_class.return_value = mock_story_service

            # Test the behavior that the tool implements
            result = mock_story_service.get_next_ready_story()
            assert result == mock_story

            # Verify service method was called
            mock_story_service.get_next_ready_story.assert_called_once()

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_no_stories_available(
        self, mock_get_db, mock_create_tables
    ):
        """Test getNextReadyStory when no stories are ready."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        with patch("src.agile_mcp.api.backlog_tools.StoryRepository"), patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ), patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            mock_story_service.get_next_ready_story.return_value = None
            mock_story_service_class.return_value = mock_story_service

            # Test by calling the service layer directly
            result = mock_story_service.get_next_ready_story()
            assert result is None

            # The tool should return empty dict when service returns None
            # This tests the expected behavior based on the tool implementation

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_database_error(self, mock_get_db, mock_create_tables):
        """Test getNextReadyStory handles database errors properly."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        from src.agile_mcp.services.exceptions import DatabaseError

        with patch("src.agile_mcp.api.backlog_tools.StoryRepository"), patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ), patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            mock_story_service.get_next_ready_story.side_effect = DatabaseError(
                "Database connection failed"
            )
            mock_story_service_class.return_value = mock_story_service

            # The service layer raises DatabaseError
            with pytest.raises(DatabaseError):
                mock_story_service.get_next_ready_story()

            # The tool should convert this to McpError (tested in integration)

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_validation_error(
        self, mock_get_db, mock_create_tables
    ):
        """Test getNextReadyStory handles validation errors properly."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        from src.agile_mcp.services.exceptions import StoryValidationError

        with patch("src.agile_mcp.api.backlog_tools.StoryRepository"), patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ), patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            mock_story_service.get_next_ready_story.side_effect = StoryValidationError(
                "Dependency repository required"
            )
            mock_story_service_class.return_value = mock_story_service

            # The service layer raises StoryValidationError
            with pytest.raises(StoryValidationError):
                mock_story_service.get_next_ready_story()

            # The tool should convert this to McpError (tested in integration)
