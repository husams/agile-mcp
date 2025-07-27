# Contributing to Agile MCP

This guide covers the development workflow and quality checks for contributing to the Agile MCP project.

## Prerequisites

- Python 3.11+
- Git
- Access to production MCP server for E2E testing

## Development Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Pre-commit Hooks

Pre-commit hooks ensure code quality and prevent issues before they reach production:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files (optional)
pre-commit run --all-files
```

### 3. Verify Setup

```bash
# Test pre-commit installation
pre-commit run --all-files

# Run a quick test
python -m pytest tests/unit/ -v
```

## Quality Checks

Our pre-commit hooks run automatically before each commit and include:

### Code Formatting & Linting
- **Black**: Code formatting with 88-character line length
- **isort**: Import sorting with Black profile
- **Flake8**: Linting with docstring checks
- **MyPy**: Type checking for better code reliability

### Security & Quality
- **Bandit**: Security vulnerability scanning
- **General checks**: Trailing whitespace, JSON/YAML validation, merge conflicts

### MCP-Specific Validation
- **JSON Response Validation**: Ensures all `@mcp.tool` functions return valid JSON
- **MCP Protocol Compliance**: Validates tool names, descriptions, and annotations
- **Critical E2E Tests**: Runs subset of E2E tests against production server

## Development Workflow

### 1. Before Starting Work

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 2. During Development

- Write code following existing patterns and conventions
- Add type hints to all functions and parameters
- Include comprehensive docstrings
- Ensure `@mcp.tool` functions return JSON strings

### 3. Before Committing

Pre-commit hooks will automatically run, but you can run them manually:

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run black
pre-commit run json-response-validation
```

### 4. Testing

```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Run E2E tests (requires production server)
python -m pytest tests/e2e/ -v
```

## MCP Tool Development Guidelines

### Tool Function Requirements

All `@mcp.tool` decorated functions must:

1. **Return JSON strings** - Use `json.dumps()` or `mcp_response()` helpers
2. **Have type annotations** - All parameters and return type must be annotated
3. **Include docstrings** - Document purpose, parameters, and return values
4. **Follow naming conventions** - Use snake_case for parameters
5. **Have unique tool names** - Tool names must be unique across the project

### Example Tool Function

```python
@mcp.tool(
    name="get_story_details",
    description="Retrieve detailed information about a specific story including its tasks and status."
)
def get_story_details(story_id: int) -> str:
    """
    Get comprehensive details for a story by its ID.

    Args:
        story_id: The unique identifier of the story to retrieve

    Returns:
        JSON string containing story details, tasks, and metadata

    Raises:
        ValueError: If story_id is invalid or story not found
    """
    try:
        story = story_service.get_story(story_id)
        return json.dumps({
            "success": True,
            "story": story.model_dump(),
            "tasks": [task.model_dump() for task in story.tasks]
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })
```

## Pre-commit Hook Details

### Custom Validation Scripts

Located in `scripts/` directory:

- `validate_responses.py` - Ensures tool functions return valid JSON
- `validate_mcp_protocol.py` - Checks MCP protocol compliance
- `run_critical_tests.py` - Runs E2E tests against production server

### Hook Configuration

See `.pre-commit-config.yaml` for complete configuration. Key hooks:

- **json-response-validation**: Validates JSON responses in API tools
- **critical-e2e-tests**: Runs production server tests on relevant changes
- **mcp-protocol-validation**: Ensures MCP compliance

## Testing Requirements

### E2E Testing Architecture (MANDATORY)

- **Production Server Only**: All E2E tests MUST use production server
- **Real Data**: No mocked or fabricated data in E2E tests
- **No Isolation**: E2E tests operate on shared production data state

### Test Categories

1. **Unit Tests** (`tests/unit/`) - Fast, isolated component tests
2. **E2E Tests** (`tests/e2e/`) - Full system tests with production server
3. **Quality Tests** - Automated via pre-commit hooks

## Troubleshooting

### Pre-commit Hook Failures

#### JSON Response Validation Errors
```bash
❌ Tool function 'get_story' must return JSON string
```
**Fix**: Ensure function returns `json.dumps(...)` or uses `mcp_response()` helper

#### MCP Protocol Compliance Errors
```bash
❌ Tool description too short: 'Gets story' (minimum 10 characters)
```
**Fix**: Add detailed description (10-500 characters) ending with period

#### Critical E2E Test Failures
```bash
❌ test_story_tools_e2e: FAILED
```
**Fix**: Check production server is running and API responses match expected format

### Common Issues

1. **Import Errors**: Ensure all dependencies in `requirements.txt` are installed
2. **Type Check Failures**: Add type hints to all parameters and return values
3. **Format Violations**: Run `black` and `isort` to fix formatting
4. **Security Issues**: Review `bandit` output for security vulnerabilities

### Emergency Bypass

For critical fixes that need to bypass quality checks:

```bash
git commit --no-verify -m "emergency: critical production fix"
```

**Note**: Use sparingly and fix quality issues in follow-up commits.

## Quality Check Bypass

In exceptional circumstances, you can skip pre-commit hooks:

```bash
# Skip all hooks (emergency only)
git commit --no-verify

# Skip specific hooks
SKIP=mypy,bandit git commit
```

## Getting Help

1. Check this documentation first
2. Review error messages and suggested fixes
3. Ask team members for assistance
4. Create GitHub issue for persistent problems

## Quality Metrics

Our quality checks ensure:
- 100% JSON compliance for MCP tool responses
- Type safety with MyPy validation
- Security compliance with Bandit scanning
- MCP protocol adherence for all tools
- Production-validated E2E test coverage
