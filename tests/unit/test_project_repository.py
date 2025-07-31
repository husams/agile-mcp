"""
Unit tests for Project repository layer.
"""

from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base
from src.agile_mcp.models.project import Project
from src.agile_mcp.repositories.project_repository import ProjectRepository


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def project_repository(in_memory_db):
    """Create ProjectRepository with in-memory database session."""
    return ProjectRepository(in_memory_db)


def test_create_project_success(project_repository):
    """Test successful project creation."""
    project = project_repository.create_project("Test Project", "Test description")

    assert project.id is not None  # UUID should be generated
    assert project.name == "Test Project"
    assert project.description == "Test description"


def test_create_project_generates_uuid(project_repository):
    """Test that create_project generates unique UUIDs."""
    project1 = project_repository.create_project("Project 1", "Description 1")
    project2 = project_repository.create_project("Project 2", "Description 2")

    assert project1.id != project2.id
    assert len(project1.id) == 36  # Standard UUID length
    assert len(project2.id) == 36


def test_create_project_database_persistence(project_repository, in_memory_db):
    """Test that created project persists in database."""
    project = project_repository.create_project(
        "Persistent Project", "Persistent description"
    )

    # Verify it's persisted by querying directly
    retrieved = in_memory_db.query(Project).filter_by(id=project.id).first()
    assert retrieved is not None
    assert retrieved.name == "Persistent Project"
    assert retrieved.description == "Persistent description"


def test_find_all_projects_success(project_repository):
    """Test successful retrieval of all projects."""
    # Create test projects
    project1 = project_repository.create_project("Project 1", "Description 1")
    project2 = project_repository.create_project("Project 2", "Description 2")

    # Retrieve all projects
    projects = project_repository.find_all_projects()

    assert len(projects) == 2
    project_ids = [p.id for p in projects]
    assert project1.id in project_ids
    assert project2.id in project_ids


def test_find_all_projects_empty(project_repository):
    """Test retrieval when no projects exist."""
    projects = project_repository.find_all_projects()
    assert projects == []


def test_find_project_by_id_success(project_repository):
    """Test successful project retrieval by ID."""
    # Create a test project
    created_project = project_repository.create_project(
        "Test Project", "Test description"
    )

    # Find the project by ID
    found_project = project_repository.find_project_by_id(created_project.id)

    assert found_project is not None
    assert found_project.id == created_project.id
    assert found_project.name == "Test Project"
    assert found_project.description == "Test description"


def test_find_project_by_id_not_found(project_repository):
    """Test project retrieval by non-existent ID."""
    found_project = project_repository.find_project_by_id("non-existent-id")
    assert found_project is None


def test_create_project_rollback_on_error():
    """Test that transaction is rolled back on database error."""
    mock_session = Mock()
    mock_session.add.side_effect = SQLAlchemyError("Database error")

    repository = ProjectRepository(mock_session)

    with pytest.raises(SQLAlchemyError):
        repository.create_project("Test", "Test description")

    # Verify rollback was called
    mock_session.rollback.assert_called_once()


def test_find_all_projects_database_error():
    """Test find_all_projects with database error."""
    mock_session = Mock()
    mock_session.query.side_effect = SQLAlchemyError("Database error")

    repository = ProjectRepository(mock_session)

    with pytest.raises(SQLAlchemyError):
        repository.find_all_projects()


def test_find_project_by_id_database_error():
    """Test find_project_by_id with database error."""
    mock_session = Mock()
    mock_session.query.side_effect = SQLAlchemyError("Database error")

    repository = ProjectRepository(mock_session)

    with pytest.raises(SQLAlchemyError):
        repository.find_project_by_id("test-id")
