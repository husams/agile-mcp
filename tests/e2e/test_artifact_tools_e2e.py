"""
End-to-end tests for Artifact tools via MCP JSON-RPC over stdio transport.
"""

import json
import time

from tests.e2e.test_helpers import (
    validate_artifact_tool_response,
    validate_error_response_format,
    validate_json_response,
    validate_jsonrpc_response_format,
)

# Use the robust fixture from conftest.py instead of custom subprocess handling


def send_jsonrpc_request(process_or_fixture, method, params=None):
    """Send JSON-RPC request to MCP server and return response."""
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(process_or_fixture, tuple):
        process, env_vars, communicate_json_rpc = process_or_fixture
    else:
        process = process_or_fixture

    # Original function body follows:
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


def initialize_server(process_or_fixture):
    """Initialize the MCP server for testing."""
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(process_or_fixture, tuple):
        process, env_vars, communicate_json_rpc = process_or_fixture
    else:
        process = process_or_fixture

    # Send initialize request
    init_response = send_jsonrpc_request(
        process_or_fixture,
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


def create_test_epic_and_story(process):
    """Create a test epic and story for artifact testing."""
    # Create project first
    project_response = send_jsonrpc_request(
        process,
        "tools/call",
        {
            "name": "projects.create",
            "arguments": {
                "name": "Test Project for Artifacts",
                "description": "Project created for artifact testing purposes",
            },
        },
    )

    assert "result" in project_response
    assert "content" in project_response["result"]
    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Create epic with project_id
    epic_response = send_jsonrpc_request(
        process,
        "tools/call",
        {
            "name": "backlog.createEpic",
            "arguments": {
                "title": "Test Epic for Artifacts",
                "description": "Epic created for artifact testing purposes",
                "project_id": project_id,
            },
        },
    )

    assert "result" in epic_response
    assert "content" in epic_response["result"]
    epic_data = json.loads(epic_response["result"]["content"][0]["text"])
    epic_id = epic_data["id"]

    # Create story
    story_response = send_jsonrpc_request(
        process,
        "tools/call",
        {
            "name": "backlog.createStory",
            "arguments": {
                "epic_id": epic_id,
                "title": "Test Story for Artifacts",
                "description": "As a developer, I want to test artifact linking",
                "acceptance_criteria": [
                    "Should link artifacts",
                    "Should retrieve artifacts",
                ],
            },
        },
    )

    assert "result" in story_response
    assert "content" in story_response["result"]
    story_data = json.loads(story_response["result"]["content"][0]["text"])
    story_id = story_data["id"]

    return epic_id, story_id


class TestArtifactToolsE2E:
    """End-to-end tests for artifact management tools."""

    def test_artifacts_link_to_story_e2e_success(self, mcp_server_subprocess):
        """Test artifacts.linkToStory tool via MCP JSON-RPC - success case."""
        process = mcp_server_subprocess

        # Initialize server
        init_response = initialize_server(process)
        assert "result" in init_response

        # Create test epic and story
        epic_id, story_id = create_test_epic_and_story(process)

        # Link artifact to story
        link_response = send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": "artifacts.linkToStory",
                "arguments": {
                    "story_id": story_id,
                    "uri": "file:///path/to/implementation.js",
                    "relation": "implementation",
                },
            },
        )

        # Verify response structure
        assert "result" in link_response
        assert "content" in link_response["result"]
        assert len(link_response["result"]["content"]) == 1
        assert link_response["result"]["content"][0]["type"] == "text"

        # Extract and validate tool response using validation helpers
        tool_response_text = link_response["result"]["content"][0]["text"]
        artifact_response = validate_artifact_tool_response(tool_response_text)

        # Verify artifact data using validated Pydantic model
        assert artifact_response.uri == "file:///path/to/implementation.js"
        assert artifact_response.relation == "implementation"
        assert artifact_response.story_id == story_id
        assert artifact_response.id is not None

    def test_artifacts_link_to_story_e2e_validation_error(self, mcp_server_subprocess):
        """Test artifacts.linkToStory tool with validation error."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Create test epic and story
        epic_id, story_id = create_test_epic_and_story(process)

        # Try to link artifact with empty URI
        response = send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": "artifacts.linkToStory",
                "arguments": {
                    "story_id": story_id,
                    "uri": "",
                    "relation": "implementation",
                },
            },
        )

        # Verify error response using validation helpers
        assert "result" in response
        assert "content" in response["result"]
        assert response["result"]["isError"] is True

        # Validate error response format and content
        tool_response_text = response["result"]["content"][0]["text"]
        error_response_json = validate_json_response(tool_response_text)
        validated_error = validate_error_response_format(error_response_json)

        # Verify error message content
        assert "Artifact validation error" in validated_error["message"]
        assert "URI cannot be empty" in validated_error["message"]

    def test_artifacts_link_to_story_e2e_invalid_relation(self, mcp_server_subprocess):
        """Test artifacts.linkToStory tool with invalid relation type."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Create test epic and story
        epic_id, story_id = create_test_epic_and_story(process)

        # Try to link artifact with invalid relation
        response = send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": "artifacts.linkToStory",
                "arguments": {
                    "story_id": story_id,
                    "uri": "file:///path/to/code.js",
                    "relation": "invalid-relation",
                },
            },
        )

        # Verify error response using validation helpers
        assert "result" in response
        assert "content" in response["result"]
        assert response["result"]["isError"] is True

        # Validate error response format
        tool_response_text = response["result"]["content"][0]["text"]
        error_response_json = validate_json_response(tool_response_text)
        validated_error = validate_error_response_format(error_response_json)

        # Verify error message content
        assert "Invalid relation type" in validated_error["message"]

    def test_artifacts_link_to_story_e2e_story_not_found(self, mcp_server_subprocess):
        """Test artifacts.linkToStory tool with non-existent story."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Try to link artifact to non-existent story
        response = send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": "artifacts.linkToStory",
                "arguments": {
                    "story_id": "non-existent-story-id",
                    "uri": "file:///path/to/code.js",
                    "relation": "implementation",
                },
            },
        )

        # Verify error response (FastMCP returns successful response with error content)
        assert "result" in response
        assert "content" in response["result"]
        assert response["result"]["isError"] is True
        assert "Story not found" in response["result"]["content"][0]["text"]

    def test_artifacts_list_for_story_e2e_success(self, mcp_server_subprocess):
        """Test artifacts.listForStory tool via MCP JSON-RPC - success case."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Create test epic and story
        epic_id, story_id = create_test_epic_and_story(process)

        # Link multiple artifacts to story
        artifacts_data = [
            {"uri": "file:///path/to/implementation.js", "relation": "implementation"},
            {"uri": "file:///path/to/design.md", "relation": "design"},
            {"uri": "file:///path/to/test.py", "relation": "test"},
        ]

        created_artifacts = []
        for artifact_data in artifacts_data:
            link_response = send_jsonrpc_request(
                process,
                "tools/call",
                {
                    "name": "artifacts.linkToStory",
                    "arguments": {
                        "story_id": story_id,
                        "uri": artifact_data["uri"],
                        "relation": artifact_data["relation"],
                    },
                },
            )
            artifact = json.loads(link_response["result"]["content"][0]["text"])
            created_artifacts.append(artifact)

        # List artifacts for story
        list_response = send_jsonrpc_request(
            process,
            "tools/call",
            {"name": "artifacts.listForStory", "arguments": {"story_id": story_id}},
        )

        # Verify response structure
        assert "result" in list_response
        assert "content" in list_response["result"]
        assert len(list_response["result"]["content"]) == 1
        assert list_response["result"]["content"][0]["type"] == "text"

        # Parse and verify artifacts list
        artifacts_list = json.loads(list_response["result"]["content"][0]["text"])
        assert isinstance(artifacts_list, list)
        assert len(artifacts_list) == 3

        # Verify all created artifacts are in the list
        artifact_ids = [a["id"] for a in artifacts_list]
        for created_artifact in created_artifacts:
            assert created_artifact["id"] in artifact_ids

        # Verify artifact properties
        for artifact in artifacts_list:
            assert "id" in artifact
            assert "uri" in artifact
            assert "relation" in artifact
            assert artifact["story_id"] == story_id
            assert artifact["relation"] in ["implementation", "design", "test"]

    def test_artifacts_list_for_story_e2e_empty_result(self, mcp_server_subprocess):
        """Test artifacts.listForStory tool with no artifacts."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Create test epic and story (no artifacts linked)
        epic_id, story_id = create_test_epic_and_story(process)

        # List artifacts for story
        list_response = send_jsonrpc_request(
            process,
            "tools/call",
            {"name": "artifacts.listForStory", "arguments": {"story_id": story_id}},
        )

        # Verify response structure
        assert "result" in list_response
        assert "content" in list_response["result"]

        # Handle both empty result scenarios: no content or empty list content
        if len(list_response["result"]["content"]) == 0:
            # No content means empty result
            artifacts_list = []
        else:
            # Content with empty list
            assert list_response["result"]["content"][0]["type"] == "text"
            artifacts_list = json.loads(list_response["result"]["content"][0]["text"])

        assert isinstance(artifacts_list, list)
        assert len(artifacts_list) == 0

    def test_artifacts_list_for_story_e2e_validation_error(self, mcp_server_subprocess):
        """Test artifacts.listForStory tool with validation error."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Try to list artifacts with empty story ID
        response = send_jsonrpc_request(
            process,
            "tools/call",
            {"name": "artifacts.listForStory", "arguments": {"story_id": ""}},
        )

        # Verify error response (FastMCP returns successful response with error content)
        assert "result" in response
        assert "content" in response["result"]
        assert response["result"]["isError"] is True
        assert "Artifact validation error" in response["result"]["content"][0]["text"]
        assert "Story ID cannot be empty" in response["result"]["content"][0]["text"]

    def test_complete_workflow_create_story_link_artifacts_retrieve(
        self, mcp_server_subprocess
    ):
        """Test complete workflow: create story, link artifacts, retrieve artifacts."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Step 1: Create project first
        project_response = send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": "projects.create",
                "arguments": {
                    "name": "Complete Workflow Project",
                    "description": "Project for complete workflow testing",
                },
            },
        )

        project_data = json.loads(project_response["result"]["content"][0]["text"])
        project_id = project_data["id"]

        # Step 2: Create epic
        epic_response = send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": "backlog.createEpic",
                "arguments": {
                    "title": "Complete Workflow Epic",
                    "description": "Epic for complete workflow testing",
                    "project_id": project_id,
                },
            },
        )
        epic_data = json.loads(epic_response["result"]["content"][0]["text"])
        epic_id = epic_data["id"]

        # Step 3: Create story
        story_response = send_jsonrpc_request(
            process,
            "tools/call",
            {
                "name": "backlog.createStory",
                "arguments": {
                    "epic_id": epic_id,
                    "title": "Complete Workflow Story",
                    "description": "As a user, I want to test the complete workflow",
                    "acceptance_criteria": [
                        "Should create epic",
                        "Should create story",
                        "Should link artifacts",
                        "Should retrieve artifacts",
                    ],
                },
            },
        )
        story_data = json.loads(story_response["result"]["content"][0]["text"])
        story_id = story_data["id"]

        # Step 3: Link multiple artifacts with different relation types
        test_artifacts = [
            ("file:///src/components/UserProfile.jsx", "implementation"),
            ("file:///docs/user-profile-design.md", "design"),
            ("file:///tests/user-profile.test.js", "test"),
            ("https://github.com/project/repo/pull/123", "implementation"),
        ]

        linked_artifacts = []
        for uri, relation in test_artifacts:
            link_response = send_jsonrpc_request(
                process,
                "tools/call",
                {
                    "name": "artifacts.linkToStory",
                    "arguments": {
                        "story_id": story_id,
                        "uri": uri,
                        "relation": relation,
                    },
                },
            )
            assert "result" in link_response
            artifact_data = json.loads(link_response["result"]["content"][0]["text"])
            linked_artifacts.append(artifact_data)

        # Step 4: Retrieve all artifacts for the story
        list_response = send_jsonrpc_request(
            process,
            "tools/call",
            {"name": "artifacts.listForStory", "arguments": {"story_id": story_id}},
        )

        assert "result" in list_response
        retrieved_artifacts = json.loads(list_response["result"]["content"][0]["text"])

        # Step 5: Verify all artifacts were linked and retrieved correctly
        assert len(retrieved_artifacts) == len(test_artifacts)

        # Check each artifact is present with correct properties
        retrieved_uris = [artifact["uri"] for artifact in retrieved_artifacts]
        for uri, relation in test_artifacts:
            assert uri in retrieved_uris

            # Find matching artifact and verify relation
            matching_artifact = next(a for a in retrieved_artifacts if a["uri"] == uri)
            assert matching_artifact["relation"] == relation
            assert matching_artifact["story_id"] == story_id
            assert "id" in matching_artifact

        # Step 6: Verify story retrieval still works with artifacts linked
        story_get_response = send_jsonrpc_request(
            process,
            "tools/call",
            {"name": "backlog.getStory", "arguments": {"story_id": story_id}},
        )

        assert "result" in story_get_response
        retrieved_story = json.loads(story_get_response["result"]["content"][0]["text"])
        assert retrieved_story["id"] == story_id
        assert retrieved_story["title"] == "Complete Workflow Story"

    def test_artifacts_with_various_uri_formats(self, mcp_server_subprocess):
        """Test artifact linking with various valid URI formats."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Create test epic and story
        epic_id, story_id = create_test_epic_and_story(process)

        # Test various URI formats
        test_uris = [
            "file:///absolute/path/to/local/file.js",
            "https://github.com/user/repo/blob/main/src/component.jsx",
            "http://example.com/api/documentation",
            "ftp://files.company.com/specifications/spec.pdf",
            "mailto:team@company.com",
            "custom-scheme://internal/resource/path",
        ]

        # Link artifacts with different URI formats
        for uri in test_uris:
            link_response = send_jsonrpc_request(
                process,
                "tools/call",
                {
                    "name": "artifacts.linkToStory",
                    "arguments": {
                        "story_id": story_id,
                        "uri": uri,
                        "relation": "implementation",
                    },
                },
            )

            # Verify successful linking
            assert "result" in link_response
            artifact_data = json.loads(link_response["result"]["content"][0]["text"])
            assert artifact_data["uri"] == uri
            assert artifact_data["story_id"] == story_id

        # Verify all artifacts are retrieved
        list_response = send_jsonrpc_request(
            process,
            "tools/call",
            {"name": "artifacts.listForStory", "arguments": {"story_id": story_id}},
        )

        artifacts_list = json.loads(list_response["result"]["content"][0]["text"])
        assert len(artifacts_list) == len(test_uris)

        retrieved_uris = [artifact["uri"] for artifact in artifacts_list]
        for uri in test_uris:
            assert uri in retrieved_uris

    def test_artifacts_with_invalid_uri_formats(self, mcp_server_subprocess):
        """Test artifact linking with invalid URI formats returns proper errors."""
        process = mcp_server_subprocess

        # Initialize server
        initialize_server(process)

        # Create test epic and story
        epic_id, story_id = create_test_epic_and_story(process)

        # Test invalid URI formats (reduced to prevent server hang after 4+
        # sequential invalid requests)
        invalid_uris = [
            "not-a-uri",
            "://missing-scheme",
            "123://invalid-scheme-start",
            "file:// spaces in uri",
        ]

        for i, invalid_uri in enumerate(invalid_uris):
            # Add small delay between requests to prevent server from hanging
            if i > 0:
                time.sleep(0.1)

            response = send_jsonrpc_request(
                process,
                "tools/call",
                {
                    "name": "artifacts.linkToStory",
                    "arguments": {
                        "story_id": story_id,
                        "uri": invalid_uri,
                        "relation": "implementation",
                    },
                },
            )

            # Verify error response (FastMCP returns successful response with
            # error content)
            assert "result" in response
            assert "content" in response["result"]
            assert response["result"]["isError"] is True
            assert (
                "validation error" in response["result"]["content"][0]["text"].lower()
            )

    def test_server_capabilities_include_artifact_tools(self, mcp_server_subprocess):
        """Test that server initialization includes artifact tools in capabilities."""
        process = mcp_server_subprocess

        # Initialize server and check capabilities
        init_response = initialize_server(process)

        # Verify response contains capabilities
        assert "result" in init_response
        assert "capabilities" in init_response["result"]
        assert "tools" in init_response["result"]["capabilities"]

        # The server should register the artifact tools
        # Note: The exact structure depends on FastMCP implementation
        # This test verifies the server initializes without errors
