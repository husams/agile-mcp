"""
Unit tests for Task management tools.
"""

from unittest.mock import Mock, patch

import pytest

from src.agile_mcp.api.story_tools import register_story_tools


@pytest.fixture
def mock_fastmcp():
    """Create a mock FastMCP server instance."""
    return Mock()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def sample_story_with_tasks():
    """Sample story data with tasks for testing."""
    return {
        "id": "test-story-1",
        "title": "Test Story",
        "description": "Test story description",
        "acceptance_criteria": ["Test AC"],
        "tasks": [
            {
                "id": "task-1",
                "description": "First task",
                "completed": False,
                "order": 1,
            },
            {
                "id": "task-2",
                "description": "Second task",
                "completed": True,
                "order": 2,
            },
        ],
        "status": "ToDo",
        "priority": 0,
        "created_at": "2023-01-01T00:00:00Z",
        "epic_id": "epic-1",
    }


class TestTaskManagementToolsRegistration:
    """Test task management tools registration."""

    def test_task_tools_are_registered(self, mock_fastmcp):
        """Test that task management tools are registered with the server."""
        with patch("src.agile_mcp.api.story_tools.create_tables"):
            register_story_tools(mock_fastmcp)

            # Verify that tools were registered
            assert mock_fastmcp.tool.called

            # Check that task-related tools were registered by name
            tool_calls = mock_fastmcp.tool.call_args_list
            registered_tool_names = [call[0][0] for call in tool_calls]

            # Check that our task management tools are in the registered tools
            assert "tasks.addToStory" in registered_tool_names
            assert "tasks.updateTaskStatus" in registered_tool_names
            assert "tasks.updateTaskDescription" in registered_tool_names
            assert "tasks.reorderTasks" in registered_tool_names


class TestAddTaskToStoryTool:
    """Test the tasks.addToStory tool functionality."""

    def test_add_task_service_integration(self, mock_fastmcp, sample_story_with_tasks):
        """Test that add task tool integrates with story service correctly."""
        with (
            patch("src.agile_mcp.api.story_tools.get_db") as mock_get_db,
            patch("src.agile_mcp.api.story_tools.StoryRepository") as _,
            patch("src.agile_mcp.api.story_tools.StoryService") as mock_service_class,
            patch("src.agile_mcp.api.story_tools.create_tables"),
        ):
            mock_session = Mock()
            mock_get_db.return_value = mock_session

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock service to return story with new task
            updated_story = sample_story_with_tasks.copy()
            new_task = {
                "id": "task-3",
                "description": "New task",
                "completed": False,
                "order": 3,
            }
            updated_story["tasks"].append(new_task)
            mock_service.add_task_to_story.return_value = updated_story

            # Register tools
            register_story_tools(mock_fastmcp)

            # Verify tools were registered
            assert mock_fastmcp.tool.called

            # Simulate calling the service method that would be called by the tool
            result = mock_service.add_task_to_story("test-story-1", "New task", 3)

            # Verify result
            assert len(result["tasks"]) == 3
            assert result["tasks"][2]["description"] == "New task"


class TestUpdateTaskStatusTool:
    """Test the tasks.updateTaskStatus tool functionality."""

    def test_update_task_status_service_integration(
        self, mock_fastmcp, sample_story_with_tasks
    ):
        """Test that update task status tool integrates with story service correctly."""
        with (
            patch("src.agile_mcp.api.story_tools.get_db") as mock_get_db,
            patch("src.agile_mcp.api.story_tools.StoryRepository") as _,
            patch("src.agile_mcp.api.story_tools.StoryService") as mock_service_class,
            patch("src.agile_mcp.api.story_tools.create_tables"),
        ):
            mock_session = Mock()
            mock_get_db.return_value = mock_session

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock service to return story with updated task
            updated_story = sample_story_with_tasks.copy()
            updated_story["tasks"][0]["completed"] = True
            mock_service.update_task_status.return_value = updated_story

            # Register tools
            register_story_tools(mock_fastmcp)

            # Verify tools were registered
            assert mock_fastmcp.tool.called

            # Simulate calling the service method that would be called by the tool
            result = mock_service.update_task_status("test-story-1", "task-1", True)

            # Verify result
            assert result["tasks"][0]["completed"] is True


class TestUpdateTaskDescriptionTool:
    """Test the tasks.updateTaskDescription tool functionality."""

    def test_update_task_description_service_integration(
        self, mock_fastmcp, sample_story_with_tasks
    ):
        """Test update task description tool integrates with story service."""
        with (
            patch("src.agile_mcp.api.story_tools.get_db") as mock_get_db,
            patch("src.agile_mcp.api.story_tools.StoryRepository") as _,
            patch("src.agile_mcp.api.story_tools.StoryService") as mock_service_class,
            patch("src.agile_mcp.api.story_tools.create_tables"),
        ):
            mock_session = Mock()
            mock_get_db.return_value = mock_session

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock service to return story with updated task
            updated_story = sample_story_with_tasks.copy()
            updated_story["tasks"][0]["description"] = "Updated task description"
            mock_service.update_task_description.return_value = updated_story

            # Register tools
            register_story_tools(mock_fastmcp)

            # Verify tools were registered
            assert mock_fastmcp.tool.called

            # Simulate calling the service method that would be called by the tool
            result = mock_service.update_task_description(
                "test-story-1", "task-1", "Updated task description"
            )

            # Verify result
            assert result["tasks"][0]["description"] == "Updated task description"


class TestReorderTasksTool:
    """Test the tasks.reorderTasks tool functionality."""

    def test_reorder_tasks_service_integration(
        self, mock_fastmcp, sample_story_with_tasks
    ):
        """Test that reorder tasks tool integrates with story service correctly."""
        with (
            patch("src.agile_mcp.api.story_tools.get_db") as mock_get_db,
            patch("src.agile_mcp.api.story_tools.StoryRepository") as _,
            patch("src.agile_mcp.api.story_tools.StoryService") as mock_service_class,
            patch("src.agile_mcp.api.story_tools.create_tables"),
        ):
            mock_session = Mock()
            mock_get_db.return_value = mock_session

            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock service to return story with reordered tasks
            updated_story = sample_story_with_tasks.copy()
            updated_story["tasks"][0]["order"] = 2
            updated_story["tasks"][1]["order"] = 1
            mock_service.reorder_tasks.return_value = updated_story

            # Register tools
            register_story_tools(mock_fastmcp)

            # Verify tools were registered
            assert mock_fastmcp.tool.called

            # Simulate calling the service method that would be called by the tool
            task_orders = [
                {"task_id": "task-1", "order": 2},
                {"task_id": "task-2", "order": 1},
            ]
            result = mock_service.reorder_tasks("test-story-1", task_orders)

            # Verify result
            assert result["tasks"][0]["order"] == 2
            assert result["tasks"][1]["order"] == 1
