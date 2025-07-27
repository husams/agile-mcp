"""
Unit tests for Epic repository.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base, Epic
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


def test_update_epic_status_success(epic_repository):
    """Test successful epic status update."""
    # Create epic
    epic = epic_repository.create_epic("Test Epic", "Test description")
    original_id = epic.id

    # Update status
    updated_epic = epic_repository.update_epic_status(epic.id, "Ready")

    assert updated_epic is not None
    assert updated_epic.id == original_id
    assert updated_epic.title == "Test Epic"
    assert updated_epic.description == "Test description"
    assert updated_epic.status == "Ready"

    # Verify change persisted in database
    found_epic = epic_repository.find_epic_by_id(epic.id)
    assert found_epic.status == "Ready"


def test_update_epic_status_all_valid_statuses(epic_repository):
    """Test updating epic status to all valid status values."""
    valid_statuses = ["Draft", "Ready", "In Progress", "Done", "On Hold"]

    for status in valid_statuses:
        epic = epic_repository.create_epic(f"Epic {status}", "Test description")
        updated_epic = epic_repository.update_epic_status(epic.id, status)

        assert updated_epic.status == status

        # Verify persistence
        found_epic = epic_repository.find_epic_by_id(epic.id)
        assert found_epic.status == status


def test_update_epic_status_not_found(epic_repository):
    """Test updating status of non-existent epic."""
    non_existent_id = str(uuid.uuid4())

    updated_epic = epic_repository.update_epic_status(non_existent_id, "Ready")

    assert updated_epic is None


def test_update_epic_status_invalid_status_constraint(epic_repository):
    """Test updating epic with invalid status triggers validation error."""
    epic = epic_repository.create_epic("Test Epic", "Test description")

    # This should fail due to Epic model validation
    with pytest.raises(ValueError):
        epic_repository.update_epic_status(epic.id, "InvalidStatus")


def test_update_epic_status_transaction_rollback(epic_repository, in_memory_db):
    """Test that failed update operations rollback properly."""
    # Create epic
    epic = epic_repository.create_epic("Test Epic", "Test description")
    original_status = epic.status

    # Attempt invalid update that should fail and rollback
    try:
        epic_repository.update_epic_status(epic.id, "InvalidStatus")
    except ValueError:
        pass

    # Verify original epic status is unchanged
    found_epic = epic_repository.find_epic_by_id(epic.id)
    assert found_epic.status == original_status


def test_update_epic_status_sequential_updates(epic_repository):
    """Test multiple sequential status updates on same epic."""
    epic = epic_repository.create_epic("Test Epic", "Test description")

    # Draft -> Ready
    updated_epic = epic_repository.update_epic_status(epic.id, "Ready")
    assert updated_epic.status == "Ready"

    # Ready -> In Progress
    updated_epic = epic_repository.update_epic_status(epic.id, "In Progress")
    assert updated_epic.status == "In Progress"

    # In Progress -> Done
    updated_epic = epic_repository.update_epic_status(epic.id, "Done")
    assert updated_epic.status == "Done"

    # Verify final state persisted
    found_epic = epic_repository.find_epic_by_id(epic.id)
    assert found_epic.status == "Done"
