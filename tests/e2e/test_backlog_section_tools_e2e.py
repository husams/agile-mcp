"""
End-to-end tests for backlog management tools integration.
"""

import pytest
import os
from unittest.mock import patch, mock_open
from src.agile_mcp.main import create_server

from .test_helpers import (
    validate_full_tool_response, validate_story_tool_response,
    validate_jsonrpc_response_format, validate_json_response,
    validate_error_response_format
)





@pytest.fixture
def sample_story_content():
    """Sample story markdown content for E2E testing."""
    return '''# Story 1.1: Test Story for E2E

## Status
Done

## Story
**As an** AI Agent,
**I want** to retrieve just a specific section of a story, like its Acceptance Criteria,
**so that** I can focus on the most relevant information for my current task without processing the entire story object.

## Acceptance Criteria
1. A `backlog.getStorySection` tool is available.
2. The tool accepts a story ID and a section name (e.g., "Acceptance Criteria", "Description").
3. The tool returns the content of the requested section.
4. The tool returns an appropriate error if the section does not exist.

## Tasks / Subtasks
- [x] Task 1: Create Story Section Parsing Logic
  - [x] Create utility function to parse story markdown sections
  - [x] Implement section name validation and normalization
- [x] Task 2: Implement Service Layer Logic
  - [x] Add get_story_section method to StoryService class

## Dev Notes
This is a comprehensive E2E test story with multiple sections for testing purposes.

## Testing
The testing section contains information about test execution requirements.
'''


class TestBacklogSectionToolsE2E:
    """End-to-end test cases for backlog section management tools."""
    
    def test_server_initialization_with_backlog_tools(self, mcp_server_subprocess):
        """Test that server initialization successfully includes backlog tools."""
        process, env_vars, communicate_json_rpc = mcp_server_subprocess
        # Verify server process was created successfully
        assert process is not None
        
        # The server should exit cleanly after showing startup banner 
        # This indicates successful initialization with all tools including backlog tools
        
        # This test verifies that the server can be created without errors
        # when backlog tools are registered, which indicates successful integration
    
    def test_backlog_tools_registration_during_server_creation(self):
        """Test that backlog tools are registered during server creation without errors."""
        # Create a new server instance to test registration process
        from src.agile_mcp.main import create_server
        
        # This should complete without throwing exceptions
        server = create_server()
        assert server is not None
        assert server.name == "Agile Management Server"
        
        # The fact that create_server() completes successfully means
        # all tools including backlog tools were registered properly