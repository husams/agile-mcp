"""
TestDatabaseManager - Comprehensive test-only database isolation system.

Provides thread-safe database session management with automatic cleanup for
all test types.
Implements three-tier isolation system:
- In-memory SQLite for unit tests (≤10ms)
- Shared in-memory for integration tests (≤100ms)
- Isolated file databases for E2E tests (≤1s)
"""

import os
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.agile_mcp.models.epic import Base


class DatabaseManager:
    """Thread-safe database manager for comprehensive test isolation."""

    _instance: Optional["DatabaseManager"] = None
    _instance_lock = threading.Lock()
    _engines: Dict[str, Engine] = {}
    _session_factories: Dict[str, sessionmaker] = {}

    def __init__(self):
        """Initialize the test database manager."""
        self._local = threading.local()

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """Get singleton instance with thread safety."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def create_memory_database(
        self, test_id: Optional[str] = None
    ) -> Tuple[Engine, sessionmaker]:
        """Create an in-memory SQLite database for unit tests.

        Target performance: ≤10ms per test.

        Args:
            test_id: Optional unique test identifier for isolation

        Returns:
            Tuple of (engine, session_factory)
        """
        if test_id is None:
            test_id = str(uuid.uuid4())

        # Always create a new isolated database for each test
        # - no caching for unit tests
        # Use unique identifier to ensure complete isolation
        unique_id = f"{test_id}_{uuid.uuid4().hex[:8]}"
        db_url = f"sqlite:///:memory:?cache=private&uri=true&test_id={unique_id}"

        engine = create_engine(
            db_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False, "uri": True},
            echo=False,
        )

        # Create all tables
        Base.metadata.create_all(engine)

        # Create session factory
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        return engine, session_factory

    def create_shared_memory_database(
        self, test_suite_id: str = "integration"
    ) -> Tuple[Engine, sessionmaker]:
        """Create a shared in-memory SQLite database for integration tests.

        Target performance: ≤100ms per test.

        Args:
            test_suite_id: Identifier for the test suite sharing this database

        Returns:
            Tuple of (engine, session_factory)
        """
        cache_key = f"shared_memory_{test_suite_id}"

        if cache_key not in self._engines:
            # Create shared in-memory database with cache=shared
            # for integration tests
            # This allows multiple sessions to share the same database
            # within a test suite
            db_url = (
                f"sqlite:///:memory:?cache=shared&uri=true&" f"suite_id={test_suite_id}"
            )

            engine = create_engine(
                db_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False, "uri": True},
                echo=False,
            )

            # Create all tables
            Base.metadata.create_all(engine)

            # Create session factory with transaction support
            # for integration tests
            session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )

            self._engines[cache_key] = engine
            self._session_factories[cache_key] = session_factory

        return self._engines[cache_key], self._session_factories[cache_key]

    def create_file_database(
        self, test_id: Optional[str] = None
    ) -> Tuple[Engine, sessionmaker, str]:
        """Create an isolated file database for E2E tests.

        Target performance: ≤1s per test.

        Args:
            test_id: Optional unique test identifier

        Returns:
            Tuple of (engine, session_factory, file_path)
        """
        if test_id is None:
            test_id = str(uuid.uuid4())

        # Create temporary file for database
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{test_id}.db", prefix="test_agile_mcp_"
        )
        db_path = temp_file.name
        temp_file.close()

        cache_key = f"file_{test_id}"

        # Create file-based SQLite engine
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(
            db_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Create all tables
        Base.metadata.create_all(engine)

        # Create session factory
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        self._engines[cache_key] = engine
        self._session_factories[cache_key] = session_factory

        return engine, session_factory, db_path

    @contextmanager
    def get_test_session(self, test_type: str = "unit", test_id: Optional[str] = None):
        """
        Context manager for getting a test session with automatic cleanup.

        Args:
            test_type: Type of test ("unit", "integration", "e2e")
            test_id: Optional unique test identifier

        Yields:
            SQLAlchemy Session instance
        """
        if test_type == "unit":
            engine, session_factory = self.create_memory_database(test_id)
        elif test_type == "integration":
            engine, session_factory = self.create_shared_memory_database()
        elif test_type == "e2e":
            engine, session_factory, db_path = self.create_file_database(test_id)
        else:
            raise ValueError(f"Unknown test type: {test_type}")

        session = session_factory()

        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

            # Cleanup file database if E2E test
            if test_type == "e2e" and "db_path" in locals():
                try:
                    os.unlink(db_path)
                except OSError:
                    pass  # File may already be deleted

    def validate_database_health(self, engine: Engine) -> bool:
        """
        Validate database connection and schema health.

        Args:
            engine: SQLAlchemy engine to validate

        Returns:
            True if database is healthy, False otherwise
        """
        try:
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if result is None or result[0] != 1:
                    return False

            # Validate table creation
            metadata = Base.metadata
            missing_tables = []

            with engine.connect() as conn:
                for table_name in metadata.tables.keys():
                    try:
                        conn.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        ).fetchone()
                    except Exception:
                        missing_tables.append(table_name)

            if missing_tables:
                # Recreate missing tables
                metadata.create_all(engine)

            return True

        except Exception:
            return False

    def cleanup_all_databases(self):
        """Clean up all cached database engines and sessions."""
        with self._instance_lock:
            # Close all engines
            for engine in self._engines.values():
                engine.dispose()

            # Clear caches
            self._engines.clear()
            self._session_factories.clear()

    def get_database_info(self, engine: Engine) -> Dict[str, Any]:
        """
        Get diagnostic information about a database.

        Args:
            engine: SQLAlchemy engine to inspect

        Returns:
            Dictionary with database information
        """
        info = {
            "url": str(engine.url),
            "pool_class": engine.pool.__class__.__name__,
            "tables": [],
            "connection_count": 0,
        }

        try:
            # Get table information
            metadata = Base.metadata
            info["tables"] = list(metadata.tables.keys())

            # Get connection pool information
            if hasattr(engine.pool, "size"):
                info["connection_count"] = engine.pool.size()

        except Exception as e:
            info["error"] = str(e)

        return info

    def measure_performance(
        self, test_type: str, test_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Measure database performance for the specified test type.

        Args:
            test_type: Type of test ("unit", "integration", "e2e")
            test_id: Optional unique test identifier

        Returns:
            Dictionary with performance metrics in milliseconds
        """
        metrics: Dict[str, Any] = {}

        # Measure database creation time
        start_time = time.time()
        if test_type == "unit":
            engine, session_factory = self.create_memory_database(test_id)
        elif test_type == "integration":
            engine, session_factory = self.create_shared_memory_database()
        elif test_type == "e2e":
            engine, session_factory, db_path = self.create_file_database(test_id)
        else:
            raise ValueError(f"Unknown test type: {test_type}")

        metrics["database_creation_ms"] = (time.time() - start_time) * 1000

        # Measure session creation time
        start_time = time.time()
        session = session_factory()
        metrics["session_creation_ms"] = (time.time() - start_time) * 1000

        # Measure basic database operation time
        start_time = time.time()
        try:
            # Simple insert operation for performance testing
            from src.agile_mcp.models.epic import Epic

            test_epic = Epic(
                id=f"perf_test_{uuid.uuid4().hex[:8]}",
                title="Performance Test Epic",
                description="Test epic for performance measurement",
                status="Ready",
            )
            session.add(test_epic)
            session.commit()

            # Simple query operation
            found_epic = session.query(Epic).filter_by(id=test_epic.id).first()
            assert found_epic is not None

            metrics["basic_operations_ms"] = (time.time() - start_time) * 1000

        except Exception as e:
            metrics["basic_operations_error"] = str(e)
            metrics["basic_operations_ms"] = float("inf")
        finally:
            session.close()

            # Cleanup E2E test file
            if test_type == "e2e" and "db_path" in locals():
                try:
                    os.unlink(db_path)
                except OSError:
                    pass

        # Calculate total time
        metrics["total_test_setup_ms"] = (
            metrics.get("database_creation_ms", 0)
            + metrics.get("session_creation_ms", 0)
            + metrics.get("basic_operations_ms", 0)
        )

        return metrics

    def validate_performance_targets(self, test_type: str) -> bool:
        """
        Validate that performance meets the specified targets.

        Args:
            test_type: Type of test ("unit", "integration", "e2e")

        Returns:
            True if performance targets are met, False otherwise
        """
        # Define performance targets in milliseconds
        targets = {
            "unit": 10,  # ≤10ms for unit tests
            "integration": 100,  # ≤100ms for integration tests
            "e2e": 1000,  # ≤1s for E2E tests
        }

        if test_type not in targets:
            return False

        try:
            metrics = self.measure_performance(test_type)
            total_time = metrics.get("total_test_setup_ms", float("inf"))
            target_time = targets[test_type]

            return total_time <= target_time

        except Exception:
            return False
