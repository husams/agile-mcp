"""
DatabaseIsolationValidator - Verify database isolation is working correctly.

Provides validation methods for clean database state and production isolation,
ensuring that test database isolation prevents cross-test contamination.
"""

import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.agile_mcp.models.epic import Epic
from tests.utils.test_database_manager import DatabaseManager


class DatabaseIsolationValidator:
    """Validator class for verifying database isolation is working correctly."""

    def __init__(self):
        """Initialize the database isolation validator."""
        self.manager = DatabaseManager.get_instance()

    def validate_clean_database_state(self, engine: Engine) -> Dict[str, Any]:
        """
        Validate that a database is in a clean state with no test data contamination.

        Args:
            engine: SQLAlchemy engine to validate

        Returns:
            Dictionary with validation results and any issues found
        """
        validation_result: Dict[str, Any] = {
            "is_clean": True,
            "issues": [],
            "table_counts": {},
            "contamination_details": [],
        }

        try:
            with engine.connect() as conn:
                # Check each table for data
                tables_to_check = [
                    "epics",
                    "stories",
                    "artifacts",
                    "story_dependencies",
                ]

                for table_name in tables_to_check:
                    try:
                        result = conn.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        ).scalar()
                        validation_result["table_counts"][table_name] = result

                        if result is not None and result > 0:
                            validation_result["is_clean"] = False
                            validation_result["issues"].append(
                                f"Table {table_name} contains {result} records"
                            )

                            # Get sample contamination data
                            sample_result = conn.execute(
                                text(f"SELECT * FROM {table_name} LIMIT 3")
                            ).fetchall()
                            validation_result["contamination_details"].append(
                                {
                                    "table": table_name,
                                    "count": result,
                                    "sample_records": [
                                        dict(row._mapping) for row in sample_result
                                    ],
                                }
                            )

                    except Exception as e:
                        validation_result["issues"].append(
                            f"Error checking table {table_name}: {str(e)}"
                        )

        except Exception as e:
            validation_result["is_clean"] = False
            validation_result["issues"].append(f"Database connection error: {str(e)}")

        return validation_result

    def validate_production_isolation(self, test_engine: Engine) -> Dict[str, Any]:
        """
        Validate that test database is properly isolated from production.

        Args:
            test_engine: Test database engine to validate

        Returns:
            Dictionary with isolation validation results
        """
        validation_result: Dict[str, Any] = {
            "is_isolated": True,
            "issues": [],
            "test_db_info": {},
            "production_db_info": {},
        }

        try:
            # Get test database information
            test_url = str(test_engine.url)
            validation_result["test_db_info"] = {
                "url": test_url,
                "database_type": test_engine.url.drivername,
                "is_memory": ":memory:" in test_url,
                "is_temp_file": "/tmp" in test_url or "test_" in test_url,
            }

            # Check if test database is using production database file
            production_db_path = "agile_mcp.db"
            if (
                production_db_path in test_url
                and not validation_result["test_db_info"]["is_memory"]
            ):
                validation_result["is_isolated"] = False
                validation_result["issues"].append(
                    "Test database is using production database file"
                )

            # Validate test environment markers
            test_mode = os.getenv("MCP_TEST_MODE")
            if not test_mode:
                validation_result["issues"].append(
                    "MCP_TEST_MODE environment variable not set"
                )

            # Check for test database URL override
            test_db_url = os.getenv("TEST_DATABASE_URL")
            if test_db_url and production_db_path in test_db_url:
                validation_result["is_isolated"] = False
                validation_result["issues"].append(
                    "TEST_DATABASE_URL points to production database"
                )

        except Exception as e:
            validation_result["is_isolated"] = False
            validation_result["issues"].append(f"Isolation validation error: {str(e)}")

        return validation_result

    def validate_test_isolation_between_sessions(
        self, test_type: str = "unit"
    ) -> Dict[str, Any]:
        """
        Validate that different test sessions are properly isolated from each other.

        Args:
            test_type: Type of test ("unit", "integration", "e2e")

        Returns:
            Dictionary with cross-session isolation validation results
        """
        validation_result: Dict[str, Any] = {
            "is_isolated": True,
            "issues": [],
            "session_results": [],
            "cross_contamination": [],
        }

        try:
            # Create two separate database sessions
            if test_type == "unit":
                engine1, factory1 = self.manager.create_memory_database(
                    "isolation_test_1"
                )
                engine2, factory2 = self.manager.create_memory_database(
                    "isolation_test_2"
                )
            elif test_type == "integration":
                engine1, factory1 = self.manager.create_shared_memory_database(
                    "isolation_suite_1"
                )
                engine2, factory2 = self.manager.create_shared_memory_database(
                    "isolation_suite_2"
                )
            elif test_type == "e2e":
                engine1, factory1, path1 = self.manager.create_file_database(
                    "isolation_test_1"
                )
                engine2, factory2, path2 = self.manager.create_file_database(
                    "isolation_test_2"
                )
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            # Test isolation by adding data to first session
            session1 = factory1()
            session2 = factory2()

            try:
                # Add test data to first session with unique ID to avoid conflicts
                test_id = uuid.uuid4().hex[:8]
                epic1 = Epic(
                    id=f"isolation-test-epic-{test_id}",
                    title=f"Isolation Test Epic {test_id}",
                    description="Epic for isolation testing",
                    status="Ready",
                )
                session1.add(epic1)
                session1.commit()

                # Verify data exists in first session
                found_in_session1 = (
                    session1.query(Epic)
                    .filter_by(id=f"isolation-test-epic-{test_id}")
                    .first()
                )
                validation_result["session_results"].append(
                    {"session": 1, "found_own_data": found_in_session1 is not None}
                )

                # Verify data does NOT exist in second session (for unit/e2e tests)
                found_in_session2 = (
                    session2.query(Epic)
                    .filter_by(id=f"isolation-test-epic-{test_id}")
                    .first()
                )
                session2_contaminated = found_in_session2 is not None

                validation_result["session_results"].append(
                    {"session": 2, "found_other_session_data": session2_contaminated}
                )

                if session2_contaminated and test_type in ["unit", "e2e"]:
                    validation_result["is_isolated"] = False
                    validation_result["issues"].append(
                        "Cross-session contamination detected"
                    )
                    validation_result["cross_contamination"].append(
                        {
                            "from_session": 1,
                            "to_session": 2,
                            "contaminated_data": f"isolation-test-epic-{test_id}",
                        }
                    )

                # For integration tests, cross-session visibility might be expected
                # depending on implementation - document this in results
                if test_type == "integration":
                    validation_result["integration_note"] = (
                        "Integration tests may share data depending on configuration"
                    )

            finally:
                session1.close()
                session2.close()

                # Cleanup E2E test files
                if test_type == "e2e":
                    for path in [path1, path2]:
                        try:
                            os.unlink(path)
                        except OSError:
                            pass

        except Exception as e:
            validation_result["is_isolated"] = False
            validation_result["issues"].append(
                f"Session isolation validation error: {str(e)}"
            )

        return validation_result

    def validate_thread_safety(
        self, test_type: str = "unit", thread_count: int = 5
    ) -> Dict[str, Any]:
        """
        Validate that database isolation works correctly with concurrent access.

        Args:
            test_type: Type of test ("unit", "integration", "e2e")
            thread_count: Number of concurrent threads to test

        Returns:
            Dictionary with thread safety validation results
        """
        validation_result: Dict[str, Any] = {
            "is_thread_safe": True,
            "issues": [],
            "thread_results": [],
            "performance_metrics": {},
        }

        results_lock = threading.Lock()
        thread_results = []

        def thread_test_function(thread_id: int):
            """Run function in each thread for testing."""
            thread_result: Dict[str, Any] = {
                "thread_id": thread_id,
                "success": False,
                "error": None,
                "data_created": False,
                "data_isolated": True,
                "execution_time": 0,
            }

            start_time = time.time()

            try:
                # Create database session for this thread
                if test_type == "unit":
                    engine, factory = self.manager.create_memory_database(
                        f"thread_test_{thread_id}"
                    )
                elif test_type == "integration":
                    engine, factory = self.manager.create_shared_memory_database(
                        f"thread_suite_{thread_id}"
                    )
                elif test_type == "e2e":
                    engine, factory, db_path = self.manager.create_file_database(
                        f"thread_test_{thread_id}"
                    )
                else:
                    raise ValueError(f"Unknown test type: {test_type}")

                session = factory()

                try:
                    # Create unique test data for this thread
                    epic = Epic(
                        id=f"thread-epic-{thread_id}",
                        title=f"Thread {thread_id} Epic",
                        description=f"Epic created by thread {thread_id}",
                        status="Ready",
                    )
                    session.add(epic)
                    session.commit()
                    thread_result["data_created"] = True

                    # Verify data exists
                    found = (
                        session.query(Epic)
                        .filter_by(id=f"thread-epic-{thread_id}")
                        .first()
                    )
                    if found is None:
                        thread_result["error"] = "Created data not found"
                        thread_result["data_isolated"] = False
                    else:
                        thread_result["success"] = True

                finally:
                    session.close()

                    # Cleanup E2E test file
                    if test_type == "e2e" and "db_path" in locals():
                        try:
                            os.unlink(db_path)
                        except OSError:
                            pass

            except Exception as e:
                thread_result["error"] = str(e)

            thread_result["execution_time"] = time.time() - start_time

            with results_lock:
                thread_results.append(thread_result)

        # Start all threads
        threads = []
        overall_start_time = time.time()

        for i in range(thread_count):
            thread = threading.Thread(target=thread_test_function, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        overall_execution_time = time.time() - overall_start_time

        # Process results
        validation_result["thread_results"] = thread_results
        successful_threads = sum(1 for result in thread_results if result["success"])
        failed_threads = thread_count - successful_threads

        if failed_threads > 0:
            validation_result["is_thread_safe"] = False
            validation_result["issues"].append(
                f"{failed_threads} out of {thread_count} threads failed"
            )

        # Performance metrics
        execution_times = [
            result["execution_time"]
            for result in thread_results
            if "execution_time" in result and result["execution_time"] is not None
        ]
        validation_result["performance_metrics"] = {
            "total_execution_time": overall_execution_time,
            "successful_threads": successful_threads,
            "failed_threads": failed_threads,
            "average_thread_time": (
                sum(execution_times) / len(execution_times) if execution_times else 0
            ),
            "max_thread_time": max(execution_times) if execution_times else 0,
            "min_thread_time": min(execution_times) if execution_times else 0,
        }

        return validation_result

    def generate_isolation_report(
        self, test_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive isolation validation report for all test types.

        Args:
            test_types: List of test types to validate (default: all types)

        Returns:
            Dictionary with comprehensive isolation report
        """
        if test_types is None:
            test_types = ["unit", "integration", "e2e"]

        report: Dict[str, Any] = {
            "timestamp": time.time(),
            "overall_status": "PASS",
            "test_types": {},
            "summary": {
                "total_validations": 0,
                "passed_validations": 0,
                "failed_validations": 0,
                "issues": [],
            },
        }

        for test_type in test_types:
            type_report: Dict[str, Any] = {
                "clean_state": self.validate_clean_database_state(
                    self.manager.create_memory_database(f"clean_test_{test_type}")[0]
                ),
                "session_isolation": self.validate_test_isolation_between_sessions(
                    test_type
                ),
                "thread_safety": self.validate_thread_safety(test_type, thread_count=3),
            }

            # Check production isolation for file-based tests
            if test_type == "e2e":
                engine, _, db_path = self.manager.create_file_database(
                    "prod_isolation_test"
                )
                type_report["production_isolation"] = (
                    self.validate_production_isolation(engine)
                )
                try:
                    os.unlink(db_path)
                except OSError:
                    pass

            # Count validations
            validations_in_type = len(type_report)
            report["summary"]["total_validations"] += validations_in_type

            # Check if all validations passed
            all_passed = True
            for validation_name, validation_result in type_report.items():
                if isinstance(validation_result, dict):
                    passed = (
                        validation_result.get("is_clean", True)
                        and validation_result.get("is_isolated", True)
                        and validation_result.get("is_thread_safe", True)
                    )
                    if not passed:
                        all_passed = False
                        issues = validation_result.get("issues", [])
                        report["summary"]["issues"].extend(
                            [
                                f"{test_type}.{validation_name}: {issue}"
                                for issue in issues
                            ]
                        )

            if all_passed:
                report["summary"]["passed_validations"] += 1
                type_report["status"] = "PASS"
            else:
                report["summary"]["failed_validations"] += 1
                type_report["status"] = "FAIL"
                report["overall_status"] = "FAIL"

            report["test_types"][test_type] = type_report

        return report
