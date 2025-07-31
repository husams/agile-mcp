"""
Unit tests for Project model.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base
from src.agile_mcp.models.project import Project


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_project_creation():
    """Test Project model creation with valid data."""
    project = Project(
        id="test-project-1",
        name="Test Project",
        description="This is a test project description",
    )

    assert project.id == "test-project-1"
    assert project.name == "Test Project"
    assert project.description == "This is a test project description"


def test_project_to_dict():
    """Test Project model to_dict method."""
    project = Project(
        id="test-project-2",
        name="Test Project 2",
        description="Second test project",
    )

    project_dict = project.to_dict()

    expected = {
        "id": "test-project-2",
        "name": "Test Project 2",
        "description": "Second test project",
    }

    assert project_dict == expected


def test_project_repr():
    """Test Project model string representation."""
    project = Project(
        id="test-project-3",
        name="Test Project 3",
        description="Third test project",
    )

    repr_str = repr(project)
    assert "test-project-3" in repr_str
    assert "Test Project 3" in repr_str


def test_project_database_persistence(in_memory_db):
    """Test Project model database persistence."""
    project = Project(
        id="test-project-4",
        name="Persistent Project",
        description="This project should persist in the database",
    )

    # Save to database
    in_memory_db.add(project)
    in_memory_db.commit()

    # Retrieve from database
    retrieved_project = (
        in_memory_db.query(Project).filter_by(id="test-project-4").first()
    )

    assert retrieved_project is not None
    assert retrieved_project.id == "test-project-4"
    assert retrieved_project.name == "Persistent Project"
    assert (
        retrieved_project.description == "This project should persist in the database"
    )


def test_project_name_validation():
    """Test Project model name validation."""
    # Test empty name
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(id="test", name="", description="Valid description")

    # Test whitespace-only name
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(id="test", name="   ", description="Valid description")

    # Test name too long
    long_name = "x" * 201  # Exceeds 200 character limit
    with pytest.raises(ValueError, match="Project name cannot exceed 200 characters"):
        Project(id="test", name=long_name, description="Valid description")


def test_project_description_validation():
    """Test Project model description validation."""
    # Test empty description
    with pytest.raises(ValueError, match="Project description cannot be empty"):
        Project(id="test", name="Valid name", description="")

    # Test whitespace-only description
    with pytest.raises(ValueError, match="Project description cannot be empty"):
        Project(id="test", name="Valid name", description="   ")

    # Test description too long
    long_description = "x" * 2001  # Exceeds 2000 character limit
    with pytest.raises(
        ValueError, match="Project description cannot exceed 2000 characters"
    ):
        Project(id="test", name="Valid name", description=long_description)


def test_project_whitespace_trimming():
    """Test Project model trims whitespace from name and description."""
    project = Project(
        id="test-project-5",
        name="  Test Project  ",
        description="  Test description  ",
    )

    assert project.name == "Test Project"
    assert project.description == "Test description"
