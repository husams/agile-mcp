import json
from datetime import datetime

import pytest

from src.agile_mcp.utils.mcp_response import MCPResponse


class TestMCPResponse:
    """Test suite for MCPResponse utility class."""

    def test_success_response_basic(self):
        """Test basic success response formatting."""
        result = MCPResponse.success()
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["message"] == "Operation completed successfully"
        assert parsed["data"] is None

    def test_success_response_with_data(self):
        """Test success response with data."""
        test_data = {"story_id": "TEST-001", "depends_on": "TEST-002"}
        result = MCPResponse.success(test_data, "Dependency added successfully")
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert parsed["message"] == "Dependency added successfully"
        assert parsed["data"] == test_data

    def test_success_response_with_datetime(self):
        """Test success response with datetime serialization."""
        test_data = {"created_at": datetime.now()}
        result = MCPResponse.success(test_data)
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert isinstance(parsed["data"]["created_at"], str)

    def test_error_response_basic(self):
        """Test basic error response formatting."""
        result = MCPResponse.error("test_error", "Test error message")
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert parsed["error"] == "test_error"
        assert parsed["message"] == "Test error message"
        assert "details" not in parsed

    def test_error_response_with_details(self):
        """Test error response with details."""
        details = {"story_id": "TEST-001", "invalid_field": "value"}
        result = MCPResponse.error("validation_error", "Invalid data", details)
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert parsed["error"] == "validation_error"
        assert parsed["message"] == "Invalid data"
        assert parsed["details"] == details

    def test_circular_dependency_error(self):
        """Test circular dependency error format."""
        details = {"story_id": "A", "depends_on_story_id": "B"}
        result = MCPResponse.error(
            "circular_dependency", "Circular dependency detected", details
        )
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert parsed["error"] == "circular_dependency"
        assert parsed["message"] == "Circular dependency detected"
        assert parsed["details"] == details

    def test_story_not_found_error(self):
        """Test story not found error format."""
        result = MCPResponse.error("story_not_found", "Story TEST-999 not found")
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert parsed["error"] == "story_not_found"
        assert parsed["message"] == "Story TEST-999 not found"

    def test_json_validity(self):
        """Test that all responses produce valid JSON."""
        # Test various data types
        test_cases = [
            MCPResponse.success({"key": "value"}),
            MCPResponse.success([1, 2, 3]),
            MCPResponse.success("simple string"),
            MCPResponse.success(42),
            MCPResponse.error("error", "message"),
            MCPResponse.error("error", "message", {"detail": "value"}),
        ]

        for response in test_cases:
            # Should not raise JSONDecodeError
            parsed = json.loads(response)
            assert isinstance(parsed, dict)
            assert "success" in parsed
