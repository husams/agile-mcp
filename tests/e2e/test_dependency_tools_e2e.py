"""
End-to-end tests for Dependency tools via MCP JSON-RPC over stdio transport.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def mcp_server_process(isolated_test_database):
    """Start MCP server as subprocess with isolated database."""
    # Get the path to the run_server.py file
    run_server_path = Path(__file__).parent.parent.parent / "run_server.py"

    # Set up environment with isolated test database
    env = os.environ.copy()
    env["TEST_DATABASE_URL"] = f"sqlite:///{isolated_test_database}"

    # Start server process with isolated database
    process = subprocess.Popen(
        [sys.executable, str(run_server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    yield process

    # Cleanup
    process.terminate()
    process.wait()


def send_jsonrpc_request(process, method, params=None):
    """Send JSON-RPC request to MCP server and return response."""
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}

    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()

    # Read response
    response_line = process.stdout.readline()
    if not response_line:
        return None

    try:
        response = json.loads(response_line.strip())
        return response
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "raw": response_line}


def initialize_server(process):
    """Initialize the MCP server."""
    # Initialize server first
    send_jsonrpc_request(
        process,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    )

    # Send initialized notification (no response expected)
    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()


def create_test_epic(process):
    """Create a test epic for dependency testing."""
    response = send_jsonrpc_request(
        process,
        "tools/call",
        {
            "name": "backlog.createEpic",
            "arguments": {
                "title": "Dependency Test Epic",
                "description": "Epic for testing story dependencies",
            },
        },
    )

    assert "error" not in response
    assert response.get("result", {}).get("content", [{}])[0].get("type") == "text"
    result_text = response["result"]["content"][0]["text"]
    result_data = json.loads(result_text)
    return result_data["id"]


def create_test_story(process, epic_id, title):
    """Create a test story for dependency testing."""
    response = send_jsonrpc_request(
        process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": title,
                "description": f"As a tester, I want to test {title.lower()}",
                "acceptance_criteria": [f"Should test {title.lower()} functionality"],
            },
        },
    )

    assert "error" not in response
    assert response.get("result", {}).get("content", [{}])[0].get("type") == "text"
    result_text = response["result"]["content"][0]["text"]
    result_data = json.loads(result_text)
    return result_data["id"]


class TestDependencyToolsE2E:
    """End-to-end tests for dependency management tools."""

    def test_backlog_add_dependency_e2e_success(self, mcp_server_process):
        """Test backlog.addDependency tool via MCP JSON-RPC - success case."""
        # Initialize server
        initialize_server(mcp_server_process)

        # First create test epic and stories
        epic_id = create_test_epic(mcp_server_process)
        story_1_id = create_test_story(mcp_server_process, epic_id, "Test Story 1")
        story_2_id = create_test_story(mcp_server_process, epic_id, "Test Story 2")

        # Test dependency addition
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_1_id,
                    "depends_on_story_id": story_2_id,
                },
            },
        )

        # Verify JSON-RPC 2.0 compliant response
        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 1
        assert "error" not in response

        # Verify response structure
        assert "result" in response
        result = response["result"]
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Parse and verify the dependency creation result
        result_text = result["content"][0]["text"]
        result_data = json.loads(result_text)

        assert result_data["status"] == "success"
        assert result_data["story_id"] == story_1_id
        assert result_data["depends_on_story_id"] == story_2_id
        assert "Dependency added" in result_data["message"]

    def test_backlog_add_dependency_e2e_circular_prevention(self, mcp_server_process):
        """Test circular dependency prevention in complete system."""
        # Initialize server
        initialize_server(mcp_server_process)

        # Create test epic and stories
        epic_id = create_test_epic(mcp_server_process)
        story_1_id = create_test_story(mcp_server_process, epic_id, "Story A")
        story_2_id = create_test_story(mcp_server_process, epic_id, "Story B")
        story_3_id = create_test_story(mcp_server_process, epic_id, "Story C")

        # Create dependency chain: A -> B -> C
        send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_1_id,
                    "depends_on_story_id": story_2_id,
                },
            },
        )

        send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_2_id,
                    "depends_on_story_id": story_3_id,
                },
            },
        )

        # Try to create circular dependency: C -> A (would create A -> B -> C -> A cycle)
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_3_id,
                    "depends_on_story_id": story_1_id,
                },
            },
        )

        # Verify error response
        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 1

        # Check for error in result format
        result = response.get("result", {})
        assert result.get("isError") is True
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"

        error_text = result["content"][0]["text"].lower()
        assert "circular dependency" in error_text

    def test_backlog_add_dependency_e2e_story_not_found(self, mcp_server_process):
        """Test story not found error handling."""
        # Initialize server
        initialize_server(mcp_server_process)

        # Create test epic and one story
        epic_id = create_test_epic(mcp_server_process)
        story_1_id = create_test_story(mcp_server_process, epic_id, "Existing Story")

        # Try to create dependency with non-existent story
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_1_id,
                    "depends_on_story_id": "nonexistent-story-id",
                },
            },
        )

        # Verify error response
        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 1

        # Check for error in result format
        result = response.get("result", {})
        assert result.get("isError") is True
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"

        error_text = result["content"][0]["text"].lower()
        assert "story not found" in error_text

    def test_backlog_add_dependency_e2e_duplicate_dependency(self, mcp_server_process):
        """Test duplicate dependency error handling."""
        # Initialize server
        initialize_server(mcp_server_process)

        # Create test epic and stories
        epic_id = create_test_epic(mcp_server_process)
        story_1_id = create_test_story(mcp_server_process, epic_id, "Story 1")
        story_2_id = create_test_story(mcp_server_process, epic_id, "Story 2")

        # Add dependency first time (should succeed)
        response1 = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_1_id,
                    "depends_on_story_id": story_2_id,
                },
            },
        )
        assert "error" not in response1

        # Try to add same dependency again (should fail)
        response2 = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_1_id,
                    "depends_on_story_id": story_2_id,
                },
            },
        )

        # Verify error response
        assert response2.get("jsonrpc") == "2.0"
        assert response2.get("id") == 1

        # Check for error in result format
        result = response2.get("result", {})
        assert result.get("isError") is True
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"

        error_text = result["content"][0]["text"].lower()
        assert "duplicate dependency" in error_text or "already exists" in error_text

    def test_backlog_add_dependency_e2e_self_dependency_prevention(
        self, mcp_server_process
    ):
        """Test prevention of self-dependency."""
        # Initialize server
        initialize_server(mcp_server_process)

        # Create test epic and story
        epic_id = create_test_epic(mcp_server_process)
        story_id = create_test_story(
            mcp_server_process, epic_id, "Self Dependent Story"
        )

        # Try to create self-dependency
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {"story_id": story_id, "depends_on_story_id": story_id},
            },
        )

        # Verify error response
        assert response.get("jsonrpc") == "2.0"
        assert response.get("id") == 1

        # Check for error in result format
        result = response.get("result", {})
        assert result.get("isError") is True
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"

        error_text = result["content"][0]["text"].lower()
        assert (
            "cannot depend on itself" in error_text or "validation error" in error_text
        )

    def test_backlog_add_dependency_e2e_validation_errors(self, mcp_server_process):
        """Test input validation error handling."""
        # Initialize server
        initialize_server(mcp_server_process)

        # Test empty story_id
        response1 = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {"story_id": "", "depends_on_story_id": "some-story-id"},
            },
        )

        # Check for error in result format
        result1 = response1.get("result", {})
        assert result1.get("isError") is True
        assert "content" in result1
        assert len(result1["content"]) > 0
        error_text1 = result1["content"][0]["text"].lower()
        assert "validation error" in error_text1

        # Test empty depends_on_story_id
        response2 = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {"story_id": "some-story-id", "depends_on_story_id": ""},
            },
        )

        # Check for error in result format
        result2 = response2.get("result", {})
        assert result2.get("isError") is True
        assert "content" in result2
        assert len(result2["content"]) > 0
        error_text2 = result2["content"][0]["text"].lower()
        assert "validation error" in error_text2

    def test_backlog_add_dependency_e2e_complex_dependency_graph(
        self, mcp_server_process
    ):
        """Test complex dependency graph creation and validation."""
        # Initialize server
        initialize_server(mcp_server_process)

        # Create test epic and multiple stories
        epic_id = create_test_epic(mcp_server_process)
        story_ids = []
        for i in range(5):
            story_id = create_test_story(mcp_server_process, epic_id, f"Story {i+1}")
            story_ids.append(story_id)

        # Create complex dependency graph:
        # Story 1 -> Story 2, Story 3
        # Story 2 -> Story 4
        # Story 3 -> Story 4
        # Story 4 -> Story 5
        dependencies = [
            (story_ids[0], story_ids[1]),  # 1 -> 2
            (story_ids[0], story_ids[2]),  # 1 -> 3
            (story_ids[1], story_ids[3]),  # 2 -> 4
            (story_ids[2], story_ids[3]),  # 3 -> 4
            (story_ids[3], story_ids[4]),  # 4 -> 5
        ]

        # Add all valid dependencies
        for story_id, depends_on_id in dependencies:
            response = send_jsonrpc_request(
                mcp_server_process,
                "tools/call",
                {
                    "name": "backlog.addDependency",
                    "arguments": {
                        "story_id": story_id,
                        "depends_on_story_id": depends_on_id,
                    },
                },
            )
            assert (
                "error" not in response
            ), f"Failed to add dependency {story_id} -> {depends_on_id}"

        # Test circular dependency prevention: try Story 5 -> Story 1 (would create cycle)
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_ids[4],  # Story 5
                    "depends_on_story_id": story_ids[0],  # Story 1
                },
            },
        )

        # Should be prevented due to circular dependency
        result = response.get("result", {})
        assert result.get("isError") is True
        assert "content" in result
        assert len(result["content"]) > 0
        error_text = result["content"][0]["text"].lower()
        assert "circular dependency" in error_text

    def test_backlog_add_dependency_e2e_integration_with_existing_tools(
        self, mcp_server_process
    ):
        """Test integration with existing story management tools."""
        # Initialize server
        initialize_server(mcp_server_process)

        # Create test epic and stories using existing tools
        epic_id = create_test_epic(mcp_server_process)
        story_1_id = create_test_story(mcp_server_process, epic_id, "Feature Story")
        story_2_id = create_test_story(mcp_server_process, epic_id, "Foundation Story")

        # Add dependency
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.addDependency",
                "arguments": {
                    "story_id": story_1_id,
                    "depends_on_story_id": story_2_id,
                },
            },
        )

        assert "error" not in response
        result_text = response["result"]["content"][0]["text"]
        result_data = json.loads(result_text)
        assert result_data["status"] == "success"

        # Verify stories still exist and can be retrieved
        story_1_response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {"name": "backlog.getStory", "arguments": {"story_id": story_1_id}},
        )
        assert "error" not in story_1_response
        result = story_1_response.get("result", {})
        assert result.get("isError") is not True

        story_2_response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {"name": "backlog.getStory", "arguments": {"story_id": story_2_id}},
        )
        assert "error" not in story_2_response
        result = story_2_response.get("result", {})
        assert result.get("isError") is not True
