"""
End-to-end tests for Story tools via MCP JSON-RPC over stdio transport.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from .test_helpers import (
    validate_json_response,
    validate_jsonrpc_response_format,
    validate_story_tool_response,
)


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
    """Send JSON-RPC request to MCP server and return validated response."""
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}

    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()

    # Read response
    response_line = process.stdout.readline()
    if not response_line:
        stderr_output = process.stderr.read()
        raise RuntimeError(f"No response from server. Stderr: {stderr_output}")

    # Validate JSON parsing
    response_json = validate_json_response(response_line.strip())

    # Validate JSON-RPC response format
    validated_response = validate_jsonrpc_response_format(response_json)

    return validated_response


def initialize_server(process):
    """Initialize the MCP server for testing."""
    # Send initialize request
    init_response = send_jsonrpc_request(
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

    return init_response


def create_test_epic(process):
    """Create a test epic for story creation tests."""
    response = send_jsonrpc_request(
        process,
        "tools/call",
        {
            "name": "backlog.createEpic",
            "arguments": {
                "title": "Test Epic for Stories",
                "description": "Epic created for story testing purposes",
            },
        },
    )

    assert "result" in response
    assert "content" in response["result"]
    epic_data = response["result"]["content"][0]["text"]
    epic = json.loads(epic_data)

    return epic["id"]


def test_story_server_initialization_includes_story_tools(mcp_server_process):
    """Test that MCP server initialization includes story management tools."""
    init_response = initialize_server(mcp_server_process)

    # Verify response structure
    assert "result" in init_response
    assert "capabilities" in init_response["result"]
    assert "tools" in init_response["result"]["capabilities"]
    assert init_response["result"]["serverInfo"]["name"] == "Agile Management Server"

    # Verify the server initialized correctly and is advertising tools
    assert "listChanged" in init_response["result"]["capabilities"]["tools"]
    assert init_response["result"]["capabilities"]["tools"]["listChanged"] is True


def test_create_story_tool_success(mcp_server_process):
    """Test successful story creation via MCP tool."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Call backlog.createStory tool
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Test Story",
                "description": "As a user, I want to test story creation via E2E tests",
                "acceptance_criteria": [
                    "Story should be created successfully",
                    "Story should have default ToDo status",
                    "Story should be associated with the epic",
                ],
            },
        },
    )

    # Verify response structure
    assert "result" in response
    assert "content" in response["result"]
    assert len(response["result"]["content"]) == 1
    assert response["result"]["content"][0]["type"] == "text"

    # Parse and validate story data using comprehensive validation helpers
    story_data = response["result"]["content"][0]["text"]

    # Apply full validation chain: JSON parsing, tool format, schema validation
    validated_story = validate_story_tool_response(story_data)

    # Production data validation with enhanced assertions
    assert validated_story.title == "Test Story"
    assert (
        validated_story.description
        == "As a user, I want to test story creation via E2E tests"
    )
    assert validated_story.acceptance_criteria == [
        "Story should be created successfully",
        "Story should have default ToDo status",
        "Story should be associated with the epic",
    ]
    assert validated_story.epic_id == epic_id
    assert validated_story.status == "ToDo"
    assert validated_story.id is not None  # Production ID validation


def test_create_story_with_missing_epic_id(mcp_server_process):
    """Test story creation with missing epic_id parameter."""
    initialize_server(mcp_server_process)

    # Call backlog.createStory tool without epic_id
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "title": "Test Story",
                "description": "This should fail",
                "acceptance_criteria": ["Should fail"],
            },
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0


def test_create_story_with_invalid_epic_id(mcp_server_process):
    """Test story creation with non-existent epic_id."""
    initialize_server(mcp_server_process)

    # Call backlog.createStory tool with invalid epic_id
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": "non-existent-epic-id",
                "title": "Test Story",
                "description": "This should fail due to invalid epic",
                "acceptance_criteria": ["Should fail"],
            },
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Epic not found" in response["result"]["content"][0]["text"]


def test_create_story_with_empty_title(mcp_server_process):
    """Test story creation with empty title."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Call backlog.createStory tool with empty title
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "",
                "description": "Valid description",
                "acceptance_criteria": ["Valid AC"],
            },
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Story validation error" in response["result"]["content"][0]["text"]


def test_create_story_with_empty_acceptance_criteria(mcp_server_process):
    """Test story creation with empty acceptance criteria."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Call backlog.createStory tool with empty acceptance criteria
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Valid title",
                "description": "Valid description",
                "acceptance_criteria": [],
            },
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Story validation error" in response["result"]["content"][0]["text"]


def test_get_story_tool_success(mcp_server_process):
    """Test successful story retrieval via MCP tool."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # First create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Retrievable Story",
                "description": "This story will be retrieved",
                "acceptance_criteria": ["Should be retrievable"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]

    # Call backlog.getStory tool
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
    )

    # Verify response structure
    assert "result" in response
    assert "content" in response["result"]
    assert len(response["result"]["content"]) == 1
    assert response["result"]["content"][0]["type"] == "text"

    # Parse and verify story data
    retrieved_story_data = response["result"]["content"][0]["text"]
    retrieved_story = json.loads(retrieved_story_data)

    assert retrieved_story["id"] == story_id
    assert retrieved_story["title"] == "Retrievable Story"
    assert retrieved_story["description"] == "This story will be retrieved"
    assert retrieved_story["acceptance_criteria"] == ["Should be retrievable"]
    assert retrieved_story["epic_id"] == epic_id
    assert retrieved_story["status"] == "ToDo"


def test_get_story_with_non_existent_id(mcp_server_process):
    """Test story retrieval with non-existent story ID."""
    initialize_server(mcp_server_process)

    # Call backlog.getStory tool with non-existent ID
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.getStory",
            "arguments": {"story_id": "non-existent-story-id"},
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Story not found" in response["result"]["content"][0]["text"]
    # FastMCP doesn't provide structured error data in the same way


def test_get_story_with_empty_id(mcp_server_process):
    """Test story retrieval with empty story ID."""
    initialize_server(mcp_server_process)

    # Call backlog.getStory tool with empty ID
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {"name": "backlog.getStory", "arguments": {"story_id": ""}},
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Story validation error" in response["result"]["content"][0]["text"]


def test_create_then_retrieve_story_integration(mcp_server_process):
    """Test complete create-then-retrieve story workflow."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Integration Test Story",
                "description": "Story for integration testing",
                "acceptance_criteria": [
                    "Should be created",
                    "Should be retrievable",
                    "Should maintain data integrity",
                ],
            },
        },
    )

    # Extract story ID
    created_story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(created_story_data)
    story_id = created_story["id"]

    # Retrieve the story
    get_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
    )

    # Verify retrieved story matches created story
    retrieved_story_data = get_response["result"]["content"][0]["text"]
    retrieved_story = json.loads(retrieved_story_data)

    assert retrieved_story == created_story
    assert retrieved_story["title"] == "Integration Test Story"
    assert retrieved_story["description"] == "Story for integration testing"
    assert retrieved_story["acceptance_criteria"] == [
        "Should be created",
        "Should be retrievable",
        "Should maintain data integrity",
    ]


def test_multiple_stories_same_epic(mcp_server_process):
    """Test creating multiple stories for the same epic."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create multiple stories
    story_ids = []
    for i in range(3):
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.createStory",
                "arguments": {
                    "epic_id": epic_id,
                    "title": f"Story {i+1}",
                    "description": f"Description for story {i+1}",
                    "acceptance_criteria": [f"AC for story {i+1}"],
                },
            },
        )

        story_data = response["result"]["content"][0]["text"]
        story = json.loads(story_data)
        story_ids.append(story["id"])

    # Verify all stories are unique and retrievable
    for i, story_id in enumerate(story_ids):
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
        )

        story_data = response["result"]["content"][0]["text"]
        story = json.loads(story_data)

        assert story["id"] == story_id
        assert story["title"] == f"Story {i+1}"
        assert story["epic_id"] == epic_id

    # Verify all story IDs are unique
    assert len(set(story_ids)) == 3


def test_jsonrpc_compliance_for_story_tools(mcp_server_process):
    """Test JSON-RPC 2.0 compliance for story tools."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Test create story tool JSON-RPC compliance
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "JSON-RPC Test Story",
                "description": "Testing JSON-RPC compliance",
                "acceptance_criteria": ["Should follow JSON-RPC 2.0"],
            },
        },
    )

    # Verify JSON-RPC 2.0 response structure
    assert "jsonrpc" in response
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    assert "result" in response or "error" in response

    if "result" in response:
        story_data = response["result"]["content"][0]["text"]
        story = json.loads(story_data)
        story_id = story["id"]

        # Test get story tool JSON-RPC compliance
        get_response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
        )

        # Verify JSON-RPC 2.0 response structure
        assert "jsonrpc" in get_response
        assert get_response["jsonrpc"] == "2.0"
        assert "id" in get_response
        assert "result" in get_response or "error" in get_response


def test_update_story_status_tool_success(mcp_server_process):
    """Test successful story status update via MCP tool."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # First create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Status Update Story",
                "description": "Story to test status updates",
                "acceptance_criteria": ["Should allow status updates"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]
    assert created_story["status"] == "ToDo"

    # Update the story status to InProgress
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": story_id, "status": "InProgress"},
        },
    )

    # Verify response structure
    assert "result" in response
    assert "content" in response["result"]
    assert len(response["result"]["content"]) == 1
    assert response["result"]["content"][0]["type"] == "text"

    # Parse and verify updated story data
    updated_story_data = response["result"]["content"][0]["text"]
    updated_story = json.loads(updated_story_data)

    assert updated_story["id"] == story_id
    assert updated_story["title"] == "Status Update Story"
    assert updated_story["status"] == "InProgress"
    assert updated_story["epic_id"] == epic_id


def test_update_story_status_all_valid_statuses(mcp_server_process):
    """Test updating story to all valid status values."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Multi-Status Story",
                "description": "Story to test all status transitions",
                "acceptance_criteria": ["Should work with all statuses"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]

    # Test all valid statuses
    valid_statuses = ["ToDo", "InProgress", "Review", "Done"]

    for status in valid_statuses:
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.updateStoryStatus",
                "arguments": {"story_id": story_id, "status": status},
            },
        )

        assert "result" in response
        updated_story_data = response["result"]["content"][0]["text"]
        updated_story = json.loads(updated_story_data)
        assert updated_story["status"] == status


def test_update_story_status_invalid_status_error(mcp_server_process):
    """Test story status update with invalid status."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Validation Test Story",
                "description": "Story to test validation",
                "acceptance_criteria": ["Should validate status"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]

    # Test invalid status
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": story_id, "status": "InvalidStatus"},
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Invalid status error" in response["result"]["content"][0]["text"]
    assert "Status must be one of:" in response["result"]["content"][0]["text"]


def test_update_story_status_empty_status_error(mcp_server_process):
    """Test story status update with empty status."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Empty Status Test Story",
                "description": "Story to test empty status validation",
                "acceptance_criteria": ["Should validate non-empty status"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]

    # Test empty status
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": story_id, "status": ""},
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Invalid status error" in response["result"]["content"][0]["text"]


def test_update_story_status_non_existent_story_error(mcp_server_process):
    """Test story status update with non-existent story ID."""
    initialize_server(mcp_server_process)

    # Test updating non-existent story
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": "non-existent-story-id", "status": "InProgress"},
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Story not found" in response["result"]["content"][0]["text"]


def test_update_story_status_empty_story_id_error(mcp_server_process):
    """Test story status update with empty story ID."""
    initialize_server(mcp_server_process)

    # Test updating with empty story ID
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": "", "status": "InProgress"},
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Story validation error" in response["result"]["content"][0]["text"]


def test_update_story_status_integration_with_get_story(mcp_server_process):
    """Test that status updates are reflected in subsequent getStory calls (AC 4)."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Integration Test Story",
                "description": "Story to test integration between update and get",
                "acceptance_criteria": ["Should persist status updates"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]

    # Verify initial status
    get_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
    )
    initial_story_data = get_response["result"]["content"][0]["text"]
    initial_story = json.loads(initial_story_data)
    assert initial_story["status"] == "ToDo"

    # Update status to InProgress
    update_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": story_id, "status": "InProgress"},
        },
    )

    # Verify the update response shows new status
    updated_story_data = update_response["result"]["content"][0]["text"]
    updated_story = json.loads(updated_story_data)
    assert updated_story["status"] == "InProgress"

    # Verify getStory reflects the update
    get_updated_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
    )
    retrieved_story_data = get_updated_response["result"]["content"][0]["text"]
    retrieved_story = json.loads(retrieved_story_data)
    assert retrieved_story["status"] == "InProgress"

    # Update to Done and verify again
    send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": story_id, "status": "Done"},
        },
    )

    final_get_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
    )
    final_story_data = final_get_response["result"]["content"][0]["text"]
    final_story = json.loads(final_story_data)
    assert final_story["status"] == "Done"


def test_create_update_get_complete_workflow(mcp_server_process):
    """Test complete workflow: create story, update status multiple times, then
    retrieve."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Step 1: Create story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Workflow Test Story",
                "description": "Testing complete story workflow",
                "acceptance_criteria": [
                    "Story should be created with ToDo status",
                    "Status should be updatable through all valid states",
                    "Final state should be retrievable",
                ],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]
    assert created_story["status"] == "ToDo"

    # Step 2: Progress through status states
    status_progression = ["InProgress", "Review", "Done"]

    for status in status_progression:
        # Update status
        update_response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.updateStoryStatus",
                "arguments": {"story_id": story_id, "status": status},
            },
        )

        # Verify update response
        updated_story_data = update_response["result"]["content"][0]["text"]
        updated_story = json.loads(updated_story_data)
        assert updated_story["status"] == status

        # Verify retrieval shows updated status
        get_response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
        )
        retrieved_story_data = get_response["result"]["content"][0]["text"]
        retrieved_story = json.loads(retrieved_story_data)
        assert retrieved_story["status"] == status

        # Verify other fields remain unchanged
        assert retrieved_story["id"] == story_id
        assert retrieved_story["title"] == "Workflow Test Story"
        assert retrieved_story["epic_id"] == epic_id


def test_concurrent_status_updates_same_story(mcp_server_process):
    """Test concurrent status updates to the same story."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Concurrent Update Story",
                "description": "Story to test concurrent updates",
                "acceptance_criteria": ["Should handle concurrent updates properly"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]

    # Perform rapid sequential updates (simulating concurrency)
    final_status = "Done"
    for status in ["InProgress", "Review", final_status]:
        response = send_jsonrpc_request(
            mcp_server_process,
            "tools/call",
            {
                "name": "backlog.updateStoryStatus",
                "arguments": {"story_id": story_id, "status": status},
            },
        )
        assert "result" in response

    # Verify final state
    get_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
    )
    final_story_data = get_response["result"]["content"][0]["text"]
    final_story = json.loads(final_story_data)
    assert final_story["status"] == final_status


def test_update_story_status_jsonrpc_compliance(mcp_server_process):
    """Test JSON-RPC 2.0 compliance for updateStoryStatus tool."""
    initialize_server(mcp_server_process)
    epic_id = create_test_epic(mcp_server_process)

    # Create a story
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "JSON-RPC Compliance Test Story",
                "description": "Testing JSON-RPC compliance for status updates",
                "acceptance_criteria": ["Should follow JSON-RPC 2.0 specification"],
            },
        },
    )

    story_data = create_response["result"]["content"][0]["text"]
    created_story = json.loads(story_data)
    story_id = created_story["id"]

    # Test successful update JSON-RPC compliance
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": story_id, "status": "InProgress"},
        },
    )

    # Verify JSON-RPC 2.0 response structure
    assert "jsonrpc" in response
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    assert "result" in response or "error" in response

    # Test error case JSON-RPC compliance
    error_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "backlog.updateStoryStatus",
            "arguments": {"story_id": story_id, "status": "InvalidStatus"},
        },
    )

    # Verify JSON-RPC 2.0 error response structure (FastMCP format)
    assert "jsonrpc" in error_response
    assert error_response["jsonrpc"] == "2.0"
    assert "id" in error_response
    assert (
        "result" in error_response
    )  # FastMCP returns errors as results with isError=true
    assert error_response["result"]["isError"] is True
    assert "content" in error_response["result"]
    assert len(error_response["result"]["content"]) > 0
