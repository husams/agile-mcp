"""
Enhanced pytest configuration and fixtures for E2E tests with comprehensive
subprocess isolation.

Provides isolated database environments, subprocess management for MCP server
testing,
and JSON-RPC client helpers for server communication with automatic cleanup.
"""

import json
import os
import subprocess
import threading
import time
from typing import Any, Dict, Optional

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Epic
from src.agile_mcp.models.project import Project
from tests.utils.test_database_manager import DatabaseManager


@pytest.fixture(scope="function")
def isolated_e2e_database():
    """
    Create completely isolated file database for E2E subprocess testing.
    Uses the enhanced DatabaseManager for better isolation and performance.

    Returns:
        Tuple of (db_path, environment_variables)
    """
    manager = DatabaseManager.get_instance()
    engine, session_factory, db_path = manager.create_file_database()

    # Create default test data for E2E tests
    session = session_factory()
    try:
        # Add default project first
        default_project = Project(
            id="default-project",
            name="Default Project",
            description="Default project for E2E testing",
        )
        session.add(default_project)

        # Add default epic required by E2E tests
        default_epic = Epic(
            id="default-epic",
            title="Default Epic",
            description="Default epic for E2E testing",
            project_id="default-project",
            status="Ready",
        )
        session.add(default_epic)
        session.commit()

        # Validate database health
        assert manager.validate_database_health(
            engine
        ), "E2E database failed health check"

    finally:
        session.close()

    # Environment variables for subprocess isolation
    env_vars = {
        "TEST_DATABASE_URL": f"sqlite:///{db_path}",
        "MCP_TEST_MODE": "true",
        "SQL_DEBUG": "false",
    }

    try:
        yield db_path, env_vars
    finally:
        # Cleanup database file
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def mcp_server_subprocess(isolated_e2e_database):
    """
    Enhanced subprocess fixture for MCP server with complete environment
    isolation.

    Provides:
    - Isolated database environment per test
    - Automatic process cleanup and error handling
    - JSON-RPC communication setup
    - Performance monitoring

    Returns:
        Tuple of (process, environment_vars, communicate_function)
    """
    db_path, env_vars = isolated_e2e_database

    # Prepare environment for subprocess
    subprocess_env = os.environ.copy()
    subprocess_env.update(env_vars)

    # Start MCP server subprocess
    process = None
    try:
        # Start the MCP server process
        # Use 'python' in CI, 'python3' locally for compatibility
        python_cmd = "python" if os.getenv("CI") == "true" else "python3"
        process = subprocess.Popen(
            [python_cmd, "-m", "src.agile_mcp.main"],
            env=subprocess_env,
            stdin=subprocess.PIPE,  # Add stdin for communication
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd(),
        )

        # Give the server a moment to start and print its initial banner/logs
        # We don't check process.poll() here, as stdio server might exit
        # if no input
        time.sleep(0.5)

        # Simplified startup approach for CI environments
        # In CI, we skip complex startup verification and rely on test timeouts
        is_ci = os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true"

        if is_ci:
            # In CI environments, use minimal startup check to avoid deadlocks
            time.sleep(5)  # Wait 5 seconds for server to start (increased for CI)
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=1)
                raise RuntimeError(
                    f"MCP server failed to start in CI. "
                    f"Exit code: {process.returncode}, "
                    f"stdout: {stdout}, stderr: {stderr}"
                )
        else:
            # Local development: use more thorough startup check
            start_time = time.time()
            server_ready = False
            startup_timeout = 10  # Increased timeout for CI environments

            while time.time() - start_time < startup_timeout:
                # Check if process has failed
                if process.poll() is not None:
                    stdout, stderr_final = process.communicate(timeout=1)
                    raise RuntimeError(
                        f"MCP server failed to start. Exit code: {process.returncode}, "
                        f"stdout: {stdout}, stderr: {stderr_final}"
                    )

                # For CI environments, we'll rely on a simple time-based check
                # instead of trying to read stderr which can deadlock
                if time.time() - start_time > 2:  # Give server 2 seconds to start
                    server_ready = True
                    break

                time.sleep(0.1)

            if not server_ready:
                # Try to get any output for debugging
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    raise RuntimeError(
                        f"MCP server startup timeout. "
                        f"stdout: {stdout}, stderr: {stderr}"
                    )
                except subprocess.TimeoutExpired:
                    raise RuntimeError(
                        "MCP server startup timeout - "
                        "process still running but not responsive"
                    )

        def communicate_json_rpc(
            method: str, params: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Helper function for JSON-RPC communication with the MCP server.

            Args:
                method: JSON-RPC method name
                params: Method parameters

            Returns:
                JSON-RPC response
            """
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or {},
            }

            # Thread-safe communication with timeout to prevent CI hanging
            try:
                # Check if process is still alive before attempting communication
                if process.poll() is not None:
                    return {"error": "MCP server process has terminated"}

                request_json = json.dumps(request) + "\n"
                process.stdin.write(request_json)
                process.stdin.flush()

                # Use threading to implement timeout for stdout.readline()
                response_data = {}

                def read_response():
                    try:
                        response_line = process.stdout.readline()
                        if response_line:
                            response_data["response"] = response_line.strip()
                        else:
                            response_data["error"] = "Empty response from server"
                    except Exception as e:
                        response_data["error"] = f"Read error: {str(e)}"

                # Start reader thread with timeout
                reader_thread = threading.Thread(target=read_response)
                reader_thread.daemon = True
                reader_thread.start()
                # Use longer timeout in CI environments which can be slower
                timeout_seconds = 30.0 if os.getenv("CI") == "true" else 10.0
                reader_thread.join(timeout=timeout_seconds)

                if reader_thread.is_alive():
                    # Thread is still running, meaning timeout occurred
                    error_msg = f"Response timeout from server after {timeout_seconds}s"
                    if os.getenv("CI") == "true":
                        error_msg += f" (CI environment, PID: {process.pid})"
                    return {"error": error_msg}

                if "error" in response_data:
                    return {"error": response_data["error"]}

                if "response" in response_data:
                    return json.loads(response_data["response"])

                return {"error": "No response received"}

            except Exception as e:
                return {"error": f"Communication error: {str(e)}"}

        yield process, env_vars, communicate_json_rpc

    finally:
        # Cleanup subprocess
        if process:
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            except Exception:
                pass  # Process cleanup failed, but continue


@pytest.fixture(scope="function")
def json_rpc_client():
    """
    JSON-RPC client helper functions for server communication.

    Returns:
        Dictionary of helper functions for common JSON-RPC operations
    """

    def create_request(
        method: str, params: Optional[Dict[str, Any]] = None, request_id: int = 1
    ) -> Dict[str, Any]:
        """Create a JSON-RPC 2.0 request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

    def parse_response(response_text: str) -> Dict[str, Any]:
        """Parse JSON-RPC response and handle errors."""
        try:
            response = json.loads(response_text)
            if "error" in response:
                raise RuntimeError(f"JSON-RPC Error: {response['error']}")
            return response.get("result", response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")

    def validate_response(
        response: Dict[str, Any], expected_keys: Optional[list[Any]] = None
    ) -> bool:
        """Validate JSON-RPC response structure."""
        if not isinstance(response, dict):
            return False

        # Check for required JSON-RPC 2.0 fields
        if "jsonrpc" in response and response["jsonrpc"] != "2.0":
            return False

        # Check for expected keys if provided
        if expected_keys:
            for key in expected_keys:
                if key not in response:
                    return False

        return True

    return {
        "create_request": create_request,
        "parse_response": parse_response,
        "validate_response": validate_response,
    }


@pytest.fixture(scope="function")
def e2e_test_data_setup(isolated_e2e_database):
    """
    E2E test data setup helpers using the new database manager.

    Returns:
        Function to setup common test data scenarios
    """
    db_path, env_vars = isolated_e2e_database

    def setup_test_data(scenario: str = "basic") -> Dict[str, Any]:
        """
        Setup test data for different E2E scenarios.

        Args:
            scenario: Type of test scenario
                ("basic", "with_stories", "complex")

        Returns:
            Dictionary with created test data IDs
        """
        # Create a session to the test database
        engine = create_engine(f"sqlite:///{db_path}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        data_ids: Dict[str, Any] = {}

        try:
            if scenario == "basic":
                # Just the default epic (already created)
                data_ids["epic_id"] = "default-epic"

            elif scenario == "with_stories":
                from src.agile_mcp.models.story import Story

                # Add test stories
                story1 = Story(
                    id="test-story-1",
                    epic_id="default-epic",
                    title="Test Story 1",
                    description="Test story for E2E testing",
                    acceptance_criteria=["Should work correctly"],
                    status="ToDo",
                )
                story2 = Story(
                    id="test-story-2",
                    epic_id="default-epic",
                    title="Test Story 2",
                    description="Another test story",
                    acceptance_criteria=["Should also work correctly"],
                    status="Ready",
                )

                session.add_all([story1, story2])
                session.commit()

                data_ids.update(
                    {
                        "epic_id": "default-epic",
                        "story_ids": ["test-story-1", "test-story-2"],
                    }
                )

            elif scenario == "complex":
                # Add stories and artifacts for complex testing
                from src.agile_mcp.models.artifact import Artifact
                from src.agile_mcp.models.story import Story

                story = Story(
                    id="complex-story",
                    epic_id="default-epic",
                    title="Complex Test Story",
                    description="Complex story with artifacts",
                    acceptance_criteria=["Should handle complexity"],
                    status="InProgress",
                )

                artifact = Artifact(
                    id="test-artifact",
                    uri="file:///test/path.py",
                    relation="implementation",
                    story_id="complex-story",
                )

                session.add_all([story, artifact])
                session.commit()

                data_ids.update(
                    {
                        "epic_id": "default-epic",
                        "story_id": "complex-story",
                        "artifact_id": "test-artifact",
                    }
                )

        finally:
            session.close()

        return data_ids

    return setup_test_data


# Legacy fixtures for backward compatibility
@pytest.fixture(scope="function")
def temp_database(isolated_e2e_database):
    """Legacy fixture for backward compatibility."""
    db_path, env_vars = isolated_e2e_database

    # Create session for legacy compatibility
    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session, db_path
    finally:
        session.close()


@pytest.fixture(scope="function")
def isolated_test_database(isolated_e2e_database):
    """Legacy fixture for backward compatibility."""
    db_path, env_vars = isolated_e2e_database
    yield db_path
