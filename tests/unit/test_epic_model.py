"""
Unit tests for Epic model.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base, Epic


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_epic_creation():
    """Test Epic model creation with valid data."""
    epic = Epic(
        id="test-epic-1",
        title="Test Epic",
        description="This is a test epic description",
        project_id="test-project-1",
        status="Draft",
    )

    assert epic.id == "test-epic-1"
    assert epic.title == "Test Epic"
    assert epic.description == "This is a test epic description"
    assert epic.project_id == "test-project-1"
    assert epic.status == "Draft"


def test_epic_default_status():
    """Test Epic model uses default status of 'Draft'."""
    epic = Epic(
        id="test-epic-2",
        title="Test Epic 2",
        description="Another test epic",
        project_id="test-project-2",
    )

    assert epic.status == "Draft"


def test_epic_to_dict():
    """Test Epic model to_dict method."""
    epic = Epic(
        id="test-epic-3",
        title="Test Epic 3",
        description="Third test epic",
        project_id="test-project-3",
        status="In Progress",
    )

    epic_dict = epic.to_dict()

    expected = {
        "id": "test-epic-3",
        "title": "Test Epic 3",
        "description": "Third test epic",
        "status": "In Progress",
        "project_id": "test-project-3",
    }

    assert epic_dict == expected


def test_epic_repr():
    """Test Epic model string representation."""
    epic = Epic(
        id="test-epic-4",
        title="Test Epic 4",
        description="Fourth test epic",
        project_id="test-project-4",
        status="Done",
    )

    repr_str = repr(epic)
    assert "test-epic-4" in repr_str
    assert "Test Epic 4" in repr_str
    assert "Done" in repr_str


def test_epic_database_persistence(in_memory_db):
    """Test Epic model database persistence."""
    epic = Epic(
        id="test-epic-5",
        title="Persistent Epic",
        description="This epic should persist in the database",
        project_id="test-project-5",
        status="Ready",
    )

    # Save to database
    in_memory_db.add(epic)
    in_memory_db.commit()

    # Retrieve from database
    retrieved_epic = in_memory_db.query(Epic).filter_by(id="test-epic-5").first()

    assert retrieved_epic is not None
    assert retrieved_epic.id == "test-epic-5"
    assert retrieved_epic.title == "Persistent Epic"
    assert retrieved_epic.description == "This epic should persist in the database"
    assert retrieved_epic.project_id == "test-project-5"
    assert retrieved_epic.status == "Ready"
