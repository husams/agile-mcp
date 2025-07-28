# Coding Guidelines and Conventions

This document outlines the coding guidelines and conventions to be followed for the Agile MCP Server project. Adhering to these guidelines ensures code consistency, readability, and maintainability across the codebase.

## General Principles

*   **Readability**: Write code that is easy to understand for other developers (and future you).
*   **Consistency**: Follow existing patterns and styles within the project.
*   **Simplicity**: Prefer straightforward solutions over overly complex ones.
*   **Maintainability**: Design code that is easy to modify and extend.
*   **Testability**: Write code that can be easily tested.

## Python Specific Guidelines

### Formatting

We use `Black` for code formatting. All code should be formatted using Black with default settings. This is enforced via pre-commit hooks.

### Naming Conventions

*   **Modules**: `lowercase_with_underscores` (e.g., `story_tools.py`)
*   **Packages**: `lowercase_with_underscores` (e.g., `agile_mcp`)
*   **Classes**: `CamelCase` (e.g., `StoryService`)
*   **Functions/Methods**: `lowercase_with_underscores` (e.g., `get_next_ready_story`)
*   **Variables**: `lowercase_with_underscores` (e.g., `story_id`)
*   **Constants**: `UPPERCASE_WITH_UNDERSCORES` (e.g., `DEFAULT_STATUS`)

### Imports

We use `isort` for sorting imports. Imports should be grouped and sorted as follows:

1.  Standard library imports.
2.  Third-party imports.
3.  Local application/project-specific imports.

Each group should be sorted alphabetically. This is enforced via pre-commit hooks.

### Type Hinting

All new code should use type hints for function arguments, return values, and variables where appropriate. This improves code clarity and enables static analysis with MyPy.

### Docstrings

All modules, classes, and public functions/methods should have docstrings. We follow the Google style for docstrings.

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of what the function does.

    Args:
        param1: Description of the first parameter.
        param2: Description of the second parameter.

    Returns:
        Description of the return value.
    """
    # Function implementation
    return True
```

### Error Handling

*   Use exceptions for exceptional conditions, not for control flow.
*   Be specific with exception types (e.g., `ValueError`, `FileNotFoundError`).
*   Catch exceptions as narrowly as possible.

### Logging

Use the standard Python `logging` module for all logging. Configure structured logging as implemented in Epic 4, Story 4.2.

### Database Interactions

*   All database interactions should go through the `repositories` layer.
*   Avoid direct SQLAlchemy ORM usage outside of the `repositories`.

## Architecture Specific Guidelines

### 3-Layer Architecture

Adhere to the defined 3-Layer Architecture:

*   **API Layer (`src/agile_mcp/api/`)**: Handles incoming requests, validates input, and calls the appropriate service layer methods. Returns responses in MCP-compliant JSON-RPC format.
*   **Service Layer (`src/agile_mcp/services/`)**: Contains the core business logic. Orchestrates operations across multiple repositories if needed. Should be independent of the API layer.
*   **Repository Layer (`src/agile_mcp/repositories/`)**: Abstracts database interactions. Provides methods for CRUD operations on models. Should be independent of the service layer.

### MCP Protocol Adherence

All external interactions (API endpoints) must strictly adhere to the Model Context Protocol (MCP) specification and JSON-RPC 2.0.

## Pre-commit Hooks

Ensure all pre-commit hooks are installed and pass before committing code. These hooks automate formatting, linting, and type checking.

```bash
pre-commit install
```

## Code Review

All code changes must go through a code review process. Reviewers should ensure adherence to these guidelines and overall code quality.
