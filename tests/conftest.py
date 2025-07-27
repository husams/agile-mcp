"""
Root pytest configuration with comprehensive database isolation fixtures.

Provides centralized test fixtures using TestDatabaseManager for all test types:
- isolated_memory_db: Function-scoped in-memory isolation for unit tests
- isolated_file_db: Subprocess testing with cleanup for E2E tests
- test_session: Automatic transaction management
- mock_database_dependencies: Comprehensive patching of all database access points
"""

import os
import tempfile
from typing import Generator
from unittest.mock import patch

import pytest

from src.agile_mcp.models.epic import Epic
from tests.utils.test_database_manager import DatabaseManager


@pytest.fixture(scope="function")
def isolated_memory_db():
    """
    Function-scoped in-memory database isolation for unit tests.
    Target performance: ≤10ms per test.

    Returns:
        Tuple of (engine, session_factory)
    """
    manager = DatabaseManager.get_instance()
    engine, session_factory = manager.create_memory_database()

    yield engine, session_factory

    # Cleanup is automatic for in-memory databases


@pytest.fixture(scope="function")
def isolated_file_db():
    """
    Isolated file database for subprocess testing with cleanup.
    Target performance: ≤1s per test.

    Returns:
        Tuple of (engine, session_factory, db_path)
    """
    manager = DatabaseManager.get_instance()
    engine, session_factory, db_path = manager.create_file_database()

    try:
        yield engine, session_factory, db_path
    finally:
        # Cleanup file database
        try:
            os.unlink(db_path)
        except OSError:
            pass  # File may already be deleted


@pytest.fixture(scope="function")
def test_session(isolated_memory_db):
    """
    Test session with automatic transaction management.
    Uses function-scoped in-memory database by default.

    Returns:
        SQLAlchemy Session instance
    """
    engine, session_factory = isolated_memory_db
    session = session_factory()

    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope="function")
def integration_session():
    """
    Integration test session using shared in-memory database.
    Target performance: ≤100ms per test.

    Returns:
        SQLAlchemy Session instance
    """
    manager = DatabaseManager.get_instance()
    engine, session_factory = manager.create_shared_memory_database("integration_suite")
    session = session_factory()

    try:
        yield session
    finally:
        # Always rollback any uncommitted changes and close session
        try:
            session.rollback()
        except Exception:
            pass  # Session may already be in a rolled back state
        session.close()


@pytest.fixture(scope="function")
def e2e_database():
    """
    E2E test database with file persistence for subprocess isolation.
    Target performance: ≤1s per test.

    Returns:
        Tuple of (db_path, environment_variables)
    """
    manager = DatabaseManager.get_instance()
    engine, session_factory, db_path = manager.create_file_database()

    # Create default test data for E2E tests
    session = session_factory()
    try:
        # Add default epic for E2E tests
        default_epic = Epic(
            id="default-epic",
            title="Default Epic",
            description="Default epic for E2E testing",
            status="Ready",
        )
        session.add(default_epic)
        session.commit()
    finally:
        session.close()

    # Environment variables for subprocess
    env_vars = {"TEST_DATABASE_URL": f"sqlite:///{db_path}", "MCP_TEST_MODE": "true"}

    try:
        yield db_path, env_vars
    finally:
        # Cleanup
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def mock_database_dependencies(test_session, monkeypatch):
    """
    Comprehensive patching of all database access points for unit tests.
    Patches get_db at all import locations to use the test session.

    Args:
        test_session: Test session fixture
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        The test session for additional test operations
    """

    def mock_get_db():
        """Mock get_db function that returns the test session."""
        return test_session

    # Patch get_db at all known import locations
    import_locations = [
        "src.agile_mcp.database.get_db",
        "src.agile_mcp.api.backlog_tools.get_db",
        "src.agile_mcp.api.story_tools.get_db",
        "src.agile_mcp.api.epic_tools.get_db",
        "src.agile_mcp.api.artifact_tools.get_db",
        "src.agile_mcp.services.epic_service.get_db",
        "src.agile_mcp.services.story_service.get_db",
        "src.agile_mcp.services.artifact_service.get_db",
        "src.agile_mcp.services.dependency_service.get_db",
    ]

    for location in import_locations:
        try:
            monkeypatch.setattr(location, mock_get_db)
        except AttributeError:
            # Location may not exist or be importable - continue
            pass

    yield test_session


@pytest.fixture(scope="function")
def mock_database_for_integration(integration_session, monkeypatch):
    """
    Database mocking for integration tests using shared in-memory database.

    Args:
        integration_session: Integration test session fixture
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        The integration session for additional test operations
    """

    def mock_get_db():
        """Mock get_db function that returns the integration session."""
        return integration_session

    # Patch get_db at all known import locations
    import_locations = [
        "src.agile_mcp.database.get_db",
        "src.agile_mcp.api.backlog_tools.get_db",
        "src.agile_mcp.api.story_tools.get_db",
        "src.agile_mcp.api.epic_tools.get_db",
        "src.agile_mcp.api.artifact_tools.get_db",
        "src.agile_mcp.services.epic_service.get_db",
        "src.agile_mcp.services.story_service.get_db",
        "src.agile_mcp.services.artifact_service.get_db",
        "src.agile_mcp.services.dependency_service.get_db",
    ]

    for location in import_locations:
        try:
            monkeypatch.setattr(location, mock_get_db)
        except AttributeError:
            # Location may not exist or be importable - continue
            pass

    yield integration_session


@pytest.fixture(scope="function")
def database_health_check():
    """
    Fixture to validate database health before and after tests.

    Returns:
        Function to check database health
    """
    manager = DatabaseManager.get_instance()

    def check_health(engine):
        """Check if database engine is healthy."""
        return manager.validate_database_health(engine)

    return check_health


@pytest.fixture(scope="function")
def performance_monitor():
    """
    Fixture to monitor test database performance.

    Returns:
        Function to measure performance for a test type
    """
    manager = DatabaseManager.get_instance()

    def measure_performance(test_type: str, test_id: str = None):
        """Measure database performance for the given test type."""
        return manager.measure_performance(test_type, test_id)

    return measure_performance


@pytest.fixture(scope="session", autouse=True)
def cleanup_database_manager():
    """
    Session-scoped fixture to cleanup database manager at the end of test session.
    Runs automatically for all test sessions.
    """
    yield

    # Cleanup all cached databases at the end of the test session
    manager = DatabaseManager.get_instance()
    manager.cleanup_all_databases()


# Test markers for the three-tier system
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers for the three-tier isolation system."""
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test (uses in-memory database, ≤10ms target)",
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (uses shared database, ≤100ms target)",
    )
    config.addinivalue_line(
        "markers",
        "e2e: mark test as an end-to-end test (uses file database, ≤1s target)",
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (no performance target)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically apply markers based on test file location.

    - tests/unit/ -> unit marker
    - tests/integration/ -> integration marker
    - tests/e2e/ -> e2e marker
    """
    for item in items:
        # Get the test file path relative to the root
        test_file_path = str(item.fspath.relto(config.rootdir))

        if "tests/unit/" in test_file_path:
            item.add_marker(pytest.mark.unit)
        elif "tests/integration/" in test_file_path:
            item.add_marker(pytest.mark.integration)
        elif "tests/e2e/" in test_file_path:
            item.add_marker(pytest.mark.e2e)
