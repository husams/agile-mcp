"""
Unit tests for E2E test validation helpers.
"""

import json

import pytest
from pydantic import ValidationError

from src.agile_mcp.models.response import ArtifactResponse, EpicResponse, StoryResponse
from tests.e2e.test_helpers import (
    extract_response_data,
    validate_artifact_response,
    validate_epic_response,
    validate_error_response_format,
    validate_full_tool_response,
    validate_json_response,
    validate_jsonrpc_request_format,
    validate_jsonrpc_response_format,
    validate_mcp_protocol_compliance,
    validate_story_response,
    validate_tool_response_format,
)


class TestJSONResponseValidation:
    """Test JSON response parsing and validation."""

    def test_validate_json_response_valid(self):
        """Test valid JSON response parsing."""
        response = '{"success": true, "data": {"id": "test"}}'
        result = validate_json_response(response)
        assert result == {"success": True, "data": {"id": "test"}}

    def test_validate_json_response_invalid_json(self):
        """Test invalid JSON response handling."""
        response = '{"invalid": json}'
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_json_response(response)
        assert "Response is not valid JSON" in str(exc_info.value)

    def test_validate_json_response_non_dict(self):
        """Test non-dict JSON response handling."""
        response = '["array", "instead", "of", "object"]'
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_json_response(response)
        assert "Response must be dict, got list" in str(exc_info.value)


class TestToolResponseValidation:
    """Test tool response format validation."""

    def test_validate_tool_response_format_success(self):
        """Test valid success tool response."""
        response = {"success": True, "data": {"id": "test", "title": "Test Story"}}
        result = validate_tool_response_format(response)
        assert result == response

    def test_validate_tool_response_format_error(self):
        """Test valid error tool response."""
        response = {
            "success": False,
            "error": "ValidationError",
            "message": "Story not found",
        }
        result = validate_tool_response_format(response)
        assert result == response

    def test_validate_tool_response_format_missing_success(self):
        """Test tool response without success field (direct data format is valid)."""
        response = {"data": {"id": "test"}}
        # Should not raise an exception - direct data responses don't require success field
        result = validate_tool_response_format(response)
        assert result == response

    def test_validate_tool_response_format_success_missing_data(self):
        """Test success response missing data field."""
        response = {"success": True}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_tool_response_format(response)
        assert "Success response missing 'data' field" in str(exc_info.value)

    def test_validate_tool_response_format_error_missing_fields(self):
        """Test error response missing required fields."""
        response = {"success": False}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_tool_response_format(response)
        assert "Error response missing required fields" in str(exc_info.value)


class TestJSONRPCValidation:
    """Test JSON-RPC 2.0 protocol validation."""

    def test_validate_jsonrpc_request_format_valid(self):
        """Test valid JSON-RPC request."""
        request = {
            "jsonrpc": "2.0",
            "method": "createStory",
            "params": {"title": "Test"},
            "id": 1,
        }
        result = validate_jsonrpc_request_format(request)
        assert result == request

    def test_validate_jsonrpc_request_format_missing_fields(self):
        """Test JSON-RPC request missing required fields."""
        request = {"jsonrpc": "2.0", "method": "createStory"}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_jsonrpc_request_format(request)
        assert "missing required fields: ['id']" in str(exc_info.value)

    def test_validate_jsonrpc_request_format_wrong_version(self):
        """Test JSON-RPC request with wrong version."""
        request = {"jsonrpc": "1.0", "method": "createStory", "id": 1}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_jsonrpc_request_format(request)
        assert "JSON-RPC version must be '2.0'" in str(exc_info.value)

    def test_validate_jsonrpc_response_format_success(self):
        """Test valid JSON-RPC success response."""
        response = {"jsonrpc": "2.0", "result": {"success": True, "data": {}}, "id": 1}
        result = validate_jsonrpc_response_format(response)
        assert result == response

    def test_validate_jsonrpc_response_format_error(self):
        """Test valid JSON-RPC error response."""
        response = {
            "jsonrpc": "2.0",
            "error": {"code": -1, "message": "Internal error"},
            "id": 1,
        }
        result = validate_jsonrpc_response_format(response)
        assert result == response

    def test_validate_jsonrpc_response_format_both_result_and_error(self):
        """Test JSON-RPC response with both result and error."""
        response = {
            "jsonrpc": "2.0",
            "result": {"success": True},
            "error": {"code": -1, "message": "Error"},
            "id": 1,
        }
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_jsonrpc_response_format(response)
        assert "cannot have both 'result' and 'error' fields" in str(exc_info.value)

    def test_validate_jsonrpc_response_format_neither_result_nor_error(self):
        """Test JSON-RPC response with neither result nor error."""
        response = {"jsonrpc": "2.0", "id": 1}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_jsonrpc_response_format(response)
        assert "must have either 'result' or 'error' field" in str(exc_info.value)


class TestMCPProtocolCompliance:
    """Test MCP protocol-specific validation."""

    def test_validate_mcp_protocol_compliance_valid(self):
        """Test valid MCP request/response pair."""
        request = {
            "jsonrpc": "2.0",
            "method": "createStory",
            "params": {"title": "Test"},
            "id": 1,
        }
        response = {"jsonrpc": "2.0", "result": {"success": True, "data": {}}, "id": 1}
        req, resp = validate_mcp_protocol_compliance(request, response)
        assert req == request
        assert resp == response

    def test_validate_mcp_protocol_compliance_id_mismatch(self):
        """Test MCP validation with mismatched request/response IDs."""
        request = {"jsonrpc": "2.0", "method": "createStory", "id": 1}
        response = {"jsonrpc": "2.0", "result": {"success": True}, "id": 2}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_mcp_protocol_compliance(request, response)
        assert "Request and response IDs must match" in str(exc_info.value)

    def test_validate_mcp_protocol_compliance_invalid_method(self):
        """Test MCP validation with invalid method name."""
        request = {"jsonrpc": "2.0", "method": "invalidMethod", "id": 1}
        response = {"jsonrpc": "2.0", "result": {"success": True}, "id": 1}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_mcp_protocol_compliance(request, response)
        assert "Unknown MCP method: invalidMethod" in str(exc_info.value)


class TestPydanticModelValidation:
    """Test Pydantic model validation for responses."""

    def test_validate_story_response_valid(self):
        """Test valid story response validation."""
        data = {
            "id": "story-1",
            "title": "Test Story",
            "description": "Test description",
            "acceptance_criteria": ["Criterion 1"],
            "status": "ToDo",
            "priority": 1,
            "created_at": "2025-07-27T10:00:00Z",
            "epic_id": "epic-1",
        }
        result = validate_story_response(data)
        assert isinstance(result, StoryResponse)
        assert result.id == "story-1"
        assert result.title == "Test Story"

    def test_validate_story_response_missing_field(self):
        """Test story response validation with missing required field."""
        data = {
            "id": "story-1",
            "title": "Test Story",
            # Missing description, acceptance_criteria, status, priority, epic_id
        }
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_story_response(data)
        assert "StoryResponse validation failed" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)

    def test_validate_epic_response_valid(self):
        """Test valid epic response validation."""
        data = {
            "id": "epic-1",
            "title": "Test Epic",
            "description": "Test description",
            "status": "Ready",
        }
        result = validate_epic_response(data)
        assert isinstance(result, EpicResponse)
        assert result.id == "epic-1"

    def test_validate_artifact_response_valid(self):
        """Test valid artifact response validation."""
        data = {
            "id": "artifact-1",
            "story_id": "story-1",
            "uri": "file:///test.js",
            "relation": "implementation",
        }
        result = validate_artifact_response(data)
        assert isinstance(result, ArtifactResponse)
        assert result.uri == "file:///test.js"


class TestErrorResponseValidation:
    """Test error response validation."""

    def test_validate_error_response_format_valid(self):
        """Test valid error response."""
        response = {
            "success": False,
            "error": "ValidationError",
            "message": "Story not found",
        }
        result = validate_error_response_format(response)
        assert result == response

    def test_validate_error_response_format_success_true(self):
        """Test error validation with success=True."""
        response = {
            "success": True,
            "error": "ValidationError",
            "message": "Story not found",
        }
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_error_response_format(response)
        assert "Expected error response but got success=True" in str(exc_info.value)

    def test_validate_error_response_format_missing_fields(self):
        """Test error response missing required fields."""
        response = {
            "success": False,
            "error": "ValidationError",
            # Missing message
        }
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_error_response_format(response)
        assert "Error response missing required fields: ['message']" in str(
            exc_info.value
        )


class TestExtractResponseData:
    """Test response data extraction."""

    def test_extract_response_data_success(self):
        """Test successful data extraction."""
        response = {"success": True, "data": {"id": "test", "title": "Test"}}
        result = extract_response_data(response)
        assert result == {"id": "test", "title": "Test"}

    def test_extract_response_data_error(self):
        """Test data extraction from error response."""
        response = {"success": False, "error": "NotFound", "message": "Story not found"}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            extract_response_data(response)
        assert "Tool execution failed with error" in str(exc_info.value)
        assert "Story not found" in str(exc_info.value)

    def test_extract_response_data_null_data(self):
        """Test data extraction with null data."""
        response = {"success": True, "data": None}
        with pytest.raises(pytest.fail.Exception) as exc_info:
            extract_response_data(response)
        assert "Success response contains null or missing data" in str(exc_info.value)


class TestFullToolResponseValidation:
    """Test complete tool response validation chain."""

    def test_validate_full_tool_response_success(self):
        """Test complete validation of successful tool response."""
        response = json.dumps(
            {
                "success": True,
                "data": {
                    "id": "story-1",
                    "title": "Test Story",
                    "description": "Test description",
                    "acceptance_criteria": ["Criterion 1"],
                    "status": "ToDo",
                    "priority": 1,
                    "created_at": "2025-07-27T10:00:00Z",
                    "epic_id": "epic-1",
                },
            }
        )
        result = validate_full_tool_response(response, StoryResponse)
        assert isinstance(result, StoryResponse)
        assert result.title == "Test Story"

    def test_validate_full_tool_response_error(self):
        """Test complete validation of error tool response."""
        response = json.dumps(
            {"success": False, "error": "ValidationError", "message": "Story not found"}
        )
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_full_tool_response(response)
        assert "Tool execution failed with error" in str(exc_info.value)

    def test_validate_full_tool_response_invalid_json(self):
        """Test complete validation with invalid JSON."""
        response = '{"invalid": json}'
        with pytest.raises(pytest.fail.Exception) as exc_info:
            validate_full_tool_response(response)
        assert "Response is not valid JSON" in str(exc_info.value)
