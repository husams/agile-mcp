# Integration Guide - Brownfield MCP Server

## Overview

This guide addresses critical integration points for the Agile MCP Server in brownfield deployments, focusing on external system interactions and integration troubleshooting.

## External Integration Points

### MCP Client Integration
**Integration Type:** Model Context Protocol (MCP) communication
**External System:** AI Agent Host Applications
**Communication Method:** JSON-RPC over stdio

**Integration Pattern:**
```
AI Agent Host → MCP Client → stdio → Agile MCP Server
```

**Critical Integration Points:**
- Server initialization and capability negotiation
- Tool call routing and response handling
- Error propagation and client notification

### Database Integration
**Integration Type:** Database persistence layer
**External System:** SQLite database file
**Communication Method:** SQLAlchemy ORM

**Integration Pattern:**
```
MCP Tools → Service Layer → Repository Layer → SQLAlchemy → SQLite
```

**Critical Integration Points:**
- Database connection management
- Transaction handling and rollback
- Schema migration and versioning

## Integration Troubleshooting

### MCP Client Connection Issues

**Symptom:** Client cannot connect to server
```bash
# Check server startup
python run_server.py
# Should output: "Starting Agile Management MCP Server"

# Test MCP initialization manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' | python run_server.py
```

**Symptom:** Tool calls fail or timeout
```bash
# Enable debug logging
export SQL_DEBUG="true"
python run_server.py

# Check tool registration
grep "tools registered successfully" server.log
```

### Database Integration Issues

**Symptom:** Database connection failures
```bash
# Check database file permissions
ls -la agile_mcp.db

# Test database connectivity
python -c "
from src.agile_mcp.database import engine
with engine.connect() as conn:
    result = conn.execute('SELECT 1').fetchone()
    print('Database OK:', result[0] == 1)
"
```

**Symptom:** Data inconsistency or corruption
```bash
# Check database integrity
sqlite3 agile_mcp.db "PRAGMA integrity_check;"

# Backup and restore if needed
cp agile_mcp.db agile_mcp_backup.db
```

## Integration Monitoring

### Key Integration Metrics
- MCP tool call success rate
- Database operation response times
- Client connection stability
- Error rates by integration point

### Health Check Commands
```bash
# Database health check
python -c "
from src.agile_mcp.utils.monitoring import IntegrationMonitor
result = IntegrationMonitor.check_database_health()
print('Database Status:', result['health_status'])
"

# Server health check
python -c "
from src.agile_mcp.utils.monitoring import IntegrationMonitor
result = IntegrationMonitor.check_server_health()
print('Server Status:', result['health_status'])
"
```

## Critical Integration Requirements

### For MCP Client Integration
1. **Protocol Compliance:** Server must implement MCP 2024-11-05 specification
2. **Error Handling:** All tool errors must be propagated as valid JSON-RPC responses
3. **Session Management:** Server must maintain state throughout client session

### For Database Integration
1. **Transaction Safety:** All database operations must be atomic
2. **Connection Pooling:** SQLAlchemy connection pool must be properly configured
3. **Schema Consistency:** Database schema must match model definitions

### For Brownfield Deployment
1. **Backward Compatibility:** New versions must not break existing client integrations
2. **Data Migration:** Database schema changes must include migration procedures
3. **Rollback Support:** All integration changes must be reversible

This minimal integration guide addresses the critical documentation gaps identified in the PO checklist validation.
