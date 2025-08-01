#!/usr/bin/env python3
"""Agile Management MCP Server - Main Entry Point.

This module serves as the primary entry point for the Agile Management MCP Server.
It initializes the FastMCP server instance and handles MCP protocol communications.
"""

import sys
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

try:
    from .api import (
        register_artifact_tools,
        register_backlog_tools,
        register_comment_tools,
        register_document_tools,
        register_epic_tools,
        register_project_tools,
        register_story_tools,
    )
    from .utils.logging_config import configure_logging, get_logger
except ImportError:  # type: ignore
    # Handle when running as script directly
    import os

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from api import register_artifact_tools  # type: ignore
    from api import (
        register_backlog_tools,
        register_comment_tools,
        register_document_tools,
        register_epic_tools,
        register_project_tools,
        register_story_tools,
    )
    from utils.logging_config import configure_logging, get_logger  # type: ignore

# Configure structured logging
configure_logging(log_level="INFO", enable_json=True)
logger = get_logger(__name__)


def create_server() -> FastMCP:
    """
    Create and configure the FastMCP server instance.

    Returns:
        FastMCP: Configured server instance with capabilities

    Raises:
        Exception: If server creation fails
    """
    try:
        # Initialize FastMCP server with proper configuration
        server: FastMCP = FastMCP("Agile Management Server")
        logger.info("FastMCP server instance created successfully")

        # Register project management tools
        register_project_tools(server)
        logger.info("Project management tools registered successfully")

        # Register epic management tools
        register_epic_tools(server)
        logger.info("Epic management tools registered successfully")

        # Register story management tools
        register_story_tools(server)
        logger.info("Story management tools registered successfully")

        # Register comment management tools
        register_comment_tools(server)
        logger.info("Comment management tools registered successfully")

        # Register artifact management tools
        register_artifact_tools(server)
        logger.info("Artifact management tools registered successfully")

        # Register backlog management tools
        register_backlog_tools(server)
        logger.info("Backlog management tools registered successfully")

        # Register document management tools
        register_document_tools(server)
        logger.info("Document management tools registered successfully")

        # FastMCP automatically handles:
        # - MCP initialize request handling
        # - Capabilities response with tool support declaration
        # - JSON-RPC 2.0 compliance
        # - Session establishment and maintenance
        # - Error handling for initialization failures

        return server
    except Exception as e:
        logger.error(f"Failed to create FastMCP server: {e}")
        raise


def main() -> None:
    """Run the Agile Management MCP Server.

    Sets up the server and runs it with stdio transport for MCP communication.
    """
    # Load environment variables from .env file
    load_dotenv()
    server: Optional[FastMCP] = None

    try:
        logger.info("Starting Agile Management MCP Server")

        # Create server instance
        server = create_server()

        # Run server with stdio transport (JSON-RPC over stdin/stdout)
        logger.info("Starting server with stdio transport")
        server.run(transport="stdio")

    except KeyboardInterrupt:
        logger.info("Server shutdown requested via keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        if server:
            logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()
