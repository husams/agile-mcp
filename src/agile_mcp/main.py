#!/usr/bin/env python3
"""
Agile Management MCP Server - Main Entry Point

This module serves as the primary entry point for the Agile Management MCP Server.
It initializes the FastMCP server instance and handles MCP protocol communications.
"""

import asyncio
import logging
import sys
from typing import Optional

from fastmcp import FastMCP

# Configure logging to stderr to avoid contaminating stdout JSON-RPC
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


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
        server = FastMCP("Agile Management Server")
        logger.info("FastMCP server instance created successfully")
        
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


async def main() -> None:
    """
    Main entry point for the Agile Management MCP Server.
    
    Sets up the server and runs it with stdio transport for MCP communication.
    """
    server: Optional[FastMCP] = None
    
    try:
        logger.info("Starting Agile Management MCP Server")
        
        # Create server instance
        server = create_server()
        
        # Run server with stdio transport (JSON-RPC over stdin/stdout)
        logger.info("Starting server with stdio transport")
        await server.run(transport="stdio")
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested via keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        if server:
            logger.info("Server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())