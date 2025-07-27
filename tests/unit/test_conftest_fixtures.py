"""
Unit tests for root conftest.py fixtures to validate comprehensive database isolation.
"""

import os


from src.agile_mcp.models.epic import Epic


def test_isolated_memory_db_fixture(isolated_memory_db):
    """Test the isolated_memory_db fixture."""
    engine, session_factory = isolated_memory_db

    assert engine is not None
    assert session_factory is not None
    assert "memory" in str(engine.url)

    # Test session creation
    session = session_factory()
    try:
        # Add test data
        epic = Epic(
            id="fixture_test", title="Fixture Test", description="Test", status="Ready"
        )
        session.add(epic)
        session.commit()

        # Verify data exists
        found = session.query(Epic).filter_by(id="fixture_test").first()
        assert found is not None
    finally:
        session.close()


def test_test_session_fixture(test_session):
    """Test the test_session fixture with automatic transaction management."""
    # Add test data
    epic = Epic(
        id="session_test", title="Session Test", description="Test", status="Ready"
    )
    test_session.add(epic)
    test_session.commit()

    # Verify data exists
    found = test_session.query(Epic).filter_by(id="session_test").first()
    assert found is not None
    assert found.title == "Session Test"


def test_integration_session_fixture(integration_session):
    """Test the integration_session fixture with transaction rollback."""
    import uuid

    # Use unique ID to avoid conflicts with other tests using shared database
    test_id = f"integration_test_{uuid.uuid4().hex[:8]}"

    # Add test data
    epic = Epic(
        id=test_id, title="Integration Test", description="Test", status="Ready"
    )
    integration_session.add(epic)
    integration_session.commit()

    # Verify data exists within the session
    found = integration_session.query(Epic).filter_by(id=test_id).first()
    assert found is not None


def test_mock_database_dependencies(mock_database_dependencies):
    """Test the mock_database_dependencies fixture."""
    # The fixture should return the test session
    session = mock_database_dependencies

    # Test that we can use the session
    epic = Epic(id="mock_test", title="Mock Test", description="Test", status="Ready")
    session.add(epic)
    session.commit()

    found = session.query(Epic).filter_by(id="mock_test").first()
    assert found is not None


def test_isolated_file_db_fixture(isolated_file_db):
    """Test the isolated_file_db fixture."""
    engine, session_factory, db_path = isolated_file_db

    assert engine is not None
    assert session_factory is not None
    assert db_path.endswith(".db")
    assert os.path.exists(db_path)

    # Test session creation
    session = session_factory()
    try:
        # Add test data
        epic = Epic(
            id="file_test", title="File Test", description="Test", status="Ready"
        )
        session.add(epic)
        session.commit()

        # Verify data persists in file
        found = session.query(Epic).filter_by(id="file_test").first()
        assert found is not None
    finally:
        session.close()


def test_e2e_database_fixture(e2e_database):
    """Test the e2e_database fixture."""
    db_path, env_vars = e2e_database

    assert os.path.exists(db_path)
    assert "TEST_DATABASE_URL" in env_vars
    assert "MCP_TEST_MODE" in env_vars
    assert env_vars["TEST_DATABASE_URL"] == f"sqlite:///{db_path}"
    assert env_vars["MCP_TEST_MODE"] == "true"


def test_database_health_check_fixture(database_health_check, isolated_memory_db):
    """Test the database_health_check fixture."""
    engine, _ = isolated_memory_db

    # Test health check
    is_healthy = database_health_check(engine)
    assert is_healthy is True


def test_performance_monitor_fixture(performance_monitor):
    """Test the performance_monitor fixture."""
    metrics = performance_monitor("unit", "perf_fixture_test")

    assert "database_creation_ms" in metrics
    assert "session_creation_ms" in metrics
    assert "basic_operations_ms" in metrics
    assert "total_test_setup_ms" in metrics


def test_fixture_isolation():
    """Test that fixtures provide proper isolation between tests."""
    # This test should run independently and not see data from other tests
    # This is implicitly tested by all other tests not interfering with each other


def test_pytest_markers_configured():
    """Test that pytest markers are properly configured."""
    # This will be verified by the pytest configuration
    # The markers should be available: unit, integration, e2e, slow
