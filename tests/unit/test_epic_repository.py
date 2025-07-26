"""
Unit tests for Epic repository.
"""

import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from src.agile_mcp.models.epic import Epic, Base
from src.agile_mcp.repositories.epic_repository import EpicRepository


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
def epic_repository(in_memory_db):
    """Create Epic repository with test database session."""
    return EpicRepository(in_memory_db)


def test_create_epic(epic_repository):
    """Test epic creation through repository."""
    epic = epic_repository.create_epic("Test Epic", "Test description")
    
    assert epic.id is not None
    assert epic.title == "Test Epic"
    assert epic.description == "Test description"
    assert epic.status == "Draft"
    
    # Verify UUID format
    uuid.UUID(epic.id)  # This will raise ValueError if not valid UUID


def test_find_all_epics_empty(epic_repository):
    """Test finding all epics when database is empty."""
    epics = epic_repository.find_all_epics()
    assert epics == []


def test_find_all_epics_with_data(epic_repository):
    """Test finding all epics with existing data."""
    # Create test epics
    epic1 = epic_repository.create_epic("Epic 1", "Description 1")
    epic2 = epic_repository.create_epic("Epic 2", "Description 2")
    epic3 = epic_repository.create_epic("Epic 3", "Description 3")
    
    # Retrieve all epics
    epics = epic_repository.find_all_epics()
    
    assert len(epics) == 3
    epic_ids = [epic.id for epic in epics]
    assert epic1.id in epic_ids
    assert epic2.id in epic_ids
    assert epic3.id in epic_ids


def test_find_epic_by_id_exists(epic_repository):
    """Test finding epic by ID when it exists."""
    created_epic = epic_repository.create_epic("Findable Epic", "Can be found")
    
    found_epic = epic_repository.find_epic_by_id(created_epic.id)
    
    assert found_epic is not None
    assert found_epic.id == created_epic.id
    assert found_epic.title == "Findable Epic"
    assert found_epic.description == "Can be found"


def test_find_epic_by_id_not_exists(epic_repository):
    """Test finding epic by ID when it doesn't exist."""
    non_existent_id = str(uuid.uuid4())
    
    found_epic = epic_repository.find_epic_by_id(non_existent_id)
    
    assert found_epic is None


def test_create_epic_generates_unique_ids(epic_repository):
    """Test that multiple epic creations generate unique IDs."""
    epic1 = epic_repository.create_epic("Epic 1", "Description 1")
    epic2 = epic_repository.create_epic("Epic 2", "Description 2")
    epic3 = epic_repository.create_epic("Epic 3", "Description 3")
    
    assert epic1.id != epic2.id
    assert epic2.id != epic3.id
    assert epic1.id != epic3.id