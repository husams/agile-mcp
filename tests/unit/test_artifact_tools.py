"""
Unit tests for Artifact tools/API layer.
"""

from unittest.mock import Mock, patch

import pytest
from fastmcp import FastMCP

from src.agile_mcp.api.artifact_tools import register_artifact_tools


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    return Mock(spec=FastMCP)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def mock_artifact_service():
    """Create a mock artifact service."""
    return Mock()


@pytest.fixture
def mock_artifact_repository():
    """Create a mock artifact repository."""
    return Mock()


class TestArtifactTools:
    """Test artifact tool registration and functionality."""

    def test_register_artifact_tools_creates_database_tables(self, mock_mcp):
        """Test that register_artifact_tools creates database tables."""
        with patch(
            "src.agile_mcp.api.artifact_tools.create_tables"
        ) as mock_create_tables:
            register_artifact_tools(mock_mcp)
            mock_create_tables.assert_called_once()

    def test_register_artifact_tools_handles_database_creation_failure(self, mock_mcp):
        """Test that register_artifact_tools handles database creation failures."""
        with patch(
            "src.agile_mcp.api.artifact_tools.create_tables"
        ) as mock_create_tables:
            mock_create_tables.side_effect = Exception("Database creation failed")

            with pytest.raises(Exception, match="Database creation failed"):
                register_artifact_tools(mock_mcp)

    def test_link_artifact_to_story_tool_registration(self, mock_mcp):
        """Test successful artifact linking tool registration."""
        with patch("src.agile_mcp.api.artifact_tools.create_tables"):
            register_artifact_tools(mock_mcp)

            # Verify the tool was registered
            assert mock_mcp.tool.called

            # Check that artifacts.linkToStory was registered
            tool_names = []
            for call in mock_mcp.tool.call_args_list:
                if call[0]:  # positional arguments
                    tool_names.append(call[0][0])

            assert "artifacts.linkToStory" in tool_names

    def test_list_artifacts_for_story_tool_registration(self, mock_mcp):
        """Test successful artifacts listing tool registration."""
        with patch("src.agile_mcp.api.artifact_tools.create_tables"):
            register_artifact_tools(mock_mcp)

            # Verify the tool was registered
            assert mock_mcp.tool.called

            # Check that artifacts.listForStory was registered
            tool_names = []
            for call in mock_mcp.tool.call_args_list:
                if call[0]:  # positional arguments
                    tool_names.append(call[0][0])

            assert "artifacts.listForStory" in tool_names

    def test_tools_registration(self, mock_mcp):
        """Test that both tools are registered correctly."""
        with patch(
            "src.agile_mcp.api.artifact_tools.create_tables"
        ) as mock_create_tables:
            register_artifact_tools(mock_mcp)

            # Verify both tools were registered
            tool_names = []
            for call in mock_mcp.tool.call_args_list:
                if call[0]:  # positional arguments
                    tool_names.append(call[0][0])

            assert "artifacts.linkToStory" in tool_names
            assert "artifacts.listForStory" in tool_names

            # Verify database tables creation was called
            mock_create_tables.assert_called_once()
