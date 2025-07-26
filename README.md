# Agile MCP Server

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

## Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd agile-mcp
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MCP client:** Add this server to your MCP client configuration

### Usage

This MCP server provides tools and resources for:
- Managing agile backlogs and user stories
- Tracking development artifacts and their relationships
- Implementing structured agile workflows

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

- [Product Requirements Document](docs/prd.md)
- [Architecture Overview](docs/architecture.md)
- [User Stories](docs/stories/)
- [MCP Protocol Documentation](docs/mcp/)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on our development process.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.