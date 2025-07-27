"""
Unit tests for Dependency repository layer.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.agile_mcp.models.epic import Base
from src.agile_mcp.models.story import Story
from src.agile_mcp.models.epic import Epic
from src.agile_mcp.repositories.dependency_repository import DependencyRepository


@pytest.fixture
def test_engine():
    """Create in-memory SQLite engine for testing."""
    from sqlalchemy import event
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def dependency_repository(test_session):
    """Create DependencyRepository with test session."""
    return DependencyRepository(test_session)


@pytest.fixture
def test_stories(test_session):
    """Create test stories for dependency testing."""
    # Create test epic first
    epic = Epic(
        id="test-epic-1",
        title="Test Epic",
        description="Epic for testing",
        status="Ready"
    )
    test_session.add(epic)
    
    # Create test stories
    stories = [
        Story(
            id="story-1",
            title="Story 1",
            description="First test story",
            acceptance_criteria=["AC1"],
            epic_id="test-epic-1"
        ),
        Story(
            id="story-2", 
            title="Story 2",
            description="Second test story",
            acceptance_criteria=["AC2"],
            epic_id="test-epic-1"
        ),
        Story(
            id="story-3",
            title="Story 3", 
            description="Third test story",
            acceptance_criteria=["AC3"],
            epic_id="test-epic-1"
        )
    ]
    
    for story in stories:
        test_session.add(story)
    
    test_session.commit()
    return stories


def test_add_dependency_success(dependency_repository, test_stories):
    """Test successful dependency creation in database."""
    # Test dependency addition
    result = dependency_repository.add_dependency("story-1", "story-2")
    assert result is True
    
    # Verify dependency exists
    dependencies = dependency_repository.get_story_dependencies("story-1")
    assert len(dependencies) == 1
    assert dependencies[0].id == "story-2"


def test_add_dependency_duplicate(dependency_repository, test_stories):
    """Test handling of duplicate dependencies."""
    # Add dependency first time
    result1 = dependency_repository.add_dependency("story-1", "story-2")
    assert result1 is True
    
    # Try to add same dependency again
    result2 = dependency_repository.add_dependency("story-1", "story-2")
    assert result2 is False
    
    # Verify only one dependency exists
    dependencies = dependency_repository.get_story_dependencies("story-1")
    assert len(dependencies) == 1


def test_add_dependency_invalid_story_id(dependency_repository, test_stories):
    """Test foreign key constraint with invalid story ID."""
    with pytest.raises(IntegrityError):
        dependency_repository.add_dependency("nonexistent-story", "story-1")


def test_add_dependency_invalid_depends_on_story_id(dependency_repository, test_stories):
    """Test foreign key constraint with invalid dependency story ID."""
    with pytest.raises(IntegrityError):
        dependency_repository.add_dependency("story-1", "nonexistent-story")


def test_get_story_dependencies_success(dependency_repository, test_stories):
    """Test successful retrieval of story dependencies."""
    # Add multiple dependencies
    dependency_repository.add_dependency("story-1", "story-2")
    dependency_repository.add_dependency("story-1", "story-3")
    
    # Get dependencies
    dependencies = dependency_repository.get_story_dependencies("story-1")
    
    # Verify results
    assert len(dependencies) == 2
    dependency_ids = [dep.id for dep in dependencies]
    assert "story-2" in dependency_ids
    assert "story-3" in dependency_ids


def test_get_story_dependencies_empty(dependency_repository, test_stories):
    """Test retrieval when story has no dependencies."""
    dependencies = dependency_repository.get_story_dependencies("story-1")
    assert dependencies == []


def test_get_story_dependents_success(dependency_repository, test_stories):
    """Test successful retrieval of story dependents."""
    # Add dependencies where story-2 is depended on by multiple stories
    dependency_repository.add_dependency("story-1", "story-2")
    dependency_repository.add_dependency("story-3", "story-2")
    
    # Get dependents of story-2
    dependents = dependency_repository.get_story_dependents("story-2")
    
    # Verify results
    assert len(dependents) == 2
    dependent_ids = [dep.id for dep in dependents]
    assert "story-1" in dependent_ids
    assert "story-3" in dependent_ids


def test_get_story_dependents_empty(dependency_repository, test_stories):
    """Test retrieval when story has no dependents."""
    dependents = dependency_repository.get_story_dependents("story-1")
    assert dependents == []


def test_story_exists_true(dependency_repository, test_stories):
    """Test story exists check for existing story."""
    assert dependency_repository.story_exists("story-1") is True
    assert dependency_repository.story_exists("story-2") is True
    assert dependency_repository.story_exists("story-3") is True


def test_story_exists_false(dependency_repository, test_stories):
    """Test story exists check for non-existent story."""
    assert dependency_repository.story_exists("nonexistent-story") is False


def test_has_circular_dependency_false(dependency_repository, test_stories):
    """Test circular dependency detection with no cycle."""
    # Add linear dependency chain: story-1 -> story-2 -> story-3
    dependency_repository.add_dependency("story-1", "story-2")
    dependency_repository.add_dependency("story-2", "story-3")
    
    # Test that adding story-1 -> story-3 doesn't create cycle (it's just redundant)
    assert dependency_repository.has_circular_dependency("story-1", "story-3") is False


def test_has_circular_dependency_simple_cycle(dependency_repository, test_stories):
    """Test circular dependency detection with simple A->B->A cycle."""
    # Add story-1 -> story-2
    dependency_repository.add_dependency("story-1", "story-2")
    
    # Test that adding story-2 -> story-1 would create cycle
    assert dependency_repository.has_circular_dependency("story-2", "story-1") is True


def test_has_circular_dependency_complex_cycle(dependency_repository, test_stories):
    """Test circular dependency detection with complex A->B->C->A cycle."""
    # Add story-1 -> story-2 -> story-3
    dependency_repository.add_dependency("story-1", "story-2")
    dependency_repository.add_dependency("story-2", "story-3")
    
    # Test that adding story-3 -> story-1 would create cycle
    assert dependency_repository.has_circular_dependency("story-3", "story-1") is True


def test_has_circular_dependency_self_reference(dependency_repository, test_stories):
    """Test that self-dependency is detected as circular."""
    # Note: This should be prevented at the database level by check constraint,
    # but we test the algorithm's detection capability
    assert dependency_repository.has_circular_dependency("story-1", "story-1") is True


def test_remove_dependency_success(dependency_repository, test_stories):
    """Test successful dependency removal."""
    # Add dependency
    dependency_repository.add_dependency("story-1", "story-2")
    
    # Verify it exists
    dependencies = dependency_repository.get_story_dependencies("story-1")
    assert len(dependencies) == 1
    
    # Remove dependency
    result = dependency_repository.remove_dependency("story-1", "story-2")
    assert result is True
    
    # Verify it's gone
    dependencies = dependency_repository.get_story_dependencies("story-1")
    assert len(dependencies) == 0


def test_remove_dependency_not_exists(dependency_repository, test_stories):
    """Test removal of non-existent dependency."""
    result = dependency_repository.remove_dependency("story-1", "story-2")
    assert result is False


def test_multiple_dependencies_complex_scenario(dependency_repository, test_stories):
    """Test complex scenario with multiple dependencies and circular detection."""
    # Create dependency chain: story-1 -> story-2, story-1 -> story-3, story-2 -> story-3
    dependency_repository.add_dependency("story-1", "story-2")
    dependency_repository.add_dependency("story-1", "story-3")  
    dependency_repository.add_dependency("story-2", "story-3")
    
    # Verify dependencies
    story_1_deps = dependency_repository.get_story_dependencies("story-1")
    assert len(story_1_deps) == 2
    
    story_2_deps = dependency_repository.get_story_dependencies("story-2")
    assert len(story_2_deps) == 1
    assert story_2_deps[0].id == "story-3"
    
    # Verify dependents
    story_3_dependents = dependency_repository.get_story_dependents("story-3")
    assert len(story_3_dependents) == 2
    dependent_ids = [dep.id for dep in story_3_dependents]
    assert "story-1" in dependent_ids
    assert "story-2" in dependent_ids
    
    # Test circular dependency detection
    assert dependency_repository.has_circular_dependency("story-3", "story-1") is True
    assert dependency_repository.has_circular_dependency("story-3", "story-2") is True


def test_database_constraint_self_dependency(dependency_repository, test_stories):
    """Test that database constraint prevents self-dependency."""
    with pytest.raises(IntegrityError) as exc_info:
        dependency_repository.add_dependency("story-1", "story-1")
    
    # Verify it's the check constraint that prevented it
    assert "CHECK constraint failed" in str(exc_info.value) or "ck_no_self_dependency" in str(exc_info.value)