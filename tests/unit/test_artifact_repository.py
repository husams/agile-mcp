"""
Unit tests for Artifact repository.
"""

import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.agile_mcp.models.epic import Epic, Base
from src.agile_mcp.models.story import Story
from src.agile_mcp.models.artifact import Artifact
from src.agile_mcp.repositories.artifact_repository import ArtifactRepository


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create a test epic and story for foreign key relationships
    epic = Epic(
        id="test-epic-1",
        title="Test Epic",
        description="Test epic for artifact relationships",
        status="Draft"
    )
    session.add(epic)
    
    story = Story(
        id="test-story-1",
        title="Test Story",
        description="Test story for artifact relationships",
        acceptance_criteria=["Should work with artifacts"],
        epic_id="test-epic-1",
        status="ToDo"
    )
    session.add(story)
    session.commit()
    
    yield session
    session.close()


@pytest.fixture
def artifact_repository(in_memory_db):
    """Create Artifact repository with test database session."""
    return ArtifactRepository(in_memory_db)


def test_create_artifact(artifact_repository):
    """Test artifact creation through repository."""
    artifact = artifact_repository.create_artifact(
        uri="file:///path/to/implementation.js",
        relation="implementation",
        story_id="test-story-1"
    )
    
    assert artifact.id is not None
    assert artifact.uri == "file:///path/to/implementation.js"
    assert artifact.relation == "implementation"
    assert artifact.story_id == "test-story-1"


def test_create_artifact_generates_uuid(artifact_repository):
    """Test that artifact creation generates a valid UUID."""
    artifact = artifact_repository.create_artifact(
        uri="file:///path/to/test.py",
        relation="test",
        story_id="test-story-1"
    )
    
    # Verify ID is a valid UUID string
    uuid.UUID(artifact.id)  # Will raise ValueError if not valid UUID


def test_create_artifact_invalid_story_id(artifact_repository):
    """Test artifact creation with non-existent story ID."""
    with pytest.raises(IntegrityError) as exc_info:
        artifact_repository.create_artifact(
            uri="file:///path/to/code.js",
            relation="implementation",
            story_id="non-existent-story"
        )
    
    assert "Story with id 'non-existent-story' does not exist" in str(exc_info.value)


def test_create_artifact_invalid_uri_format(artifact_repository):
    """Test artifact creation with invalid URI format."""
    with pytest.raises(ValueError, match="Artifact URI must be a valid URI format"):
        artifact_repository.create_artifact(
            uri="not-a-valid-uri",
            relation="implementation",
            story_id="test-story-1"
        )


def test_create_artifact_invalid_relation_type(artifact_repository):
    """Test artifact creation with invalid relation type."""
    with pytest.raises(ValueError, match="Artifact relation must be one of:"):
        artifact_repository.create_artifact(
            uri="file:///path/to/code.js",
            relation="invalid-relation",
            story_id="test-story-1"
        )


def test_create_artifact_uri_too_long(artifact_repository):
    """Test artifact creation with URI too long."""
    long_uri = "file:///" + "x" * 497  # Total length = 501 characters
    with pytest.raises(ValueError, match="Artifact URI cannot exceed 500 characters"):
        artifact_repository.create_artifact(
            uri=long_uri,
            relation="implementation",
            story_id="test-story-1"
        )


def test_find_artifact_by_id_success(artifact_repository):
    """Test finding artifact by ID."""
    # Create artifact first
    created_artifact = artifact_repository.create_artifact(
        uri="file:///path/to/found.js",
        relation="implementation",
        story_id="test-story-1"
    )
    
    # Find artifact by ID
    found_artifact = artifact_repository.find_artifact_by_id(created_artifact.id)
    
    assert found_artifact is not None
    assert found_artifact.id == created_artifact.id
    assert found_artifact.uri == "file:///path/to/found.js"
    assert found_artifact.relation == "implementation"
    assert found_artifact.story_id == "test-story-1"


def test_find_artifact_by_id_not_found(artifact_repository):
    """Test finding artifact by non-existent ID."""
    result = artifact_repository.find_artifact_by_id("non-existent-id")
    assert result is None


def test_find_artifacts_by_story_id_success(artifact_repository):
    """Test finding artifacts by story ID."""
    # Create multiple artifacts for the same story
    artifact1 = artifact_repository.create_artifact(
        uri="file:///path/to/implementation.js",
        relation="implementation",
        story_id="test-story-1"
    )
    
    artifact2 = artifact_repository.create_artifact(
        uri="file:///path/to/design.md",
        relation="design",
        story_id="test-story-1"
    )
    
    artifact3 = artifact_repository.create_artifact(
        uri="file:///path/to/test.py",
        relation="test",
        story_id="test-story-1"
    )
    
    # Find all artifacts for the story
    artifacts = artifact_repository.find_artifacts_by_story_id("test-story-1")
    
    assert len(artifacts) == 3
    artifact_ids = [a.id for a in artifacts]
    assert artifact1.id in artifact_ids
    assert artifact2.id in artifact_ids
    assert artifact3.id in artifact_ids


def test_find_artifacts_by_story_id_empty_result(artifact_repository):
    """Test finding artifacts for story with no artifacts."""
    artifacts = artifact_repository.find_artifacts_by_story_id("test-story-1")
    assert artifacts == []


def test_find_artifacts_by_story_id_non_existent_story(artifact_repository):
    """Test finding artifacts for non-existent story ID."""
    artifacts = artifact_repository.find_artifacts_by_story_id("non-existent-story")
    assert artifacts == []


def test_delete_artifact_success(artifact_repository):
    """Test deleting artifact by ID."""
    # Create artifact first
    artifact = artifact_repository.create_artifact(
        uri="file:///path/to/delete.js",
        relation="implementation",
        story_id="test-story-1"
    )
    
    # Delete the artifact
    result = artifact_repository.delete_artifact(artifact.id)
    assert result is True
    
    # Verify artifact is deleted
    found_artifact = artifact_repository.find_artifact_by_id(artifact.id)
    assert found_artifact is None


def test_delete_artifact_not_found(artifact_repository):
    """Test deleting non-existent artifact."""
    result = artifact_repository.delete_artifact("non-existent-id")
    assert result is False


def test_create_artifact_with_all_valid_relations(artifact_repository):
    """Test creating artifacts with all valid relation types."""
    valid_relations = ["implementation", "design", "test"]
    
    created_artifacts = []
    for relation in valid_relations:
        artifact = artifact_repository.create_artifact(
            uri=f"file:///path/to/{relation}.file",
            relation=relation,
            story_id="test-story-1"
        )
        created_artifacts.append(artifact)
        assert artifact.relation == relation
    
    # Verify all artifacts were created
    all_artifacts = artifact_repository.find_artifacts_by_story_id("test-story-1")
    assert len(all_artifacts) == 3


def test_create_artifact_with_various_uri_formats(artifact_repository):
    """Test creating artifacts with various valid URI formats."""
    valid_uris = [
        "file:///absolute/path/to/file.js",
        "https://github.com/user/repo/blob/main/file.py",
        "http://example.com/resource",
        "ftp://files.example.com/document.pdf"
    ]
    
    for i, uri in enumerate(valid_uris):
        artifact = artifact_repository.create_artifact(
            uri=uri,
            relation="implementation",
            story_id="test-story-1"
        )
        assert artifact.uri == uri


def test_repository_rollback_on_error(artifact_repository, in_memory_db):
    """Test that repository rolls back transaction on error."""
    # Count initial artifacts
    initial_count = len(artifact_repository.find_artifacts_by_story_id("test-story-1"))
    
    # Try to create artifact with invalid story ID (should rollback)
    try:
        artifact_repository.create_artifact(
            uri="file:///path/to/code.js",
            relation="implementation",
            story_id="non-existent-story"
        )
    except IntegrityError:
        pass  # Expected error
    
    # Verify no artifacts were added due to rollback
    final_count = len(artifact_repository.find_artifacts_by_story_id("test-story-1"))
    assert final_count == initial_count


def test_create_artifact_empty_uri(artifact_repository):
    """Test artifact creation with empty URI."""
    with pytest.raises(ValueError, match="Artifact URI cannot be empty"):
        artifact_repository.create_artifact(
            uri="",
            relation="implementation",
            story_id="test-story-1"
        )


def test_create_artifact_whitespace_uri(artifact_repository):
    """Test artifact creation with whitespace-only URI."""
    with pytest.raises(ValueError, match="Artifact URI cannot be empty"):
        artifact_repository.create_artifact(
            uri="   ",
            relation="implementation",
            story_id="test-story-1"
        )


def test_create_artifact_strips_uri_whitespace(artifact_repository):
    """Test that artifact creation strips whitespace from URI."""
    artifact = artifact_repository.create_artifact(
        uri="   file:///path/to/code.js   ",
        relation="implementation",
        story_id="test-story-1"
    )
    
    assert artifact.uri == "file:///path/to/code.js"


def test_multiple_artifacts_same_uri_different_relations(artifact_repository):
    """Test creating multiple artifacts with same URI but different relations."""
    uri = "file:///path/to/shared.file"
    
    impl_artifact = artifact_repository.create_artifact(
        uri=uri,
        relation="implementation",
        story_id="test-story-1"
    )
    
    design_artifact = artifact_repository.create_artifact(
        uri=uri,
        relation="design",
        story_id="test-story-1"
    )
    
    # Both should be created successfully
    assert impl_artifact.uri == uri
    assert design_artifact.uri == uri
    assert impl_artifact.relation == "implementation"
    assert design_artifact.relation == "design"
    assert impl_artifact.id != design_artifact.id