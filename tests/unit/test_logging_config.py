"""
Unit tests for structured logging configuration.
"""

import json
from io import StringIO
from unittest.mock import patch

import pytest
import structlog

from src.agile_mcp.utils.logging_config import (
    configure_logging,
    create_entity_context,
    create_request_context,
    get_logger,
)


class TestLoggingConfiguration:
    """Test logging configuration functionality."""

    def test_configure_logging_with_json_output(self):
        """Test that configure_logging sets up JSON output correctly."""
        # Configure logging with JSON output
        configure_logging(log_level="DEBUG", enable_json=True)

        # Get a logger and verify it's properly configured
        logger = get_logger("test_logger")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    def test_configure_logging_with_different_log_levels(self):
        """Test configuration with different log levels."""
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in log_levels:
            configure_logging(log_level=level, enable_json=True)
            logger = get_logger(f"test_logger_{level}")
            assert logger is not None

    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a properly bound structlog logger."""
        configure_logging()
        logger = get_logger("test_module")

        # Verify it's a structlog BoundLogger
        assert isinstance(logger, structlog.stdlib.BoundLogger)

    def test_create_request_context(self):
        """Test request context creation."""
        # Test with all parameters
        context = create_request_context(
            request_id="test-123", tool_name="test.tool", custom_field="value"
        )

        expected = {
            "request_id": "test-123",
            "tool_name": "test.tool",
            "custom_field": "value",
        }
        assert context == expected

        # Test with minimal parameters
        context = create_request_context()
        assert context == {}

        # Test with only request_id
        context = create_request_context(request_id="test-456")
        assert context == {"request_id": "test-456"}

    def test_create_entity_context(self):
        """Test entity context creation."""
        # Test with all parameters
        context = create_entity_context(
            story_id="story-123",
            epic_id="epic-456",
            artifact_id="artifact-789",
            custom_field="value",
        )

        expected = {
            "story_id": "story-123",
            "epic_id": "epic-456",
            "artifact_id": "artifact-789",
            "custom_field": "value",
        }
        assert context == expected

        # Test with minimal parameters
        context = create_entity_context()
        assert context == {}

        # Test with only story_id
        context = create_entity_context(story_id="story-789")
        assert context == {"story_id": "story-789"}

    @patch("sys.stderr", new_callable=StringIO)
    def test_json_log_output_format(self, mock_stderr):
        """Test that logs are output in JSON format to stderr."""
        configure_logging(log_level="INFO", enable_json=True)
        logger = get_logger("test_json_output")

        # Log a test message with context
        logger.info(
            "Test log message",
            **create_request_context(request_id="test-json-123", tool_name="test.tool"),
            **create_entity_context(story_id="story-456"),
            operation="test_operation",
        )

        # Get the log output
        log_output = mock_stderr.getvalue().strip()

        # Verify it's valid JSON
        try:
            log_data = json.loads(log_output)
        except json.JSONDecodeError:
            pytest.fail(f"Log output is not valid JSON: {log_output}")

        # Verify required fields are present
        assert "event" in log_data
        assert "timestamp" in log_data
        assert "level" in log_data
        assert "logger" in log_data

        # Verify our custom fields are present
        assert log_data["event"] == "Test log message"
        assert log_data["request_id"] == "test-json-123"
        assert log_data["tool_name"] == "test.tool"
        assert log_data["story_id"] == "story-456"
        assert log_data["operation"] == "test_operation"

    def test_logger_preserves_context_between_calls(self):
        """Test that logger context is preserved correctly."""
        configure_logging()
        logger = get_logger("test_context")

        # This is more of a smoke test since structlog handles context binding
        # We're mainly testing that multiple calls don't interfere with each other
        logger.info("First message", context="first")
        logger.info("Second message", context="second")

        # If we get here without errors, the test passes
        assert True

    def test_configure_logging_multiple_times(self):
        """Test that configure_logging can be called multiple times safely."""
        # First configuration
        configure_logging(log_level="INFO", enable_json=True)
        logger1 = get_logger("test_multiple_1")

        # Second configuration
        configure_logging(log_level="DEBUG", enable_json=False)
        logger2 = get_logger("test_multiple_2")

        # Both loggers should work
        assert logger1 is not None
        assert logger2 is not None


class TestLoggingIntegration:
    """Test logging integration with service components."""

    @patch("sys.stderr", new_callable=StringIO)
    def test_service_layer_logging_format(self, mock_stderr):
        """Test that service layer logging produces expected format."""
        configure_logging(log_level="INFO", enable_json=True)
        logger = get_logger("test_service")

        # Simulate service layer logging
        logger.info(
            "Story created successfully",
            **create_entity_context(story_id="story-123", epic_id="epic-456"),
            title="Test Story",
            status="ToDo",
            operation="create_story",
        )

        log_output = mock_stderr.getvalue().strip()
        log_data = json.loads(log_output)

        # Verify service-specific fields
        assert log_data["story_id"] == "story-123"
        assert log_data["epic_id"] == "epic-456"
        assert log_data["title"] == "Test Story"
        assert log_data["status"] == "ToDo"
        assert log_data["operation"] == "create_story"

    @patch("sys.stderr", new_callable=StringIO)
    def test_api_layer_error_logging_format(self, mock_stderr):
        """Test that API layer error logging produces expected format."""
        configure_logging(log_level="ERROR", enable_json=True)
        logger = get_logger("test_api")

        # Simulate API layer error logging
        logger.error(
            "Story validation error in create story",
            **create_request_context(
                request_id="req-789", tool_name="backlog.createStory"
            ),
            **create_entity_context(epic_id="epic-456"),
            error_type="StoryValidationError",
            error_message="Story title cannot be empty",
            mcp_error_code=-32001,
        )

        log_output = mock_stderr.getvalue().strip()
        log_data = json.loads(log_output)

        # Verify API error-specific fields
        assert log_data["request_id"] == "req-789"
        assert log_data["tool_name"] == "backlog.createStory"
        assert log_data["epic_id"] == "epic-456"
        assert log_data["error_type"] == "StoryValidationError"
        assert log_data["error_message"] == "Story title cannot be empty"
        assert log_data["mcp_error_code"] == -32001

    def test_logging_does_not_interfere_with_stdout(self):
        """Test that logging goes to stderr and doesn't interfere with stdout."""
        configure_logging(log_level="INFO", enable_json=True)
        logger = get_logger("test_stdout")

        # Capture both stdout and stderr
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout, patch(
            "sys.stderr", new_callable=StringIO
        ) as mock_stderr:

            # Log a message
            logger.info("Test message for stdout check")

            # Write something to stdout (simulating MCP JSON-RPC)
            print('{"jsonrpc": "2.0", "method": "test"}')

            # Verify stdout only contains our print statement
            stdout_content = mock_stdout.getvalue()
            assert '{"jsonrpc": "2.0", "method": "test"}' in stdout_content
            assert "Test message for stdout check" not in stdout_content

            # Verify stderr contains our log message
            stderr_content = mock_stderr.getvalue()
            assert "Test message for stdout check" in stderr_content


class TestLoggingErrorHandling:
    """Test error handling in logging configuration."""

    def test_get_logger_with_empty_name(self):
        """Test get_logger with empty name."""
        configure_logging()
        logger = get_logger("")
        assert logger is not None

    def test_create_request_context_with_none_values(self):
        """Test create_request_context handles None values correctly."""
        context = create_request_context(
            request_id=None, tool_name=None, valid_field="value"
        )

        # None values should not be included
        expected = {"valid_field": "value"}
        assert context == expected

    def test_create_entity_context_with_none_values(self):
        """Test create_entity_context handles None values correctly."""
        context = create_entity_context(
            story_id=None, epic_id="epic-123", artifact_id=None, valid_field="value"
        )

        # None values should not be included
        expected = {"epic_id": "epic-123", "valid_field": "value"}
        assert context == expected

    def test_configure_logging_with_invalid_log_level(self):
        """Test configure_logging with invalid log level."""
        # This should not raise an exception, but use a default
        try:
            configure_logging(log_level="INVALID_LEVEL")
            logger = get_logger("test_invalid_level")
            logger.info("Test message")
        except Exception as e:
            pytest.fail(
                f"configure_logging should handle invalid log levels gracefully: {e}"
            )
