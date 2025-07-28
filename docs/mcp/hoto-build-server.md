# MCP Server Development and Testing Guidelines

This document provides comprehensive guidelines for building robust, maintainable, and compliant MCP servers. It covers general coding principles as well as specific best practices for `stdio` and `HTTP` transports, with concrete examples to ensure clarity.

---

### General Transport-Agnostic Coding Guidelines

These core principles apply to any MCP server, regardless of how it communicates with a client.

#### 1. Adopt a Clean, Layered Architecture

A strict separation of concerns is the key to a scalable and testable MCP server.

*   **API/Tool Layer (`api/tools.py`):** This is the only layer that should know about the Model Context Protocol. Its responsibilities are to define tools, validate inputs, call the service layer, and handle exceptions.
*   **Service/Business Logic Layer (`services/task_service.py`):** This layer contains the core logic of your application. It is "protocol-agnostic" and should not have any MCP-specific code.
*   **Data Access/Repository Layer (`repositories/task_repository.py`):** This layer handles all database interactions, abstracting the database from the service layer.

**Example Flow:** A `get_task` call illustrates this separation:
1.  The **Tool Layer** receives the MCP request for `get_task` with an `id`.
2.  It calls the `task_service.get_task_by_id(id)` method.
3.  The **Service Layer** calls the `task_repository.find_by_id(id)` method.
4.  The **Repository Layer** queries the database and returns a `Task` object.
5.  The Service Layer gets the `Task` object and returns it.
6.  The Tool Layer receives the `Task` object, serializes it into a dictionary, and returns it as the JSON-RPC result.

#### 2. Implement Robust and Informative Error Handling

This pattern is crucial for providing clear feedback to the client and for debugging.

*   **Define Custom Exceptions:** Create specific exceptions for your business logic.
    ```python
    # In a new file, e.g., mcp_server/services/exceptions.py
    class TaskNotFoundError(Exception):
        """Raised when a task is not found in the database."""
        pass

    class CircularDependencyError(Exception):
        """Raised when adding a dependency would create a cycle."""
        pass
    ```
*   **Translate Exceptions in the API/Tool Layer:** Catch your custom exceptions and convert them into standard MCP errors.
    ```python
    # In api/tools.py
    from mcp.server.fastmcp import FastMCP
    from mcp.exceptions import McpError
    from ..services.exceptions import TaskNotFoundError
    from ..services.task_service import TaskService

    # Create an instance of the FastMCP server
    mcp = FastMCP("task-server")
    task_service = TaskService()

    @mcp.tool()
    def get_task(task_id: int) -> dict:
        """Retrieves a single task by its unique ID."""
        try:
            task = task_service.get_task(task_id)
            return task.to_dict() # Assuming a method to serialize the object
        except TaskNotFoundError as e:
            # Translate the internal exception to a standard MCP error
            raise McpError(code=-32001, message=str(e), data={"task_id": task_id})
    ```

#### 3. Prioritize Type Safety and Clear Docstrings

The `FastMCP` SDK uses type hints and docstrings to automatically generate the tool schema for the LLM. This is not just good practice; it's a functional requirement.

**Example of a well-defined tool:**
```python
@mcp.tool()
def add_dependency(task_id: int, depends_on_task_id: int) -> bool:
    """
    Creates a dependency between two tasks, making one a prerequisite for the other.

    Args:
        task_id: The ID of the task that will depend on another.
        depends_on_task_id: The ID of the task that must be completed first.

    Returns:
        True if the dependency was added successfully.
    """
    if task_service.create_dependency(task_id, depends_on_task_id):
        return True
    return False
```
*   **How MCP uses this:**
    *   `add_dependency`: Becomes the tool name.
    *   `"""..."""`: The entire docstring is sent to the LLM as the tool's description.
    *   `task_id: int`: The LLM knows this is a required parameter named `task_id` of type `integer`.
    *   `-> bool`: The LLM knows the tool is expected to return a boolean value.

---

### Transport-Specific Guidelines

### 1. STDIO (Standard I/O) Transport

**When to Use:** For local tools managed by a host application (e.g., an IDE extension). The server runs as a child process.

#### Coding Guidelines for `stdio`

*   **CRITICAL: Isolate `stdout`:** The `stdout` stream is exclusively for JSON-RPC messages. **Never** use `print()`.
*   **Log to `stderr`:** All logging and diagnostics **must** go to `stderr`.

    ```python
    # Correct logging configuration for stdio
    import logging
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stderr  # This is the crucial part
    )
    ```

#### End-to-End (E2E) Testing for `stdio`

E2E tests must simulate a host by running the server as a subprocess and checking all I/O streams.

*   **Use Python's `subprocess` Module:** Launch `server.py` and capture its `stdin`, `stdout`, and `stderr`.
*   **Assert Stream Integrity:** The most important test is verifying that `stdout` contains *only* the JSON-RPC response, while logs appear on `stderr`.

---

### 2. HTTP Transport (e.g., via FastAPI/Flask)

**When to Use:** For servers accessible over a network (microservices, web clients).

#### Coding Guidelines for `HTTP`

*   **Implement Authentication:** A networked server **must** be secured. Use Bearer Tokens as recommended by the MCP specification.
    ```python
    # Example of a simple auth dependency in FastAPI
    from fastapi import Request, HTTPException, status, Depends
    from fastapi.security import HTTPBearer

    http_bearer = HTTPBearer()

    def verify_token(token = Depends(http_bearer)):
        # Replace this with your actual token validation logic
        if token.credentials != "YOUR_SECRET_STATIC_TOKEN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired token",
            )
        return token.credentials
    ```
    You would then protect your MCP endpoint like this: `app.post("/mcp", dependencies=[Depends(verify_token)])`.

*   **Standard Web Security:** Implement CORS policies, rate limiting, and use HTTPS in production.
*   **Configuration:** Use environment variables for settings like port, host, and secrets.

#### End-to-End (E2E) Testing for `HTTP`

*   **Run the Server:** Use a `pytest` fixture to start your web server in a background process.
*   **Use an HTTP Client:** Use `httpx` or `requests` to send `POST` requests to the server's endpoint.
*   **Assert HTTP and JSON Responses:** Check for the correct HTTP status code (`200 OK`), validate the JSON body, and test authentication by sending requests with and without valid `Authorization` headers.

**Example E2E Test for an HTTP Server:**
```python
import pytest
import httpx

# Assumes a fixture named 'http_server' starts the server process
# and yields its base URL (e.g., "http://127.0.0.1:8000")

def test_e2e_http_auth_failure(http_server):
    """Tests that a request with no token fails."""
    request_body = {
        "jsonrpc": "2.0", "id": 1, "method": "list_tasks", "params": {}
    }
    with httpx.Client() as client:
        response = client.post(f"{http_server}/mcp", json=request_body)

    assert response.status_code == 403 # Or 401 depending on implementation

def test_e2e_http_list_tasks_success(http_server):
    """Tests a valid request with a token."""
    request_body = {
        "jsonrpc": "2.0", "id": 2, "method": "list_tasks", "params": {}
    }
    headers = {"Authorization": "Bearer YOUR_SECRET_STATIC_TOKEN"}

    with httpx.Client() as client:
        response = client.post(f"{http_server}/mcp", json=request_body, headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 2
    assert "result" in response_data
```
