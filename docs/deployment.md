# Agile MCP Server - Deployment Guide

## Overview

The Agile Management MCP Server is designed to run locally as a standalone process that communicates with AI agents via the Model Context Protocol (MCP). This guide provides comprehensive instructions for setting up and deploying the server in different environments.

## Prerequisites

### System Requirements
- **Python**: 3.11 or 3.12
- **Operating System**: macOS, Linux, or Windows
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB free disk space
- **Network**: Local network access (no external connections required)

### Required Tools
- Git (for source code management)
- Python pip (package manager)
- Virtual environment tool (venv, conda, or virtualenv)

## Quick Start Deployment

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd agile-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Initialization
```bash
# The database will be automatically created on first run
# Default location: ./agile_mcp.db (SQLite)

# To initialize with custom database location:
export DATABASE_URL="sqlite:///path/to/your/database.db"
```

### 3. Start the Server
```bash
# Start the MCP server
python run_server.py

# Server will start and listen for MCP connections via stdio
# Output: "Starting Agile Management MCP Server"
```

## Environment Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | `sqlite:///agile_mcp.db` | No |
| `TEST_DATABASE_URL` | Test database (for testing only) | `:memory:` | No |
| `MCP_TEST_MODE` | Enable test mode | `false` | No |
| `SQL_DEBUG` | Enable SQL query logging | `false` | No |

### Configuration Examples

#### Development Environment
```bash
export DATABASE_URL="sqlite:///dev_agile_mcp.db"
export SQL_DEBUG="true"
python run_server.py
```

#### Production Environment
```bash
export DATABASE_URL="sqlite:///prod_agile_mcp.db"
export SQL_DEBUG="false"
python run_server.py
```

#### Testing Environment
```bash
export TEST_DATABASE_URL="sqlite:///:memory:"
export MCP_TEST_MODE="true"
pytest
```

## Database Setup

### SQLite (Default)
The server uses SQLite by default, which requires no additional setup:

```bash
# Database file will be created automatically
# Location: ./agile_mcp.db
# No additional configuration needed
```

### Custom Database Location
```bash
# Specify custom database file location
export DATABASE_URL="sqlite:///path/to/custom/database.db"

# Ensure directory exists
mkdir -p /path/to/custom/
python run_server.py
```

### Database Schema Initialization
The database schema is automatically created on first startup:

```python
# Tables created automatically:
# - epics (Epic entities)
# - stories (Story entities with Epic relationships)
# - artifacts (Artifact entities linked to Stories)
# - story_dependencies (Story dependency relationships)
```

## Server Architecture

### Process Model
- **Single Process**: Monolithic server design
- **Communication**: JSON-RPC over stdio (MCP protocol)
- **Database**: SQLite with SQLAlchemy ORM
- **Concurrency**: Single-threaded with async support

### Port and Network
- **No Network Ports**: Server communicates via stdin/stdout
- **Local Only**: No external network dependencies
- **Security**: Process-level isolation

### File Structure
```
agile-mcp/
├── run_server.py          # Server entry point
├── src/agile_mcp/
│   ├── main.py           # Server initialization
│   ├── database.py       # Database configuration
│   ├── api/              # MCP tool definitions
│   ├── services/         # Business logic
│   ├── models/           # Data models
│   └── utils/            # Utilities and logging
├── tests/                # Test suite
├── docs/                 # Documentation
└── agile_mcp.db         # SQLite database (created at runtime)
```

## Integration with AI Agents

### MCP Client Connection
The server implements the Model Context Protocol (MCP) for AI agent communication:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    }
  }
}
```

### Available Tools
The server provides these MCP tools for AI agents:

- **Epic Management**: `epics.create`, `epics.find`, `epics.updateStatus`
- **Story Management**: `stories.create`, `stories.get`, `stories.updateStatus`
- **Artifact Management**: `artifacts.linkToStory`, `artifacts.listForStory`
- **Backlog Management**: `backlog.getNextReadyStory`, `backlog.addDependency`

### Client Integration Example
```python
# Example MCP client connection (pseudocode)
import json
import subprocess

# Start server process
process = subprocess.Popen(
    ['python', 'run_server.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send MCP initialize request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2024-11-05"}
}
process.stdin.write(json.dumps(request) + '\n')
```

## Monitoring and Logging

### Structured Logging
The server implements structured JSON logging:

```python
# Log configuration in utils/logging_config.py
# Logs include: timestamp, level, message, context
# Output format: JSON for production, human-readable for development
```

### Log Levels
- **INFO**: Server startup, tool registrations, normal operations
- **ERROR**: Tool execution failures, database errors
- **DEBUG**: Detailed operation traces (when SQL_DEBUG=true)

### Log Output Example
```json
{
  "timestamp": "2025-07-28T10:30:00Z",
  "level": "INFO",
  "message": "FastMCP server instance created successfully",
  "module": "agile_mcp.main"
}
```

### Monitoring Health
```bash
# Check server process
ps aux | grep "python run_server.py"

# Check database file
ls -la agile_mcp.db

# Check logs (if redirected to file)
tail -f server.log
```

## Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep -E "(fastmcp|sqlalchemy|pydantic)"

# Check database permissions
ls -la ./agile_mcp.db

# Run with debug logging
export SQL_DEBUG="true"
python run_server.py
```

#### Database Connection Issues
```bash
# Check database file exists and is writable
touch agile_mcp.db
ls -la agile_mcp.db

# Test with in-memory database
export DATABASE_URL="sqlite:///:memory:"
python run_server.py

# Check SQLite installation
python -c "import sqlite3; print(sqlite3.version)"
```

#### MCP Communication Issues
```bash
# Test server initialization manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' | python run_server.py

# Check stdin/stdout are not redirected
# Server must communicate via stdio for MCP protocol
```

#### Performance Issues
```bash
# Check database size
du -h agile_mcp.db

# Run performance tests
pytest tests/unit/ --benchmark

# Check memory usage
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f "python run_server.py")
```

### Debug Mode
```bash
# Enable comprehensive debugging
export SQL_DEBUG="true"
export MCP_TEST_MODE="true"
python run_server.py 2>&1 | tee debug.log
```

### Support Contacts
- **Technical Issues**: Check GitHub issues
- **Documentation**: Refer to `docs/` directory
- **Architecture Questions**: See `docs/architecture/`

## Security Considerations

### Process Security
- Server runs as local user process
- No elevated privileges required
- No network exposure (stdio communication only)

### Data Security
- SQLite database stored locally
- No external data transmission
- File system permissions control access

### Input Validation
- All MCP tool inputs validated via Pydantic models
- SQL injection prevention through SQLAlchemy ORM
- Error handling prevents information leakage

## Performance Optimization

### Database Performance
```bash
# Optimize SQLite for performance
export DATABASE_URL="sqlite:///agile_mcp.db?cache=shared&journal_mode=WAL"
```

### Memory Management
- Server uses minimal memory footprint
- Database connection pooling via SQLAlchemy
- Automatic garbage collection for Python objects

### Concurrent Access
```bash
# Multiple AI agents can connect simultaneously
# SQLite handles concurrent reads automatically
# Write operations are serialized by SQLite
```

## Backup and Recovery

### Database Backup
```bash
# Simple file copy (when server is stopped)
cp agile_mcp.db agile_mcp_backup_$(date +%Y%m%d).db

# Online backup (while server running)
sqlite3 agile_mcp.db ".backup backup.db"
```

### Recovery Procedure
```bash
# Restore from backup
cp agile_mcp_backup_20250728.db agile_mcp.db

# Verify database integrity
sqlite3 agile_mcp.db "PRAGMA integrity_check;"
```

### Disaster Recovery
1. Stop the server process
2. Restore database from latest backup
3. Verify database integrity
4. Restart server
5. Test basic functionality with simple MCP calls

This deployment guide ensures reliable, secure installation and operation of the Agile MCP Server in any local environment.
