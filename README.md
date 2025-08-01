# Agile MCP Server

[![CI Pipeline](https://github.com/[USERNAME]/agile-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/[USERNAME]/agile-mcp/actions/workflows/ci.yml)

A Model Context Protocol (MCP) server that provides AI agents with structured tools for agile software development lifecycle management. This server enables AI assistants to autonomously manage backlogs, retrieve task-relevant information, and track generated artifacts in a structured, context-aware manner.

## Overview

The Agile MCP Server addresses the need for a specialized tooling layer in AI-augmented development. Unlike traditional user-facing project management UIs, this MCP server provides granular, programmatic access to agile development processes that AI agents can interact with directly.

## Key Features

- **Backlog Management**: Create, update, and organize user stories, epics, and tasks
- **Artifact Tracking**: Maintain context and relationships between generated development artifacts
- **Story Workflows**: Advanced workflow management for user story lifecycle
- **MCP Protocol**: Built on the Model Context Protocol standard for reliable agent-service communication

## Architecture

This server implements the Model Context Protocol (MCP) specification, providing:
- Structured resource access for development artifacts
- Tool-based operations for backlog management
- Secure and predictable agent-service interactions

## Version Information

**Current Version**: 2.0.0

**⚠️ Breaking Changes in v2.0.0**: All tool names have been updated to use underscore-based naming for better MCP protocol compliance. See the [Migration Guide](MIGRATION-GUIDE.md) for complete details on updating from v1.x.

## Getting Started

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:husams/agile-mcp.git
   cd agile-mcp
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Configure MCP Client:**

   This MCP server uses **stdio transport** and must be configured in an MCP client (like Claude Desktop). It cannot run as a standalone process.

   **For Claude Desktop**, add to your `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "agile-mcp": {
         "command": "uv",
         "args": ["run", "run_server.py"],
         "cwd": "/path/to/agile-mcp"
       }
     }
   }
   ```

   **For other MCP clients:**
   - **Transport**: stdio
   - **Command**: `uv run run_server.py`
   - **Working Directory**: Project root path

### Usage

This MCP server provides tools and resources for:
- Managing agile backlogs and user stories
- Tracking development artifacts and their relationships
- Implementing structured agile workflows

#### Server Operation

Once configured in your MCP client, the server will automatically start when the client initializes. The server communicates via JSON-RPC over stdin/stdout as specified by the MCP protocol standard.


## Project Structure

```
agile-mcp/
├── src/agile_mcp/          # Main server implementation
│   ├── main.py             # Server entry point
│   ├── api/                # API endpoints and handlers
│   ├── repositories/       # Data access layer
│   └── services/           # Business logic
├── docs/                   # Project documentation
│   ├── prd.md              # Product Requirements Document
│   ├── architecture/       # Architecture documentation
│   ├── prd/                # Detailed PRD sections
│   └── stories/            # User story documentation
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
└── requirements.txt        # Python dependencies
```

## Documentation

- **[Migration Guide](MIGRATION-GUIDE.md)** - Complete guide for migrating from v1.x to v2.0
- **[Changelog](CHANGELOG.md)** - Version history and breaking changes
- [Available Tools](docs/tools.md) - Complete list of MCP tools and their usage
- [Product Requirements Document](docs/prd.md)
- [Architecture Overview](docs/architecture.md)
- [Configuration Management](docs/configuration.md)
- [Coding Guidelines and Conventions](docs/coding_guidelines.md)
- [Technical Debt Management](docs/technical_debt.md)
- [User Stories](docs/stories/)
- [MCP Protocol Documentation](docs/mcp/)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on our development process.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
