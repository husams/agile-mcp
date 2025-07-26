# Agile Management MCP Server

A Model Context Protocol (MCP) server for agile project management, providing tools and capabilities for managing sprints, stories, epics, and development workflows.

## Overview

This MCP server enables AI assistants to interact with agile management concepts and workflows through the Model Context Protocol. It provides structured approaches to:

- **Sprint Management**: Planning, tracking, and managing sprint cycles
- **Story Management**: Creating, updating, and tracking user stories
- **Epic Management**: Managing large features and initiatives
- **Backlog Management**: Organizing and prioritizing work items
- **DevOps Integration**: Observability and deployment workflows

## Features

- **Core Service Backlog Management**: Complete backlog lifecycle management
- **Artifact Context Management**: Document and artifact relationship tracking
- **Advanced Story Workflows**: Sophisticated story creation and management
- **DevOps & Observability**: Integration with development and deployment pipelines

## Architecture

Built using FastMCP framework with:
- JSON-RPC 2.0 over stdio transport
- Modular service architecture
- Comprehensive error handling
- Extensible tool framework

## Project Structure

```
agile-mcp/
├── src/agile_mcp/          # Main application code
│   ├── main.py             # Server entry point
│   ├── api/                # API layer
│   ├── services/           # Business logic services
│   └── repositories/       # Data access layer
├── tests/                  # Test suites
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── docs/                   # Documentation
│   ├── architecture/       # Technical architecture docs
│   ├── prd/                # Product requirements
│   └── stories/            # User stories
└── requirements.txt        # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agile-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python src/agile_mcp/main.py
```

## Usage

This server is designed to be used with MCP-compatible AI assistants. Once running, it provides tools and capabilities that can be invoked through the MCP protocol.

### As an MCP Server

The server communicates via JSON-RPC over stdin/stdout, making it compatible with any MCP client.

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test types
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/
```

### Architecture Documentation

See the `docs/architecture/` directory for detailed technical documentation including:
- High-level architecture overview
- Data models and schemas
- Error handling strategy
- Testing strategy
- Technology stack decisions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

- [Product Requirements Document](docs/prd.md)
- [Architecture Overview](docs/architecture.md)
- [Epic Breakdown](docs/prd/epic-list.md)
- [User Stories](docs/stories/)

## License

[Add your license here]

## Contact

[Add contact information]
