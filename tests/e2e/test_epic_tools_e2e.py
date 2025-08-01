"""
End-to-end tests for Epic tools via MCP JSON-RPC over stdio transport.
"""

import json

# Use the robust fixture from conftest.py instead of custom subprocess handling


def send_jsonrpc_request(process_or_fixture, method, params=None):
    """Send JSON-RPC request to MCP server and return response."""
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(process_or_fixture, tuple):
        process, env_vars, communicate_json_rpc = process_or_fixture
        # Use the robust communicate function from the fixture
        return communicate_json_rpc(method, params)
    else:
        # Legacy support for direct process
        process = process_or_fixture
        request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}

        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()

        # Read response
        response_line = process.stdout.readline()
        if not response_line:
            stderr_output = process.stderr.read()
            raise RuntimeError(f"No response from server. Stderr: {stderr_output}")

        return json.loads(response_line.strip())


def test_mcp_server_initialization(mcp_server_subprocess):
    """Test MCP server initialization handshake."""
    # Send initialize request
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    )

    # Verify response structure
    assert "result" in response
    assert "capabilities" in response["result"]
    assert "tools" in response["result"]["capabilities"]
    assert response["result"]["serverInfo"]["name"] == "Agile Management Server"


def test_create_epic_tool_success(mcp_server_subprocess):
    """Test successful epic creation via MCP tool."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_subprocess,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    )

    # Send initialized notification (no response expected)
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(mcp_server_subprocess, tuple):
        process, env_vars, communicate_json_rpc = mcp_server_subprocess
    else:
        process = mcp_server_subprocess
    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Test Project E2E",
                "description": "Project for E2E epic testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Call create_epic tool
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Test Epic E2E",
                "description": "This is an end-to-end test epic",
                "project_id": project_id,
            },
        },
    )

    # Verify response
    assert "result" in response
    result = response["result"]
    assert "content" in result

    epic_data = result["content"][0]["text"]
    epic_dict = json.loads(epic_data)

    assert epic_dict["title"] == "Test Epic E2E"
    assert epic_dict["description"] == "This is an end-to-end test epic"
    assert epic_dict["status"] == "Draft"
    assert "id" in epic_dict


def test_find_epics_tool_success(mcp_server_subprocess):
    """Test successful epic retrieval via MCP tool."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_subprocess,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    )

    # Send initialized notification (no response expected)
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(mcp_server_subprocess, tuple):
        process, env_vars, communicate_json_rpc = mcp_server_subprocess
    else:
        process = mcp_server_subprocess
    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Findable Project",
                "description": "Project for findable epic testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Create an epic first
    _ = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Findable Epic",
                "description": "This epic should be findable",
                "project_id": project_id,
            },
        },
    )

    # Call find_epics tool
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {"name": "find_epics", "arguments": {}},
    )

    # Verify response
    assert "result" in response
    result = response["result"]
    assert "content" in result

    epics_data = result["content"][0]["text"]
    epics_list = json.loads(epics_data)

    assert isinstance(epics_list, list)
    assert len(epics_list) >= 1

    # Find our created epic
    findable_epic = next(
        (epic for epic in epics_list if epic["title"] == "Findable Epic"), None
    )
    assert findable_epic is not None
    assert findable_epic["description"] == "This epic should be findable"
    assert findable_epic["status"] == "Draft"


def test_create_epic_validation_error(mcp_server_subprocess):
    """Test epic creation with validation errors."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_subprocess,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    )

    # Send initialized notification (no response expected)
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(mcp_server_subprocess, tuple):
        process, env_vars, communicate_json_rpc = mcp_server_subprocess
    else:
        process = mcp_server_subprocess
    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Validation Test Project",
                "description": "Project for validation testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Call create_epic tool with empty title
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "",
                "description": "Valid description",
                "project_id": project_id,
            },
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Validation error" in response["result"]["content"][0]["text"]
    assert "Epic title cannot be empty" in response["result"]["content"][0]["text"]


def test_create_epic_with_long_title_error(mcp_server_subprocess):
    """Test epic creation with title too long."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_subprocess,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    )

    # Send initialized notification (no response expected)
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(mcp_server_subprocess, tuple):
        process, env_vars, communicate_json_rpc = mcp_server_subprocess
    else:
        process = mcp_server_subprocess
    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Long Title Test Project",
                "description": "Project for long title testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Call create_epic tool with title too long
    long_title = "x" * 201  # Exceeds 200 character limit
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": long_title,
                "description": "Valid description",
                "project_id": project_id,
            },
        },
    )

    # Verify error response (FastMCP format)
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert len(response["result"]["content"]) > 0
    assert "Validation error" in response["result"]["content"][0]["text"]
    assert (
        "Epic title cannot exceed 200 characters"
        in response["result"]["content"][0]["text"]
    )


def initialize_server(mcp_server_subprocess):
    """Helper function to initialize MCP server."""
    # Send initialize request
    send_jsonrpc_request(
        mcp_server_subprocess,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    )

    # Send initialized notification (no response expected)
    # Handle both direct process and mcp_server_subprocess fixture tuple
    if isinstance(mcp_server_subprocess, tuple):
        process, env_vars, communicate_json_rpc = mcp_server_subprocess
    else:
        process = mcp_server_subprocess
    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()


def test_update_epic_status_tool_success(mcp_server_subprocess):
    """Test successful epic status update via MCP tool."""
    initialize_server(mcp_server_subprocess)

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Update Test Project",
                "description": "Project for update testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Create an epic first
    create_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Epic to Update",
                "description": "This epic will be updated",
                "project_id": project_id,
            },
        },
    )

    # Extract the epic ID from create response
    epic_data = create_response["result"]["content"][0]["text"]
    epic_dict = json.loads(epic_data)
    epic_id = epic_dict["id"]

    # Update epic status
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "update_epic_status",
            "arguments": {"epic_id": epic_id, "status": "Ready"},
        },
    )

    # Verify response
    assert "result" in response
    result = response["result"]
    assert "content" in result

    updated_epic_data = result["content"][0]["text"]
    updated_epic_dict = json.loads(updated_epic_data)

    assert updated_epic_dict["id"] == epic_id
    assert updated_epic_dict["title"] == "Epic to Update"
    assert updated_epic_dict["description"] == "This epic will be updated"
    assert updated_epic_dict["status"] == "Ready"


def test_update_epic_status_all_valid_statuses(mcp_server_subprocess):
    """Test updating epic status to all valid status values."""
    initialize_server(mcp_server_subprocess)

    valid_statuses = ["Draft", "Ready", "In Progress", "Done", "On Hold"]

    for status in valid_statuses:
        # Create project first
        project_response = send_jsonrpc_request(
            mcp_server_subprocess,
            "tools/call",
            {
                "name": "create_project",
                "arguments": {
                    "name": f"Project for {status}",
                    "description": f"Project for testing {status} status",
                },
            },
        )

        project_data = json.loads(project_response["result"]["content"][0]["text"])
        project_id = project_data["id"]

        # Create an epic
        create_response = send_jsonrpc_request(
            mcp_server_subprocess,
            "tools/call",
            {
                "name": "create_epic",
                "arguments": {
                    "title": f"Epic {status}",
                    "description": f"Epic for testing {status} status",
                    "project_id": project_id,
                },
            },
        )

        epic_data = create_response["result"]["content"][0]["text"]
        epic_dict = json.loads(epic_data)
        epic_id = epic_dict["id"]

        # Update status
        response = send_jsonrpc_request(
            mcp_server_subprocess,
            "tools/call",
            {
                "name": "update_epic_status",
                "arguments": {"epic_id": epic_id, "status": status},
            },
        )

        # Verify response
        updated_epic_data = response["result"]["content"][0]["text"]
        updated_epic_dict = json.loads(updated_epic_data)
        assert updated_epic_dict["status"] == status


def test_update_epic_status_not_found(mcp_server_subprocess):
    """Test updating status of non-existent epic."""
    initialize_server(mcp_server_subprocess)

    # Try to update non-existent epic
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "update_epic_status",
            "arguments": {"epic_id": "nonexistent-id", "status": "Ready"},
        },
    )

    # Verify error response
    assert "result" in response
    assert response["result"]["isError"] is True
    assert "content" in response["result"]
    assert (
        "Epic with ID 'nonexistent-id' not found"
        in response["result"]["content"][0]["text"]
    )


def test_update_epic_status_invalid_status(mcp_server_subprocess):
    """Test updating epic with invalid status values."""
    initialize_server(mcp_server_subprocess)

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Invalid Status Test Project",
                "description": "Project for invalid status testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Create an epic first
    create_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Epic for Invalid Status",
                "description": "This epic will test invalid status",
                "project_id": project_id,
            },
        },
    )

    epic_data = create_response["result"]["content"][0]["text"]
    epic_dict = json.loads(epic_data)
    epic_id = epic_dict["id"]

    invalid_statuses = ["InvalidStatus", "DRAFT", "draft", "Complete", "Finished"]

    for invalid_status in invalid_statuses:
        response = send_jsonrpc_request(
            mcp_server_subprocess,
            "tools/call",
            {
                "name": "update_epic_status",
                "arguments": {"epic_id": epic_id, "status": invalid_status},
            },
        )

        # Verify error response
        assert "result" in response
        assert response["result"]["isError"] is True
        assert "content" in response["result"]
        assert "Epic status must be one of" in response["result"]["content"][0]["text"]


def test_update_epic_status_empty_parameters(mcp_server_subprocess):
    """Test updating epic with empty parameters."""
    initialize_server(mcp_server_subprocess)

    # Test empty epic_id
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "update_epic_status",
            "arguments": {"epic_id": "", "status": "Ready"},
        },
    )

    assert "result" in response
    assert response["result"]["isError"] is True
    assert "Epic ID cannot be empty" in response["result"]["content"][0]["text"]

    # Test empty status
    response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "update_epic_status",
            "arguments": {"epic_id": "some-id", "status": ""},
        },
    )

    assert "result" in response
    assert response["result"]["isError"] is True
    assert "Epic status cannot be empty" in response["result"]["content"][0]["text"]


def test_update_epic_status_integration_with_find_epics(mcp_server_subprocess):
    """Test that status updates are reflected in findEpics calls (AC 4)."""
    initialize_server(mcp_server_subprocess)

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Integration Test Project",
                "description": "Project for integration testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Create an epic
    create_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Integration Test Epic",
                "description": "Epic for testing integration with findEpics",
                "project_id": project_id,
            },
        },
    )

    epic_data = create_response["result"]["content"][0]["text"]
    epic_dict = json.loads(epic_data)
    epic_id = epic_dict["id"]

    # Update status
    send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "update_epic_status",
            "arguments": {"epic_id": epic_id, "status": "In Progress"},
        },
    )

    # Verify change is reflected in findEpics
    find_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {"name": "find_epics", "arguments": {}},
    )

    epics_data = find_response["result"]["content"][0]["text"]
    epics_list = json.loads(epics_data)

    # Find our updated epic
    updated_epic = next((epic for epic in epics_list if epic["id"] == epic_id), None)
    assert updated_epic is not None
    assert updated_epic["status"] == "In Progress"


def test_multiple_status_transitions_workflow(mcp_server_subprocess):
    """Test multiple status transitions through workflow states."""
    initialize_server(mcp_server_subprocess)

    # Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Workflow Test Project",
                "description": "Project for workflow testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Create an epic
    create_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Workflow Epic",
                "description": "Epic for testing workflow transitions",
                "project_id": project_id,
            },
        },
    )

    epic_data = create_response["result"]["content"][0]["text"]
    epic_dict = json.loads(epic_data)
    epic_id = epic_dict["id"]

    # Test workflow: Draft -> Ready -> In Progress -> Done
    workflow_transitions = [
        ("Ready", "Epic should be Ready"),
        ("In Progress", "Epic should be In Progress"),
        ("Done", "Epic should be Done"),
    ]

    for target_status, description in workflow_transitions:
        response = send_jsonrpc_request(
            mcp_server_subprocess,
            "tools/call",
            {
                "name": "update_epic_status",
                "arguments": {"epic_id": epic_id, "status": target_status},
            },
        )

        # Verify transition
        updated_epic_data = response["result"]["content"][0]["text"]
        updated_epic_dict = json.loads(updated_epic_data)
        assert updated_epic_dict["status"] == target_status, description

    # Verify final state in findEpics
    find_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {"name": "find_epics", "arguments": {}},
    )

    epics_data = find_response["result"]["content"][0]["text"]
    epics_list = json.loads(epics_data)

    final_epic = next((epic for epic in epics_list if epic["id"] == epic_id), None)
    assert final_epic["status"] == "Done"


def test_create_update_retrieve_complete_workflow(mcp_server_subprocess):
    """Test complete workflow: create epic, update status, then retrieve epic."""
    initialize_server(mcp_server_subprocess)

    # Step 1: Create project first
    project_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_project",
            "arguments": {
                "name": "Complete Workflow Project",
                "description": "Project for complete workflow testing",
            },
        },
    )

    project_data = json.loads(project_response["result"]["content"][0]["text"])
    project_id = project_data["id"]

    # Step 2: Create epic
    create_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Complete Workflow Epic",
                "description": "Epic for testing complete workflow",
                "project_id": project_id,
            },
        },
    )

    epic_data = create_response["result"]["content"][0]["text"]
    epic_dict = json.loads(epic_data)
    epic_id = epic_dict["id"]

    # Verify initial state
    assert epic_dict["status"] == "Draft"

    # Step 2: Update status
    update_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {
            "name": "update_epic_status",
            "arguments": {"epic_id": epic_id, "status": "On Hold"},
        },
    )

    updated_epic_data = update_response["result"]["content"][0]["text"]
    updated_epic_dict = json.loads(updated_epic_data)

    # Verify update response
    assert updated_epic_dict["id"] == epic_id
    assert updated_epic_dict["status"] == "On Hold"
    assert updated_epic_dict["title"] == "Complete Workflow Epic"
    assert updated_epic_dict["description"] == "Epic for testing complete workflow"

    # Step 3: Retrieve updated epic via findEpics
    find_response = send_jsonrpc_request(
        mcp_server_subprocess,
        "tools/call",
        {"name": "find_epics", "arguments": {}},
    )

    epics_data = find_response["result"]["content"][0]["text"]
    epics_list = json.loads(epics_data)

    # Verify retrieved epic has updated status
    retrieved_epic = next((epic for epic in epics_list if epic["id"] == epic_id), None)
    assert retrieved_epic is not None
    assert retrieved_epic["status"] == "On Hold"
    assert retrieved_epic["title"] == "Complete Workflow Epic"
    assert retrieved_epic["description"] == "Epic for testing complete workflow"
