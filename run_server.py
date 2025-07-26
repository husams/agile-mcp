#!/usr/bin/env python3
"""
Entry point script for running the Agile Management MCP Server.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the server
from agile_mcp.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Already running asyncio in this thread" in str(e):
            # Get the current event loop and run the main function
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise