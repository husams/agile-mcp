"""Unit tests for DatabaseIsolationValidator to validate isolation verification."""

import os

from src.agile_mcp.models.epic import Epic
from src.agile_mcp.models.project import Project
from tests.utils.database_isolation_validator import DatabaseIsolationValidator
from tests.utils.test_database_manager import DatabaseManager


def test_validate_clean_database_state():
    """Test clean database state validation."""
    validator = DatabaseIsolationValidator()
    manager = DatabaseManager.get_instance()

    # Test with clean database
    engine, session_factory = manager.create_memory_database("clean_test")
    result = validator.validate_clean_database_state(engine)

    assert result["is_clean"] is True
    assert len(result["issues"]) == 0
    assert all(count == 0 for count in result["table_counts"].values())

    # Test with contaminated database
    session = session_factory()
    try:
        # Add test project first
        project = Project(
            id="contamination-proj",
            name="Contamination Project",
            description="Test project"
        )
        session.add(project)
        
        # Add test data to contaminate
        epic = Epic(
            id="contamination-test",
            title="Contamination",
            description="Test",
            project_id="contamination-proj",
            status="Ready",
        )
        session.add(epic)
        session.commit()

        contaminated_result = validator.validate_clean_database_state(engine)

        assert contaminated_result["is_clean"] is False
        assert len(contaminated_result["issues"]) > 0
        assert contaminated_result["table_counts"]["epics"] > 0
        assert len(contaminated_result["contamination_details"]) > 0

    finally:
        session.close()


def test_validate_production_isolation():
    """Test production isolation validation."""
    validator = DatabaseIsolationValidator()
    manager = DatabaseManager.get_instance()

    # Test with in-memory database (should be isolated)
    engine, _ = manager.create_memory_database("prod_isolation_test")
    result = validator.validate_production_isolation(engine)

    assert result["is_isolated"] is True
    assert result["test_db_info"]["is_memory"] is True

    # Test with file database (should also be isolated if properly named)
    engine_file, _, db_path = manager.create_file_database("prod_isolation_file_test")
    try:
        result_file = validator.validate_production_isolation(engine_file)

        # Should be isolated since it's a temp file with test naming
        assert result_file["is_isolated"] is True
        assert result_file["test_db_info"]["is_temp_file"] is True

    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_validate_test_isolation_between_sessions():
    """Test session isolation validation."""
    validator = DatabaseIsolationValidator()

    # Test unit test isolation
    result = validator.validate_test_isolation_between_sessions("unit")

    assert result["is_isolated"] is True
    assert len(result["session_results"]) == 2
    assert result["session_results"][0]["found_own_data"] is True
    assert result["session_results"][1]["found_other_session_data"] is False

    # Test integration test isolation (may have different behavior)
    integration_result = validator.validate_test_isolation_between_sessions(
        "integration"
    )

    # Integration tests might share data - check for proper documentation
    assert "integration_note" in integration_result

    # Test E2E isolation
    e2e_result = validator.validate_test_isolation_between_sessions("e2e")
    assert e2e_result["is_isolated"] is True


def test_validate_thread_safety():
    """Test thread safety validation."""
    validator = DatabaseIsolationValidator()

    # Test with fewer threads for faster testing
    result = validator.validate_thread_safety("unit", thread_count=3)

    assert result["is_thread_safe"] is True
    assert len(result["thread_results"]) == 3
    assert result["performance_metrics"]["successful_threads"] == 3
    assert result["performance_metrics"]["failed_threads"] == 0

    # Verify all threads succeeded
    for thread_result in result["thread_results"]:
        assert thread_result["success"] is True
        assert thread_result["data_created"] is True
        assert thread_result["data_isolated"] is True
        assert thread_result["execution_time"] > 0


def test_generate_isolation_report():
    """Test comprehensive isolation report generation."""
    validator = DatabaseIsolationValidator()

    # Generate report for unit tests only (faster)
    report = validator.generate_isolation_report(["unit"])

    assert "timestamp" in report
    assert report["overall_status"] in ["PASS", "FAIL"]
    assert "unit" in report["test_types"]
    assert report["summary"]["total_validations"] > 0

    # Check unit test report structure
    unit_report = report["test_types"]["unit"]
    assert "clean_state" in unit_report
    assert "session_isolation" in unit_report
    assert "thread_safety" in unit_report
    assert unit_report["status"] in ["PASS", "FAIL"]


def test_validator_error_handling():
    """Test validator error handling with invalid inputs."""
    validator = DatabaseIsolationValidator()

    # Test with invalid test type - should return result with errors rather than raise
    result = validator.validate_test_isolation_between_sessions("invalid")
    assert result["is_isolated"] is False
    assert len(result["issues"]) > 0

    result2 = validator.validate_thread_safety("invalid")
    assert result2["is_thread_safe"] is False
    assert len(result2["issues"]) > 0


def test_validator_with_closed_engine():
    """Test validator behavior with problematic database connections."""
    validator = DatabaseIsolationValidator()

    # Create an engine with invalid database URL to simulate connection issues
    from sqlalchemy import create_engine

    invalid_engine = create_engine("sqlite:///nonexistent/path/database.db")

    # Should handle connection errors gracefully
    result = validator.validate_clean_database_state(invalid_engine)
    # Result might pass or fail depending on SQLite behavior, but should not crash
    assert isinstance(result["is_clean"], bool)
    assert isinstance(result["issues"], list)


def test_validator_performance_metrics():
    """Test that validator provides meaningful performance metrics."""
    validator = DatabaseIsolationValidator()

    result = validator.validate_thread_safety("unit", thread_count=2)

    metrics = result["performance_metrics"]
    assert "total_execution_time" in metrics
    assert "average_thread_time" in metrics
    assert "max_thread_time" in metrics
    assert "min_thread_time" in metrics
    assert "successful_threads" in metrics
    assert "failed_threads" in metrics

    # Verify reasonable performance metrics
    assert metrics["total_execution_time"] > 0
    assert metrics["average_thread_time"] > 0
    assert metrics["max_thread_time"] >= metrics["min_thread_time"]


def test_validator_contamination_details():
    """Test that validator provides detailed contamination information."""
    validator = DatabaseIsolationValidator()
    manager = DatabaseManager.get_instance()

    # Create contaminated database
    engine, session_factory = manager.create_memory_database(
        "contamination_details_test"
    )
    session = session_factory()

    try:
        # Add test project first
        project = Project(
            id="contamination-details-proj",
            name="Contamination Details Project",
            description="Test project for contamination details"
        )
        session.add(project)
        
        # Add multiple contamination records
        for i in range(3):
            epic = Epic(
                id=f"contamination-{i}",
                title=f"Contamination {i}",
                description=f"Contamination record {i}",
                project_id="contamination-details-proj",
                status="Ready",
            )
            session.add(epic)
        session.commit()

        result = validator.validate_clean_database_state(engine)

        assert result["is_clean"] is False
        assert len(result["contamination_details"]) > 0

        # Check contamination details structure
        contamination = result["contamination_details"][0]
        assert "table" in contamination
        assert "count" in contamination
        assert "sample_records" in contamination
        assert contamination["count"] == 3
        assert len(contamination["sample_records"]) <= 3  # Limited by LIMIT 3

    finally:
        session.close()
