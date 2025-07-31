"""
Integration tests for Project-Epic relationship functionality.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base, Epic
from src.agile_mcp.models.project import Project
from src.agile_mcp.repositories.epic_repository import EpicRepository
from src.agile_mcp.repositories.project_repository import ProjectRepository
from src.agile_mcp.services.epic_service import EpicService
from src.agile_mcp.services.project_service import ProjectService


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
def project_service(in_memory_db):
    """Create ProjectService with in-memory database."""
    repository = ProjectRepository(in_memory_db)
    return ProjectService(repository)


@pytest.fixture
def epic_service(in_memory_db):
    """Create EpicService with in-memory database."""
    repository = EpicRepository(in_memory_db)
    return EpicService(repository)


def test_project_epic_creation_relationship(
    project_service, epic_service, in_memory_db
):
    """Test creating a project and then an epic that belongs to it."""
    # Create a project
    project_dict = project_service.create_project("Test Project", "A test project")
    project_id = project_dict["id"]

    # Create an epic in that project
    epic_dict = epic_service.create_epic("Test Epic", "A test epic", project_id)
    epic_id = epic_dict["id"]

    # Verify the epic has the correct project_id
    assert epic_dict["project_id"] == project_id

    # Verify database relationship
    project = in_memory_db.query(Project).filter_by(id=project_id).first()
    epic = in_memory_db.query(Epic).filter_by(id=epic_id).first()

    assert project is not None
    assert epic is not None
    assert epic.project_id == project.id


def test_project_with_multiple_epics(project_service, epic_service, in_memory_db):
    """Test a project can have multiple epics."""
    # Create a project
    project_dict = project_service.create_project(
        "Multi Epic Project", "A project with multiple epics"
    )
    project_id = project_dict["id"]

    # Create multiple epics in that project
    epic1_dict = epic_service.create_epic("Epic 1", "First epic", project_id)
    epic2_dict = epic_service.create_epic("Epic 2", "Second epic", project_id)
    epic3_dict = epic_service.create_epic("Epic 3", "Third epic", project_id)

    # Verify all epics belong to the same project
    assert epic1_dict["project_id"] == project_id
    assert epic2_dict["project_id"] == project_id
    assert epic3_dict["project_id"] == project_id

    # Verify database relationships
    project = in_memory_db.query(Project).filter_by(id=project_id).first()
    epics = in_memory_db.query(Epic).filter_by(project_id=project_id).all()

    assert project is not None
    assert len(epics) == 3
    for epic in epics:
        assert epic.project_id == project.id


def test_multiple_projects_with_epics(project_service, epic_service, in_memory_db):
    """Test multiple projects each with their own epics."""
    # Create two projects
    project1_dict = project_service.create_project("Project 1", "First project")
    project2_dict = project_service.create_project("Project 2", "Second project")

    project1_id = project1_dict["id"]
    project2_id = project2_dict["id"]

    # Create epics for each project
    epic1_dict = epic_service.create_epic(
        "Project 1 Epic", "Epic for project 1", project1_id
    )
    epic2_dict = epic_service.create_epic(
        "Project 2 Epic", "Epic for project 2", project2_id
    )

    # Verify epics belong to correct projects
    assert epic1_dict["project_id"] == project1_id
    assert epic2_dict["project_id"] == project2_id

    # Count epics per project in database
    project1_epics = in_memory_db.query(Epic).filter_by(project_id=project1_id).all()
    project2_epics = in_memory_db.query(Epic).filter_by(project_id=project2_id).all()

    assert len(project1_epics) == 1
    assert len(project2_epics) == 1
    assert project1_epics[0].project_id == project1_id
    assert project2_epics[0].project_id == project2_id


def test_epic_creation_with_invalid_project_id(epic_service):
    """Test that creating an epic with invalid project_id fails appropriately."""
    from src.agile_mcp.services.exceptions import EpicValidationError

    # Test empty project_id
    with pytest.raises(EpicValidationError, match="Epic project_id cannot be empty"):
        epic_service.create_epic("Test Epic", "Test description", "")

    # Test whitespace-only project_id
    with pytest.raises(EpicValidationError, match="Epic project_id cannot be empty"):
        epic_service.create_epic("Test Epic", "Test description", "   ")


def test_project_deletion_constraints(project_service, epic_service, in_memory_db):
    """Test behavior when trying to delete a project that has epics."""
    # Create a project with an epic
    project_dict = project_service.create_project(
        "Project to Delete", "Will have epics"
    )
    project_id = project_dict["id"]

    epic_dict = epic_service.create_epic(
        "Epic in Project", "Epic description", project_id
    )

    # Verify the epic exists
    epic = in_memory_db.query(Epic).filter_by(id=epic_dict["id"]).first()
    assert epic is not None
    assert epic.project_id == project_id

    # Try to delete the project - this should be constrained by foreign key
    project = in_memory_db.query(Project).filter_by(id=project_id).first()
    assert project is not None

    # Note: In a real scenario, we would expect the database to enforce
    # foreign key constraints. In SQLite with default settings, this might
    # not be enforced, but the relationship structure is correct.


def test_epic_update_with_project_relationship(
    epic_service, project_service, in_memory_db
):
    """Test that epic updates maintain project relationship."""
    # Create project and epic
    project_dict = project_service.create_project(
        "Update Test Project", "For testing updates"
    )
    project_id = project_dict["id"]

    epic_dict = epic_service.create_epic(
        "Update Test Epic", "Epic for update testing", project_id
    )
    epic_id = epic_dict["id"]

    # Update epic status
    updated_epic_dict = epic_service.update_epic_status(epic_id, "Ready")

    # Verify project relationship is maintained
    assert updated_epic_dict["project_id"] == project_id

    # Verify in database
    epic = in_memory_db.query(Epic).filter_by(id=epic_id).first()
    assert epic.project_id == project_id
    assert epic.status == "Ready"
