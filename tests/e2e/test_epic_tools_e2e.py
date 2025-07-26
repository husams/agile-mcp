"""
End-to-end tests for Epic tools via MCP JSON-RPC over stdio transport.
"""

import json
import subprocess
import sys
import os
import tempfile
import pytest
from pathlib import Path


@pytest.fixture
def mcp_server_process():
    """Start MCP server as subprocess and return process handle."""
    # Get the path to the run_server.py file
    run_server_path = Path(__file__).parent.parent.parent / "run_server.py"
    
    # Start server process
    process = subprocess.Popen(
        [sys.executable, str(run_server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    yield process
    
    # Cleanup
    process.terminate()
    process.wait()


def send_jsonrpc_request(process, method, params=None):
    """Send JSON-RPC request to MCP server and return response."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline()
    if not response_line:
        stderr_output = process.stderr.read()
        raise RuntimeError(f"No response from server. Stderr: {stderr_output}")
    
    return json.loads(response_line.strip())


def test_mcp_server_initialization(mcp_server_process):
    """Test MCP server initialization handshake."""
    # Send initialize request
    response = send_jsonrpc_request(
        mcp_server_process,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Verify response structure
    assert "result" in response
    assert "capabilities" in response["result"]
    assert "tools" in response["result"]["capabilities"]
    assert response["result"]["serverInfo"]["name"] == "Agile Management Server"


def test_create_epic_tool_success(mcp_server_process):
    """Test successful epic creation via MCP tool."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_process,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Send initialized notification
    send_jsonrpc_request(mcp_server_process, "notifications/initialized")
    
    # Call create_epic tool
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Test Epic E2E",
                "description": "This is an end-to-end test epic"
            }
        }
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


def test_find_epics_tool_success(mcp_server_process):
    """Test successful epic retrieval via MCP tool."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_process,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Send initialized notification
    send_jsonrpc_request(mcp_server_process, "notifications/initialized")
    
    # Create an epic first
    create_response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "Findable Epic",
                "description": "This epic should be findable"
            }
        }
    )
    
    # Call find_epics tool
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "find_epics",
            "arguments": {}
        }
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
    findable_epic = next((epic for epic in epics_list if epic["title"] == "Findable Epic"), None)
    assert findable_epic is not None
    assert findable_epic["description"] == "This epic should be findable"
    assert findable_epic["status"] == "Draft"


def test_create_epic_validation_error(mcp_server_process):
    """Test epic creation with validation errors."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_process,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Send initialized notification
    send_jsonrpc_request(mcp_server_process, "notifications/initialized")
    
    # Call create_epic tool with empty title
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": "",
                "description": "Valid description"
            }
        }
    )
    
    # Verify error response
    assert "error" in response
    assert response["error"]["code"] == -32001
    assert "Validation error" in response["error"]["message"]
    assert "Epic title cannot be empty" in response["error"]["message"]


def test_create_epic_with_long_title_error(mcp_server_process):
    """Test epic creation with title too long."""
    # Initialize server first
    send_jsonrpc_request(
        mcp_server_process,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Send initialized notification
    send_jsonrpc_request(mcp_server_process, "notifications/initialized")
    
    # Call create_epic tool with title too long
    long_title = "x" * 201  # Exceeds 200 character limit
    response = send_jsonrpc_request(
        mcp_server_process,
        "tools/call",
        {
            "name": "create_epic",
            "arguments": {
                "title": long_title,
                "description": "Valid description"
            }
        }
    )
    
    # Verify error response
    assert "error" in response
    assert response["error"]["code"] == -32001
    assert "Validation error" in response["error"]["message"]
    assert "Epic title cannot exceed 200 characters" in response["error"]["message"]