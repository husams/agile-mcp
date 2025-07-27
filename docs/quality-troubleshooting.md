# Quality Check Troubleshooting Guide

This guide helps developers resolve common issues with the proactive quality checks implemented in the Agile MCP project.

## Quick Diagnosis

### Pre-commit Hook Failures

If your commit is blocked by pre-commit hooks, follow these steps:

1. **See what failed**: Check the error output for specific failed hooks
2. **Run manually**: `pre-commit run --all-files` to see all issues
3. **Fix and retry**: Address issues and commit again

## Common Issues and Solutions

### JSON Response Validation Errors

#### Error: Tool function must return JSON string
```bash
❌ src/agile_mcp/api/story_tools.py:45 - Tool function 'get_story' must return JSON string
```

**Cause**: Function doesn't return a valid JSON string
**Solution**: Ensure function returns `json.dumps(...)` or uses helper functions:

```python
# ❌ Wrong - returns dict
@mcp.tool()
def get_story(story_id: int) -> str:
    return {"success": True, "data": story}

# ✅ Correct - returns JSON string
@mcp.tool()
def get_story(story_id: int) -> str:
    return json.dumps({"success": True, "data": story})

# ✅ Also correct - uses helper
@mcp.tool()
def get_story(story_id: int) -> str:
    return mcp_response(success=True, data=story)
```

#### Error: Function has complex data structures but no Pydantic serialization
```bash
❌ Function 'get_stories' has complex data structures but no Pydantic serialization
```

**Cause**: Complex data without proper serialization
**Solution**: Use Pydantic models for consistent JSON output:

```python
# ✅ Use Pydantic model serialization
@mcp.tool()
def get_stories() -> str:
    stories = story_service.get_all_stories()
    return json.dumps([story.model_dump() for story in stories])
```

### MCP Protocol Compliance Errors

#### Error: Tool name must start with letter
```bash
❌ Tool name '_internal_helper' must start with letter and contain only alphanumeric, underscore, or hyphen characters
```

**Solution**: Use valid tool names:
```python
# ❌ Wrong
@mcp.tool(name="_internal_helper")
def helper(): pass

# ✅ Correct
@mcp.tool(name="internal_helper")
def helper(): pass
```

#### Error: Tool description too short
```bash
❌ Tool description too short: 'Gets story' (minimum 10 characters)
```

**Solution**: Provide descriptive explanations:
```python
# ❌ Wrong
@mcp.tool(description="Gets story")
def get_story(): pass

# ✅ Correct
@mcp.tool(description="Retrieve detailed information about a specific story including its tasks and status.")
def get_story(): pass
```

#### Error: Parameter missing type annotation
```bash
❌ Parameter 'story_id' missing type annotation
```

**Solution**: Add type hints to all parameters:
```python
# ❌ Wrong
def get_story(story_id):
    pass

# ✅ Correct
def get_story(story_id: int) -> str:
    pass
```

### Critical E2E Test Failures

#### Error: E2E tests failed
```bash
❌ test_story_tools_e2e: FAILED
```

**Diagnosis Steps**:
1. Check if production server is running: `curl http://localhost:8000/health`
2. Verify database connectivity
3. Check recent changes affect API responses

**Common Causes**:
- Production server not running
- Database connection issues
- API response format changes
- Network connectivity problems

**Solutions**:
```bash
# Start production server
python -m src.agile_mcp.main &

# Test server health
curl http://localhost:8000/health

# Run specific test for debugging
pytest tests/e2e/test_story_tools_e2e.py::test_get_story -v
```

### Code Quality Issues

#### Black Formatting Errors
```bash
❌ would reformat src/agile_mcp/api/story_tools.py
```

**Solution**: Run Black formatter:
```bash
black src/agile_mcp/api/story_tools.py
# Or format all files
black .
```

#### Flake8 Linting Errors
```bash
❌ src/agile_mcp/api/story_tools.py:123:80: E501 line too long
```

**Solutions**:
```python
# ❌ Long line
very_long_variable_name = some_function_with_many_parameters(param1, param2, param3, param4)

# ✅ Break into multiple lines
very_long_variable_name = some_function_with_many_parameters(
    param1, param2, param3, param4
)
```

#### MyPy Type Errors
```bash
❌ error: Argument 1 to "get_story" has incompatible type "str"; expected "int"
```

**Solution**: Fix type mismatches:
```python
# ❌ Wrong type
story_id = "123"  # str
get_story(story_id)  # expects int

# ✅ Correct type
story_id = int("123")  # int
get_story(story_id)
```

#### Import Sorting (isort) Errors
```bash
❌ Fixing src/agile_mcp/api/story_tools.py
```

**Solution**: Run isort:
```bash
isort src/agile_mcp/api/story_tools.py
# Or all files
isort .
```

### Security Issues (Bandit)

#### High severity issues
```bash
❌ [B105:hardcoded_password_string] Possible hardcoded password
```

**Solution**: Use environment variables:
```python
# ❌ Wrong - hardcoded secret
API_KEY = "secret123"

# ✅ Correct - environment variable
API_KEY = os.getenv("API_KEY")
```

#### SQL injection risks
```bash
❌ [B608:hardcoded_sql_expressions] Possible SQL injection vector
```

**Solution**: Use parameterized queries:
```python
# ❌ Wrong - SQL injection risk
query = f"SELECT * FROM stories WHERE id = {story_id}"

# ✅ Correct - parameterized query
query = "SELECT * FROM stories WHERE id = ?"
cursor.execute(query, (story_id,))
```

## Emergency Procedures

### Bypassing Quality Checks

**For critical production fixes only**:

```bash
# Skip all pre-commit hooks
git commit --no-verify -m "emergency: critical production fix"

# Skip specific hooks
SKIP=mypy,bandit git commit -m "fix: urgent issue"
```

**Important**: Create follow-up commits to fix quality issues.

### When Pre-commit Hooks Won't Install

```bash
# Reinstall pre-commit
pip uninstall pre-commit
pip install pre-commit

# Clean and reinstall hooks
pre-commit clean
pre-commit install

# Update hook repositories
pre-commit autoupdate
```

### Performance Issues

If pre-commit hooks are too slow:

```bash
# Run only on changed files
pre-commit run --files src/agile_mcp/api/story_tools.py

# Skip slow hooks for quick commits
SKIP=critical-e2e-tests git commit -m "minor: documentation update"
```

## Debugging Workflow

### Step 1: Identify the Problem
```bash
# Run all quality checks manually
pre-commit run --all-files

# Run specific validation
python scripts/validate_responses.py src/agile_mcp/api/*.py
python scripts/validate_mcp_protocol.py src/agile_mcp/api/*.py
```

### Step 2: Test Specific Components
```bash
# Test JSON response validation
python scripts/validate_responses.py src/agile_mcp/api/story_tools.py

# Test MCP protocol compliance
python scripts/validate_mcp_protocol.py src/agile_mcp/api/story_tools.py

# Test critical E2E tests
python scripts/run_critical_tests.py --production-server src/agile_mcp/api/story_tools.py
```

### Step 3: Fix and Verify
```bash
# After making changes, test again
pre-commit run --files src/agile_mcp/api/story_tools.py

# Test specific hook
pre-commit run json-response-validation --files src/agile_mcp/api/story_tools.py
```

## Getting Help

### Check Logs
- Pre-commit output shows specific line numbers and issues
- CI/CD logs provide detailed error information
- E2E test logs show server response details

### Team Resources
1. Check this troubleshooting guide first
2. Review similar fixes in git history: `git log --grep="fix:"`
3. Ask team members for assistance
4. Create GitHub issue for persistent problems

### Useful Commands

```bash
# Show current hook configuration
pre-commit --version
cat .pre-commit-config.yaml

# List installed hooks
ls -la .git/hooks/

# Check pre-commit cache
pre-commit clean

# Update all hooks to latest versions
pre-commit autoupdate

# Run specific tool manually
black --check src/
flake8 src/
mypy src/
bandit -r src/
```

## Quality Standards Reference

### JSON Response Requirements
- All `@mcp.tool` functions must return JSON strings
- Use `json.dumps()` or `mcp_response()` helpers
- Consider Pydantic models for complex data structures

### MCP Protocol Requirements
- Tool names: alphanumeric, underscore, hyphen only
- Descriptions: 10-500 characters, proper punctuation
- Type annotations: all parameters and return types
- Docstrings: comprehensive parameter documentation

### Code Quality Standards
- Line length: 88 characters (Black standard)
- Import sorting: isort with Black profile
- Type checking: MyPy with ignore-missing-imports
- Security: Bandit scanning for vulnerabilities
- Coverage: minimum 75% for changed code

### E2E Testing Requirements
- Production server only (no mocked data)
- Real database connections
- Actual API response validation
- Network connectivity required
