# Agile MCP Server - Configuration Management

## Overview

The Agile Management MCP Server uses environment-based configuration to support different deployment scenarios while maintaining security and flexibility. Configuration is managed through environment variables with sensible defaults for immediate usability.

## Configuration Architecture

### Current Implementation
Configuration is handled directly in `src/agile_mcp/database.py` and other modules using environment variables:

```python
# src/agile_mcp/database.py
DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///agile_mcp.db")
```

### Design Principles
- **Environment-First**: All configuration through environment variables
- **Secure Defaults**: Safe default values for immediate use
- **Environment Isolation**: Clear separation between development, testing, and production
- **No Secrets in Code**: Sensitive information only via environment variables

## Environment Variables Reference

### Core Database Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATABASE_URL` | Primary database connection string | `sqlite:///agile_mcp.db` | `sqlite:///prod_agile_mcp.db` |
| `TEST_DATABASE_URL` | Test database connection (testing only) | Used when set | `sqlite:///:memory:` |

### Logging Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SQL_DEBUG` | Enable SQL query logging | `false` | `true` |
| `LOG_LEVEL` | Application log level | `INFO` | `DEBUG`, `WARNING`, `ERROR` |

### Testing Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MCP_TEST_MODE` | Enable test mode for E2E tests | `false` | `true` |
| `PYTEST_PARALLEL` | Enable parallel test execution | `false` | `true` |

## Environment-Specific Configurations

### Development Environment

**Purpose**: Local development with debugging enabled

```bash
# Development configuration
export DATABASE_URL="sqlite:///dev_agile_mcp.db"
export SQL_DEBUG="true"
export LOG_LEVEL="DEBUG"

# Configure in MCP client (e.g., Claude Desktop)
# The server will be started by the MCP client via stdio transport
```

**Characteristics**:
- Detailed SQL query logging
- Debug-level application logs
- Separate development database
- Fast restart capability

### Testing Environment

**Purpose**: Automated testing with isolation

```bash
# Testing configuration
export TEST_DATABASE_URL="sqlite:///:memory:"
export MCP_TEST_MODE="true"
export SQL_DEBUG="false"

# Run test suite
pytest
```

**Characteristics**:
- In-memory database for speed
- Test-specific environment detection
- Minimal logging for clean test output
- Complete database isolation

### Production Environment

**Purpose**: Stable production deployment

```bash
# Production configuration
export DATABASE_URL="sqlite:///prod_agile_mcp.db"
export SQL_DEBUG="false"
export LOG_LEVEL="INFO"

# Configure in MCP client production deployment
# The server runs via stdio transport managed by MCP client
```

**Characteristics**:
- Persistent database storage
- Structured JSON logging
- Error-level logging only
- Performance-optimized settings

## Database Configuration Options

### SQLite Configuration (Default)

**Basic SQLite**:
```bash
export DATABASE_URL="sqlite:///agile_mcp.db"
```

**SQLite with Performance Optimization**:
```bash
export DATABASE_URL="sqlite:///agile_mcp.db?cache=shared&journal_mode=WAL"
```

**SQLite In-Memory (Testing)**:
```bash
export DATABASE_URL="sqlite:///:memory:"
```

### Future Database Support

The system is designed to support multiple database backends:

**PostgreSQL (Future)**:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/agile_mcp"
```

**MongoDB (Future)**:
```bash
export DATABASE_URL="mongodb://localhost:27017/agile_mcp"
```

## Configuration Management Patterns

### Environment File Usage

**Development .env file** (not committed to repository):
```bash
# .env.development
DATABASE_URL=sqlite:///dev_agile_mcp.db
SQL_DEBUG=true
LOG_LEVEL=DEBUG
```

**Production .env file**:
```bash
# .env.production
DATABASE_URL=sqlite:///prod_agile_mcp.db
SQL_DEBUG=false
LOG_LEVEL=INFO
```

### Shell Script Configuration

**Development environment setup**:
```bash
#!/bin/bash
# dev-env.sh - Set development environment variables
export DATABASE_URL="sqlite:///dev_agile_mcp.db"
export SQL_DEBUG="true"
export LOG_LEVEL="DEBUG"
# Server will be started by MCP client using stdio transport
echo "Development environment configured for MCP server"
```

**Production environment setup**:
```bash
#!/bin/bash
# prod-env.sh - Set production environment variables
export DATABASE_URL="sqlite:///prod_agile_mcp.db"
export SQL_DEBUG="false"
export LOG_LEVEL="INFO"
# Server will be started by MCP client using stdio transport
echo "Production environment configured for MCP server"
```

## MCP Client Configuration

This server uses **stdio transport** and must be configured in an MCP client. It cannot run standalone.

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agile-mcp": {
      "command": "uv",
      "args": ["run", "run_server.py"],
      "cwd": "/path/to/agile-mcp",
      "env": {
        "DATABASE_URL": "sqlite:///agile_mcp.db",
        "LOG_LEVEL": "INFO",
        "SQL_DEBUG": "false"
      }
    }
  }
}
```

### Generic MCP Client Configuration

For other MCP clients, use these settings:
- **Transport**: stdio
- **Command**: `uv run run_server.py`
- **Working Directory**: Project root path
- **Environment Variables**: As defined in previous sections

## Security Configuration

### Sensitive Information Handling

**Principles**:
- Never commit sensitive values to repository
- Use environment variables for all credentials
- Implement secure defaults
- Log configuration without exposing secrets

**Database Security**:
```bash
# Secure database file permissions
chmod 600 agile_mcp.db

# Environment variable for sensitive database URL
export DATABASE_URL="sqlite:///secure/path/agile_mcp.db"
```

**Logging Security**:
```python
# Logging configuration automatically sanitizes sensitive data
# Database URLs and credentials are not logged in full
```

### Environment Validation

The system validates configuration on startup:

```python
# Configuration validation (conceptual)
def validate_config():
    database_url = os.getenv("DATABASE_URL", "sqlite:///agile_mcp.db")
    if not database_url:
        raise ValueError("DATABASE_URL must be configured")

    # Additional validation as needed
    return True
```

## Configuration Troubleshooting

### Common Configuration Issues

**Database Connection Problems**:
```bash
# Check current configuration
echo $DATABASE_URL

# Test database accessibility
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///agile_mcp.db'))
print('Database connection successful')
"
```

**Environment Variable Issues**:
```bash
# List all environment variables
env | grep -E "(DATABASE|SQL|LOG|MCP)"

# Clear conflicting variables
unset TEST_DATABASE_URL
unset MCP_TEST_MODE
```

**Permission Issues**:
```bash
# Check database file permissions
ls -la agile_mcp.db

# Fix permissions if needed
chmod 644 agile_mcp.db
```

### Debug Configuration

**Verbose configuration debugging**:
```bash
# Enable all debugging
export SQL_DEBUG="true"
export LOG_LEVEL="DEBUG"
export MCP_TEST_MODE="true"

# Show configuration on startup
python -c "
import os
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
print('SQL_DEBUG:', os.getenv('SQL_DEBUG'))
print('LOG_LEVEL:', os.getenv('LOG_LEVEL'))
"
```

## Configuration Best Practices

### Development Workflow
1. Use separate databases for development and testing
2. Enable debug logging during development
3. Test configuration changes in isolation
4. Document environment-specific requirements

### Production Deployment
1. Use production-specific database paths
2. Disable debug logging
3. Implement configuration validation
4. Monitor configuration drift

### Security Guidelines
1. Never commit sensitive configuration to repository
2. Use environment variables for all secrets
3. Implement proper file permissions
4. Regular security configuration reviews

### Performance Optimization
1. Use appropriate database configuration for environment
2. Optimize logging levels for performance
3. Configure database pooling appropriately
4. Monitor configuration impact on performance

## Configuration Examples

### CI/CD Pipeline Configuration

**GitHub Actions configuration**:
```yaml
# .github/workflows/ci.yml
env:
  DATABASE_URL: "sqlite:///:memory:"
  TEST_DATABASE_URL: "sqlite:///:memory:"
  MCP_TEST_MODE: "true"
  SQL_DEBUG: "false"
```

### Docker Configuration

**Development Docker**:
```dockerfile
ENV DATABASE_URL="sqlite:///data/dev_agile_mcp.db"
ENV SQL_DEBUG="true"
ENV LOG_LEVEL="DEBUG"
```

**Production Docker**:
```dockerfile
ENV DATABASE_URL="sqlite:///data/prod_agile_mcp.db"
ENV SQL_DEBUG="false"
ENV LOG_LEVEL="INFO"
```

This configuration management system provides flexibility, security, and maintainability for the Agile MCP Server across all deployment scenarios.
