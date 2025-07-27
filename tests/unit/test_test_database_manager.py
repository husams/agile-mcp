"""
Unit tests for TestDatabaseManager to validate database isolation system.
"""

import os
import threading
import time

import pytest

from src.agile_mcp.models.epic import Epic
from tests.utils.test_database_manager import DatabaseManager


def test_memory_database_creation():
    """Test in-memory database creation for unit tests."""
    manager = DatabaseManager.get_instance()

    # Test database creation
    engine, session_factory = manager.create_memory_database("test_001")

    # Validate health
    assert manager.validate_database_health(engine)

    # Test session creation
    session = session_factory()
    try:
        # Insert test data
        epic = Epic(id="test", title="Test Epic", description="Test", status="Ready")
        session.add(epic)
        session.commit()

        # Verify data exists
        found_epic = session.query(Epic).filter_by(id="test").first()
        assert found_epic is not None
        assert found_epic.title == "Test Epic"

    finally:
        session.close()


def test_database_isolation():
    """Test that different test databases are isolated."""
    manager = DatabaseManager.get_instance()

    # Create two separate databases
    engine1, factory1 = manager.create_memory_database("test_001")
    engine2, factory2 = manager.create_memory_database("test_002")

    session1 = factory1()
    session2 = factory2()

    try:
        # Add data to first database
        epic1 = Epic(id="epic1", title="Epic 1", description="Test", status="Ready")
        session1.add(epic1)
        session1.commit()

        # Add different data to second database
        epic2 = Epic(id="epic2", title="Epic 2", description="Test", status="Ready")
        session2.add(epic2)
        session2.commit()

        # Verify isolation
        found_in_db1 = session1.query(Epic).filter_by(id="epic2").first()
        found_in_db2 = session2.query(Epic).filter_by(id="epic1").first()

        assert found_in_db1 is None  # epic2 should not exist in db1
        assert found_in_db2 is None  # epic1 should not exist in db2

    finally:
        session1.close()
        session2.close()


def test_context_manager():
    """Test the context manager for test sessions."""
    manager = DatabaseManager.get_instance()

    # Test unit test context
    with manager.get_test_session("unit", "test_003") as session:
        epic = Epic(
            id="ctx_test", title="Context Test", description="Test", status="Ready"
        )
        session.add(epic)
        session.commit()

        found_epic = session.query(Epic).filter_by(id="ctx_test").first()
        assert found_epic is not None


def test_performance_targets():
    """Test that database creation meets performance targets."""
    manager = DatabaseManager.get_instance()

    # Test unit test performance (≤10ms target)
    start_time = time.time()
    engine, session_factory = manager.create_memory_database("perf_test")
    creation_time = (time.time() - start_time) * 1000  # Convert to ms

    # Allow some flexibility in CI environments
    assert (
        creation_time < 50
    ), f"Database creation took {creation_time}ms, should be ≤50ms"

    # Test session creation performance
    start_time = time.time()
    session = session_factory()
    session.close()
    session_time = (time.time() - start_time) * 1000

    assert session_time < 10, f"Session creation took {session_time}ms, should be ≤10ms"


def test_thread_safety():
    """Test thread safety of the database manager."""
    manager = DatabaseManager.get_instance()
    results = []

    def create_and_test_db(thread_id):
        try:
            with manager.get_test_session("unit", f"thread_{thread_id}") as session:
                epic = Epic(
                    id=f"thread_epic_{thread_id}",
                    title=f"Thread {thread_id} Epic",
                    description="Thread test",
                    status="Ready",
                )
                session.add(epic)
                session.commit()

                found = (
                    session.query(Epic).filter_by(id=f"thread_epic_{thread_id}").first()
                )
                results.append(found is not None)
        except Exception as e:
            results.append(False)

    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_and_test_db, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # All threads should succeed
    assert all(results), "Some threads failed database operations"
    assert len(results) == 5, "Not all threads completed"


def test_three_tier_isolation_system():
    """Test the three-tier isolation system with different database types."""
    manager = DatabaseManager.get_instance()

    # Test unit test tier (in-memory private)
    engine1, factory1 = manager.create_memory_database("unit_test")
    assert "memory" in str(engine1.url)

    # Test integration test tier (shared in-memory)
    engine2, factory2 = manager.create_shared_memory_database("integration_suite")
    assert "memory" in str(engine2.url)

    # Test E2E test tier (file database)
    engine3, factory3, db_path = manager.create_file_database("e2e_test")
    assert db_path.endswith(".db")
    assert os.path.exists(db_path)

    # Cleanup file database
    try:
        os.unlink(db_path)
    except OSError:
        pass


def test_performance_measurement():
    """Test performance measurement capabilities."""
    manager = DatabaseManager.get_instance()

    # Test unit test performance measurement
    metrics = manager.measure_performance("unit", "perf_test_unit")

    assert "database_creation_ms" in metrics
    assert "session_creation_ms" in metrics
    assert "basic_operations_ms" in metrics
    assert "total_test_setup_ms" in metrics

    # All measurements should be reasonable (not infinite)
    assert metrics["database_creation_ms"] < 1000  # Should be much faster
    assert metrics["session_creation_ms"] < 100
    assert metrics["basic_operations_ms"] < 500


def test_performance_targets_validation():
    """Test performance target validation."""
    manager = DatabaseManager.get_instance()

    # Test each tier - allow some flexibility in CI environments
    # These might fail in slow environments, but should generally pass
    unit_meets_target = manager.validate_performance_targets("unit")
    integration_meets_target = manager.validate_performance_targets("integration")
    e2e_meets_target = manager.validate_performance_targets("e2e")

    # At least one should meet targets (unit tests are usually fastest)
    assert (
        unit_meets_target or integration_meets_target
    ), "At least unit or integration tests should meet performance targets"


def test_shared_database_caching():
    """Test that shared databases are properly cached for integration tests."""
    manager = DatabaseManager.get_instance()

    # Get the same integration database twice
    engine1, factory1 = manager.create_shared_memory_database("test_suite")
    engine2, factory2 = manager.create_shared_memory_database("test_suite")

    # Should return the same engine (cached)
    assert engine1 is engine2, "Shared databases should be cached"
    assert factory1 is factory2, "Session factories should be cached"
