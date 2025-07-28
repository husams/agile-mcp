# Rollback Procedures - Brownfield MCP Server

## Overview

Essential rollback procedures for the Agile MCP Server to address critical risk management requirements identified in brownfield deployment validation.

## Git-Based Rollback (Primary Method)

### Feature Branch Rollback
```bash
# 1. Identify problematic commit/branch
git log --oneline -10

# 2. Create rollback branch from last known good state
git checkout main
git checkout -b rollback/fix-issue-$(date +%Y%m%d)

# 3. Reset to last known good commit
git reset --hard <last-good-commit-hash>

# 4. Force push to rollback
git push origin rollback/fix-issue-$(date +%Y%m%d) --force
```

### Production Rollback
```bash
# 1. Stop current server
pkill -f "python run_server.py"

# 2. Checkout previous stable version
git checkout <previous-stable-tag>

# 3. Restore database if needed (see Database Rollback)
# 4. Restart server
python run_server.py
```

## Database Rollback

### SQLite Database Rollback
```bash
# 1. Stop server
pkill -f "python run_server.py"

# 2. Backup current database
cp agile_mcp.db agile_mcp_failed_$(date +%Y%m%d).db

# 3. Restore from backup
cp agile_mcp_backup_<date>.db agile_mcp.db

# 4. Verify database integrity
sqlite3 agile_mcp.db "PRAGMA integrity_check;"

# 5. Restart server
python run_server.py
```

### Schema Migration Rollback
```bash
# If schema changes need to be reverted
# 1. Export data
sqlite3 agile_mcp.db ".dump" > data_export.sql

# 2. Recreate database with old schema
rm agile_mcp.db
git checkout <previous-schema-version>
python run_server.py  # Creates new database with old schema
pkill -f "python run_server.py"

# 3. Import compatible data
sqlite3 agile_mcp.db < data_export.sql
```

## Integration Rollback

### MCP Client Integration Issues
```bash
# 1. Revert to previous server version
git checkout <last-working-mcp-version>

# 2. Test MCP connectivity
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' | python run_server.py

# 3. Verify tool availability
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python run_server.py
```

## Rollback Decision Matrix

### When to Rollback

| Issue Type | Severity | Rollback Decision | Procedure |
|------------|----------|-------------------|-----------|
| Server won't start | Critical | Immediate | Git + Database |
| MCP tools failing | High | Within 1 hour | Git rollback |
| Data corruption | Critical | Immediate | Database rollback |
| Performance degradation | Medium | Within 4 hours | Git rollback |
| Client connectivity issues | High | Within 2 hours | Integration rollback |

### Rollback Validation

After any rollback:
```bash
# 1. Verify server starts
python run_server.py &
SERVER_PID=$!

# 2. Test basic MCP functionality
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' | python run_server.py

# 3. Test critical tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"epics.find","arguments":{}}}' | python run_server.py

# 4. Check database integrity
sqlite3 agile_mcp.db "SELECT COUNT(*) FROM epics;"

# 5. Cleanup
kill $SERVER_PID
```

## Emergency Rollback Script

```bash
#!/bin/bash
# emergency-rollback.sh - Use only in critical situations

echo "EMERGENCY ROLLBACK INITIATED"
echo "Current time: $(date)"

# Stop server
echo "Stopping server..."
pkill -f "python run_server.py"

# Backup current state
echo "Backing up current state..."
cp agile_mcp.db emergency_backup_$(date +%Y%m%d_%H%M%S).db

# Get last stable commit
LAST_STABLE=$(git tag | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)
echo "Rolling back to: $LAST_STABLE"

# Rollback code
git checkout $LAST_STABLE

# Restore database if backup exists
if [ -f "agile_mcp_backup.db" ]; then
    echo "Restoring database backup..."
    cp agile_mcp_backup.db agile_mcp.db
fi

# Restart server
echo "Restarting server..."
python run_server.py &

# Verify
sleep 2
if pgrep -f "python run_server.py" > /dev/null; then
    echo "ROLLBACK SUCCESSFUL - Server is running"
else
    echo "ROLLBACK FAILED - Server not running"
    exit 1
fi
```

## Recovery After Rollback

### Post-Rollback Steps
1. **Assess Impact**: Determine what functionality was lost
2. **Notify Stakeholders**: Inform users of rollback and timeline for fix
3. **Root Cause Analysis**: Identify why rollback was necessary
4. **Plan Forward**: Create plan to reimplement changes safely
5. **Test Thoroughly**: Ensure new implementation doesn't repeat issues

### Rollback Documentation Template
```markdown
## Rollback Event Report

**Date:** [Date of rollback]
**Trigger:** [What caused the need for rollback]
**Rollback Scope:** [Code/Database/Both]
**Downtime:** [Duration of service interruption]
**Data Loss:** [Any data lost during rollback]
**Recovery Steps Taken:** [Detailed steps performed]
**Root Cause:** [Why the issue occurred]
**Prevention Measures:** [Steps to prevent recurrence]
```

This document addresses the critical rollback procedure gaps identified in the PO validation checklist for brownfield risk management.
