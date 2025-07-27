#!/usr/bin/env python3
"""
Script to create Epic 5 for Database Isolation using MCP server tools.
"""

import json
import subprocess
import sys
import time
from typing import Any, Dict


def send_mcp_request(
    process: subprocess.Popen, method: str, params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Send JSON-RPC request to MCP server and return response."""
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}

    request_json = json.dumps(request) + "\n"

    try:
        process.stdin.write(request_json)
        process.stdin.flush()

        response_line = process.stdout.readline()
        if not response_line:
            stderr_output = process.stderr.read()
            raise Exception(f"No response from server. STDERR: {stderr_output}")

        return json.loads(response_line)

    except Exception as e:
        # Capture any remaining stderr
        process.poll()  # Update return code
        if process.returncode is not None:
            stdout, stderr = process.communicate()
            raise Exception(
                f"Server process died. Return code: {process.returncode}, STDERR: {stderr}"
            )
        raise e


def create_mcp_server() -> subprocess.Popen:
    """Start the MCP server process."""
    process = subprocess.Popen(
        [sys.executable, "run_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give server time to start
    time.sleep(1.0)

    # Verify process started successfully
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        raise Exception(f"Server failed to start. STDOUT: {stdout}, STDERR: {stderr}")

    return process


def main():
    """Create Epic 5 and its stories using MCP tools."""

    # Epic 5 data
    epic_data = {
        "title": "E2E Test Failure Remediation & Database Isolation",
        "description": """Implement comprehensive database isolation solution to eliminate critical E2E test failures and achieve bulletproof test reliability.

## Context
Current QA assessment identified 4 critical E2E test failures due to database state bleeding, resulting in 93.4% pass rate vs. target 100%. This epic addresses core infrastructure issues preventing reliable test execution.

## Core Objectives
- Fix 4 failing E2E tests (artifact tools response format issues)
- Implement test-only DatabaseManager in tests/utils/ directory
- Achieve three-tier test isolation (unit/integration/E2E)
- Maintain production server unchanged (zero regression risk)
- Enable 10x unit test performance improvement
- Support parallel test execution for CI/CD optimization

## Key Requirements
- Create test-only DatabaseManager with bulletproof session management
- Fix artifact tools error response format compliance with MCP protocol
- Implement per-function database isolation for unit tests
- Add isolated file databases for E2E subprocess testing
- Maintain production server architecture unchanged
- Enable parallel test execution with --n auto support

## Success Criteria
- All 61 E2E tests pass consistently (100% pass rate)
- Unit test execution under 5 seconds (10x improvement)
- Zero test pollution between test runs
- Production server code unchanged
- Support for concurrent test execution
- Database isolation prevents all test interference""",
    }

    # Stories for Epic 5
    stories = [
        {
            "title": "5.1 Create Test-Only DatabaseManager Infrastructure",
            "description": """Create comprehensive test-only database manager in tests/utils/ directory.

As a developer, I need a bulletproof test-only database manager so that I can achieve complete database isolation without touching production server code.

## Technical Requirements
- Create tests/utils/test_database_manager.py with TestDatabaseManager class
- Implement thread-safe session management with per-function isolation
- Support in-memory SQLite for unit tests (fastest execution)
- Support file-based databases for E2E subprocess testing
- Provide context managers for automatic cleanup
- Add health check and debugging utilities

## Implementation Details
- Use threading.Lock for thread safety
- Cache engines and session factories per thread
- Generate unique database URLs with UUID test IDs
- Enable foreign key constraints and WAL mode for SQLite
- Provide legacy compatibility functions for existing code""",
            "acceptance_criteria": [
                "TestDatabaseManager class created in tests/utils/test_database_manager.py",
                "Thread-safe session management implemented with locking",
                "Support for both in-memory and file-based databases",
                "Context manager provides automatic session cleanup",
                "Health check method validates database connections",
                "Legacy compatibility functions maintain existing API",
                "Documentation includes usage examples and patterns",
            ],
        },
        {
            "title": "5.2 Enhanced Test Fixtures with Bulletproof Isolation",
            "description": """Update root conftest.py with comprehensive database isolation fixtures.

As a QA engineer, I need enhanced test fixtures that provide bulletproof database isolation so that tests never interfere with each other.

## Technical Requirements
- Update tests/conftest.py with new fixtures using TestDatabaseManager
- Implement per-function database isolation for unit tests
- Create isolated file database fixtures for E2E tests
- Add comprehensive database dependency mocking
- Provide test data factory utilities
- Include database isolation validation helpers

## Implementation Details
- Use isolated_memory_db fixture for fastest unit tests
- Use isolated_file_db fixture for E2E subprocess testing
- Mock all database imports across API, service, and repository layers
- Add TestDataFactory for consistent test data creation
- Include DatabaseIsolationValidator for debugging""",
            "acceptance_criteria": [
                "Root tests/conftest.py updated with new fixtures",
                "isolated_memory_db fixture provides per-function isolation",
                "isolated_file_db fixture creates temporary file databases",
                "mock_database_dependencies comprehensively patches all imports",
                "TestDataFactory creates consistent test data patterns",
                "DatabaseIsolationValidator helps debug isolation issues",
                "All fixtures include proper cleanup mechanisms",
            ],
        },
        {
            "title": "5.3 Fix Artifact Tools MCP Protocol Compliance",
            "description": """Fix the 4 failing E2E tests related to artifact tools response format issues.

As a developer using the MCP server, I need all error responses to follow JSON-RPC format so that my tools can reliably parse responses.

## Technical Requirements
- Fix src/agile_mcp/api/artifact_tools.py error handling (lines 220, 258)
- Ensure all error responses return JSON-RPC compliant format
- Update response validation helpers to handle optional fields
- Standardize error response structure across all tools
- Maintain MCP protocol compliance for all scenarios

## Error Details
- JSONDecodeError: Expecting value: line 1 column 1 (char 0)
- Tool response missing required field 'success'
- Plain text error returns instead of structured JSON responses

## Implementation Details
- Replace plain text error returns with structured JSON responses
- Use consistent error response format across all API tools
- Update validation helpers to be more flexible with optional fields""",
            "acceptance_criteria": [
                "All artifact tools return JSON-RPC compliant error responses",
                "No more JSONDecodeError exceptions in E2E tests",
                "Response validation handles optional 'success' field gracefully",
                "Error response format standardized across all tools",
                "All 4 failing E2E tests now pass consistently",
                "MCP protocol compliance maintained for all scenarios",
                "Error messages remain informative while being properly structured",
            ],
        },
        {
            "title": "5.4 E2E Test Configuration with Subprocess Isolation",
            "description": """Create E2E-specific test configuration with subprocess isolation.

As a QA engineer, I need E2E tests that run in completely isolated subprocesses so that they accurately simulate real-world MCP server usage.

## Technical Requirements
- Create tests/e2e/conftest.py with subprocess isolation fixtures
- Implement mcp_server_subprocess fixture with isolated databases
- Add JSON-RPC client helpers for server communication
- Provide e2e_test_data fixture for consistent test data
- Ensure proper process cleanup and error handling

## Implementation Details
- Start MCP server in subprocess with isolated file database
- Set TEST_DATABASE_URL and MCP_TEST_MODE environment variables
- Provide JSON-RPC communication helpers
- Handle process startup/shutdown gracefully
- Create test data in isolated database before test execution""",
            "acceptance_criteria": [
                "tests/e2e/conftest.py created with subprocess fixtures",
                "mcp_server_subprocess fixture starts server in isolation",
                "JSON-RPC client helpers communicate with subprocess server",
                "e2e_test_data fixture creates isolated test data",
                "Process cleanup handles both normal and error scenarios",
                "Environment variables properly isolate subprocess database",
                "Server startup validation prevents flaky test failures",
            ],
        },
        {
            "title": "5.5 Migrate All Test Types to New Isolation Architecture",
            "description": """Migrate unit, integration, and E2E tests to use new isolation architecture.

As a developer, I need all tests to use the new isolation system so that I get reliable, fast, and parallel-safe test execution.

## Technical Requirements
- Update unit tests to use mock_database_dependencies fixture
- Update integration tests to use shared in-memory databases
- Update E2E tests to use subprocess isolation fixtures
- Add pytest markers for test categorization (unit/integration/e2e)
- Enable parallel execution for unit and integration tests

## Implementation Details
- Replace existing database setup with new fixtures
- Add @pytest.mark.unit, @pytest.mark.integration, @pytest.mark.e2e markers
- Update test imports to use new fixture patterns
- Validate 10x performance improvement for unit tests
- Ensure all 61 E2E tests pass consistently""",
            "acceptance_criteria": [
                "All unit tests use mock_database_dependencies fixture",
                "All integration tests use shared in-memory databases",
                "All E2E tests use subprocess isolation fixtures",
                "Pytest markers properly categorize test types",
                "Unit tests execute in under 5 seconds (10x improvement)",
                "Integration tests maintain consistent performance",
                "All 61 E2E tests pass with 100% reliability",
                "Parallel execution works safely for unit/integration tests",
            ],
        },
        {
            "title": "5.6 CI/CD Pipeline Optimization for Parallel Execution",
            "description": """Optimize CI/CD pipeline to leverage new test isolation for parallel execution.

As a DevOps engineer, I need the CI/CD pipeline to run tests in parallel safely so that we get faster feedback cycles.

## Technical Requirements
- Update .github/workflows/ci.yml to use parallel execution
- Add test categorization with pytest markers
- Configure separate execution strategies for different test types
- Add performance monitoring and regression detection
- Implement quality gates based on test execution time

## Implementation Details
- Use pytest -n auto for unit and integration tests
- Run E2E tests sequentially due to subprocess nature
- Add test execution time monitoring
- Configure coverage collection with parallel execution
- Add performance regression alerts if tests slow down""",
            "acceptance_criteria": [
                "CI/CD pipeline updated with parallel execution support",
                "Unit tests run with pytest -n auto flag",
                "Integration tests run with pytest -n auto flag",
                "E2E tests run sequentially with proper isolation",
                "Test execution time monitored and reported",
                "Coverage collection works with parallel execution",
                "Quality gates prevent performance regressions",
                "Overall CI execution time reduced significantly",
            ],
        },
        {
            "title": "5.7 Documentation and Validation Testing",
            "description": """Create comprehensive documentation and validation tests for the new isolation system.

As a team member, I need clear documentation and validation tests so that I can confidently use and maintain the new database isolation system.

## Technical Requirements
- Create tests/test_isolation_validation.py with isolation verification tests
- Update documentation with new testing patterns
- Add troubleshooting guide for isolation issues
- Create examples for different test scenarios
- Add performance benchmarking tests

## Implementation Details
- Test database isolation between test functions
- Test thread safety with concurrent database operations
- Validate production server remains unchanged
- Create examples for unit, integration, and E2E test patterns
- Add benchmarks showing 10x performance improvement""",
            "acceptance_criteria": [
                "Isolation validation tests verify bulletproof separation",
                "Thread safety tests confirm concurrent execution safety",
                "Production server validation confirms zero changes",
                "Documentation includes clear usage examples",
                "Performance benchmarks demonstrate 10x improvement",
                "Troubleshooting guide helps debug isolation issues",
                "All validation tests pass consistently in CI/CD",
            ],
        },
    ]

    print("🚀 Starting Epic 5 creation process...")

    # Start MCP server
    print("📡 Starting MCP server...")
    server_process = create_mcp_server()

    try:
        # Initialize MCP server first
        print("🔧 Initializing MCP server...")
        init_response = send_mcp_request(
            server_process,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "epic-creator", "version": "1.0.0"},
            },
        )

        if "error" in init_response:
            print(f"❌ Error initializing server: {init_response['error']}")
            return

        print("✅ MCP server initialized successfully")

        # Send initialized notification (no response expected)
        print("📡 Sending initialized notification...")
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        request_json = json.dumps(request) + "\n"
        server_process.stdin.write(request_json)
        server_process.stdin.flush()

        # Create Epic 5
        print(
            "📝 Creating Epic 5: E2E Test Failure Remediation & Database Isolation..."
        )
        epic_response = send_mcp_request(
            server_process,
            "tools/call",
            {"name": "backlog.createEpic", "arguments": epic_data},
        )

        if "error" in epic_response:
            print(f"❌ Error creating epic: {epic_response['error']}")
            return

        print(f"📊 Epic creation response: {json.dumps(epic_response, indent=2)}")

        # Parse the epic response - it might be in a different format
        if "result" in epic_response and "content" in epic_response["result"]:
            epic_data_text = epic_response["result"]["content"][0]["text"]
            epic_dict = json.loads(epic_data_text)
            epic_id = epic_dict["id"]
        else:
            epic_id = epic_response["result"]["id"]
        print(f"✅ Epic 5 created successfully with ID: {epic_id}")

        # Create all stories
        story_ids = []
        for i, story_data in enumerate(stories, 1):
            print(f"📖 Creating Story 5.{i}: {story_data['title'][:50]}...")

            story_response = send_mcp_request(
                server_process,
                "tools/call",
                {
                    "name": "backlog.createStory",
                    "arguments": {
                        "epic_id": epic_id,
                        "title": story_data["title"],
                        "description": story_data["description"],
                        "acceptance_criteria": story_data["acceptance_criteria"],
                    },
                },
            )

            if "error" in story_response:
                print(f"❌ Error creating story {i}: {story_response['error']}")
                continue

            # Parse the story response - same format as epic
            if "result" in story_response and "content" in story_response["result"]:
                story_data_text = story_response["result"]["content"][0]["text"]
                story_dict = json.loads(story_data_text)
                story_id = story_dict["id"]
            else:
                story_id = story_response["result"]["id"]
            story_ids.append(story_id)
            print(f"✅ Story 5.{i} created successfully with ID: {story_id}")

        print(f"\n🎉 Epic 5 creation completed!")
        print(f"📊 Summary:")
        print(f"   Epic ID: {epic_id}")
        print(f"   Stories created: {len(story_ids)}")
        print(f"   Story IDs: {story_ids}")

        # Display epic summary
        print(f"\n📋 Epic 5 Summary:")
        print(f"Title: {epic_data['title']}")
        print(f"Total Stories: {len(stories)}")
        print(f"Focus: Database isolation and E2E test reliability")
        print(f"Target: 93.4% → 100% E2E pass rate")

    finally:
        # Cleanup server process
        print("🧹 Cleaning up server process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()
        print("✅ Server cleanup completed")


if __name__ == "__main__":
    main()
