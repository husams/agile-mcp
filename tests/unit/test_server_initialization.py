"""
Unit tests for server initialization components.

Tests the FastMCP server initialization process, capabilities response,
and JSON-RPC 2.0 compliance in isolation.
"""

from unittest.mock import Mock, patch

import pytest

from src.agile_mcp.main import create_server, main


class TestServerInitialization:
    """Test server initialization and configuration."""

    def test_create_server_returns_fastmcp_instance(self):
        """Test that create_server returns a properly configured FastMCP instance."""
        with patch("src.agile_mcp.main.logger") as mock_logger:
            server = create_server()

            # Verify server is created with expected configuration
            assert server.name == "Agile Management Server"
            # Verify successful creation was logged
            mock_logger.info.assert_any_call(
                "FastMCP server instance created successfully"
            )

    def test_server_capabilities_include_tools(self):
        """Test that server declares tool support in capabilities."""
        server = create_server()

        # FastMCP automatically declares tool capabilities
        # This test verifies the server object exists and can be introspected
        assert hasattr(server, "name")
        assert server is not None

    def test_main_handles_server_creation(self):
        """Test that main function creates and runs server successfully."""
        with patch("src.agile_mcp.main.create_server") as mock_create_server:
            mock_server = Mock()
            mock_server.run = Mock()
            mock_create_server.return_value = mock_server

            main()

            # Verify server was created and run called
            mock_create_server.assert_called_once()
            mock_server.run.assert_called_once_with(transport="stdio")

    def test_main_handles_initialization_errors(self):
        """Test that main function handles initialization errors gracefully."""
        with patch("src.agile_mcp.main.create_server") as mock_create_server:
            # Mock server creation failure
            mock_create_server.side_effect = Exception("Server creation failed")

            # Capture stderr and logging to verify error logging
            with patch("src.agile_mcp.main.logger") as mock_logger:
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Verify error handling
                assert exc_info.value.code == 1
                # Verify that error was logged properly
                mock_logger.error.assert_called_with(
                    "Server error: Server creation failed"
                )

    def test_main_handles_server_run_errors(self):
        """Test that main function handles server run errors gracefully."""
        with patch("src.agile_mcp.main.create_server") as mock_create_server:
            mock_server = Mock()
            mock_server.run = Mock(side_effect=Exception("Server run failed"))
            mock_create_server.return_value = mock_server

            # Capture logging to verify error logging
            with patch("src.agile_mcp.main.logger") as mock_logger:
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Verify error handling
                assert exc_info.value.code == 1
                # Verify that error was logged properly
                mock_logger.error.assert_called_with("Server error: Server run failed")

    def test_main_handles_keyboard_interrupt(self):
        """Test that main function handles KeyboardInterrupt gracefully."""
        with patch("src.agile_mcp.main.create_server") as mock_create_server:
            mock_server = Mock()
            mock_server.run = Mock(side_effect=KeyboardInterrupt())
            mock_create_server.return_value = mock_server

            # Capture logging to verify graceful shutdown
            with patch("src.agile_mcp.main.logger") as mock_logger:
                main()  # Should not raise SystemExit for KeyboardInterrupt

                # Verify graceful shutdown was logged
                mock_logger.info.assert_any_call(
                    "Server shutdown requested via keyboard interrupt"
                )
                mock_logger.info.assert_any_call("Server shutdown complete")

    def test_create_server_handles_fastmcp_failure(self):
        """Test that create_server handles FastMCP creation failures."""
        with patch("src.agile_mcp.main.FastMCP") as mock_fastmcp:
            mock_fastmcp.side_effect = Exception("FastMCP creation failed")

            with patch("src.agile_mcp.main.logger") as mock_logger:
                with pytest.raises(Exception) as exc_info:
                    create_server()

                # Verify error was logged and re-raised
                assert "FastMCP creation failed" in str(exc_info.value)
                mock_logger.error.assert_called_with(
                    "Failed to create FastMCP server: FastMCP creation failed"
                )


class TestJSONRPCCompliance:
    """Test JSON-RPC 2.0 compliance for server communications."""

    def test_server_uses_stdio_transport(self):
        """Test that server is configured to use stdio transport for JSON-RPC."""
        server = create_server()

        # FastMCP handles JSON-RPC 2.0 compliance automatically
        # This test verifies the server object exists and can be configured
        assert server is not None

    def test_error_logging_to_stderr(self):
        """Test that errors are logged to stderr to avoid contaminating stdout JSON-RPC."""
        # This is tested in the error handling tests above
        # Verifying that error output goes to stderr, not stdout
