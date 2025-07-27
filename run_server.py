#!/usr/bin/env python3
"""
Entry point script for running the Agile Management MCP Server.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the server
from agile_mcp.main import main

if __name__ == "__main__":
    main()