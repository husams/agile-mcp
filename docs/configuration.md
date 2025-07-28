# Configuration Management

This document outlines the approach to managing configuration within the Agile MCP Server.

## Principles

*   **Centralized Configuration**: All application-wide settings should be managed from a central location.
*   **Environment-Specific Overrides**: Support for different configurations based on the deployment environment (e.g., development, testing, production).
*   **Security**: Sensitive information (e.g., API keys, database credentials) must be handled securely and not hardcoded.

## Implementation

Configuration is managed primarily through `src/agile_mcp/config.py`. This module loads settings from environment variables, providing flexibility for different deployment scenarios.

### `src/agile_mcp/config.py`

This file defines the default configuration values and provides mechanisms to override them using environment variables.

```python
# Example (conceptual)
import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agile_mcp.db")
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", 8000))
    # Add other configuration parameters here

settings = Settings()
```

### Environment Variables

The following environment variables can be used to customize the server's behavior:

*   `DATABASE_URL`: Specifies the database connection string (e.g., `sqlite:///./test.db` for testing).
*   `MCP_SERVER_HOST`: Sets the host address for the server (default: `127.0.0.1`).
*   `MCP_SERVER_PORT`: Sets the port for the server (default: `8000`).

### Local Development

For local development, you can set environment variables directly in your shell before running the server:

```bash
export DATABASE_URL="sqlite:///./dev_agile_mcp.db"
export MCP_SERVER_PORT=8001
python run_server.py
```

Alternatively, you can use a `.env` file and a library like `python-dotenv` to load environment variables automatically (though `python-dotenv` is not a core dependency and would need to be added if desired).

## Sensitive Information

Sensitive configuration (e.g., API keys for external services, if any were to be integrated) should **never** be committed directly into the repository. Instead, they should be provided via environment variables or a secure secrets management solution in production environments.
