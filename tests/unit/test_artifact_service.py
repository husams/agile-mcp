"""
Unit tests for Artifact service layer.
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.agile_mcp.services.artifact_service import ArtifactService
from src.agile_mcp.services.exceptions import (
    ArtifactValidationError, 
    ArtifactNotFoundError, 
    StoryNotFoundError, 
    DatabaseError, 
    InvalidRelationTypeError
)
from src.agile_mcp.models.artifact import Artifact


@pytest.fixture
def mock_repository():
    """Create a mock Artifact repository."""
    return Mock()


@pytest.fixture
def artifact_service(mock_repository):
    """Create Artifact service with mock repository."""
    return ArtifactService(mock_repository)


def test_link_artifact_to_story_success(artifact_service, mock_repository):
    """Test successful artifact linking."""
    # Setup mock
    mock_artifact = Artifact(
        id="test-artifact-id",
        uri="file:///path/to/code.js",
        relation="implementation",
        story_id="test-story-id"
    )
    mock_repository.create_artifact.return_value = mock_artifact
    
    # Call service method
    result = artifact_service.link_artifact_to_story(
        story_id="test-story-id",
        uri="file:///path/to/code.js",
        relation="implementation"
    )
    
    # Verify result
    expected = {
        "id": "test-artifact-id",
        "uri": "file:///path/to/code.js",
        "relation": "implementation",
        "story_id": "test-story-id"
    }
    assert result == expected
    mock_repository.create_artifact.assert_called_once_with(
        "file:///path/to/code.js",
        "implementation",
        "test-story-id"
    )


def test_link_artifact_to_story_empty_story_id(artifact_service, mock_repository):
    """Test artifact linking with empty story ID."""
    with pytest.raises(ArtifactValidationError, match="Story ID cannot be empty"):
        artifact_service.link_artifact_to_story(
            story_id="",
            uri="file:///path/to/code.js",
            relation="implementation"
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_whitespace_story_id(artifact_service, mock_repository):
    """Test artifact linking with whitespace-only story ID."""
    with pytest.raises(ArtifactValidationError, match="Story ID cannot be empty"):
        artifact_service.link_artifact_to_story(
            story_id="   ",
            uri="file:///path/to/code.js",
            relation="implementation"
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_empty_uri(artifact_service, mock_repository):
    """Test artifact linking with empty URI."""
    with pytest.raises(ArtifactValidationError, match="Artifact URI cannot be empty"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="",
            relation="implementation"
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_whitespace_uri(artifact_service, mock_repository):
    """Test artifact linking with whitespace-only URI."""
    with pytest.raises(ArtifactValidationError, match="Artifact URI cannot be empty"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="   ",
            relation="implementation"
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_empty_relation(artifact_service, mock_repository):
    """Test artifact linking with empty relation."""
    with pytest.raises(InvalidRelationTypeError, match="Artifact relation cannot be empty"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="file:///path/to/code.js",
            relation=""
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_whitespace_relation(artifact_service, mock_repository):
    """Test artifact linking with whitespace-only relation."""
    with pytest.raises(InvalidRelationTypeError, match="Artifact relation cannot be empty"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="file:///path/to/code.js",
            relation="   "
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_uri_too_long(artifact_service, mock_repository):
    """Test artifact linking with URI too long."""
    long_uri = "file:///" + "x" * 497  # Total length = 501 characters
    with pytest.raises(ArtifactValidationError, match="Artifact URI cannot exceed 500 characters"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri=long_uri,
            relation="implementation"
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_invalid_uri_format(artifact_service, mock_repository):
    """Test artifact linking with invalid URI format."""
    with pytest.raises(ArtifactValidationError, match="Artifact URI must be a valid URI format"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="not-a-valid-uri",
            relation="implementation"
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_invalid_relation_type(artifact_service, mock_repository):
    """Test artifact linking with invalid relation type."""
    with pytest.raises(InvalidRelationTypeError, match="Artifact relation must be one of: design, implementation, test"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="file:///path/to/code.js",
            relation="invalid-relation"
        )
    mock_repository.create_artifact.assert_not_called()


def test_link_artifact_to_story_valid_relation_types(artifact_service, mock_repository):
    """Test artifact linking with all valid relation types."""
    valid_relations = ["implementation", "design", "test"]
    
    for relation in valid_relations:
        mock_artifact = Artifact(
            id=f"test-artifact-{relation}",
            uri="file:///path/to/code.js",
            relation=relation,
            story_id="test-story-id"
        )
        mock_repository.create_artifact.return_value = mock_artifact
        
        result = artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="file:///path/to/code.js",
            relation=relation
        )
        assert result["relation"] == relation


def test_link_artifact_to_story_story_not_found(artifact_service, mock_repository):
    """Test artifact linking when story doesn't exist."""
    mock_repository.create_artifact.side_effect = IntegrityError(
        statement="INSERT",
        params={},
        orig=Exception("Story with id 'non-existent' does not exist")
    )
    
    with pytest.raises(StoryNotFoundError, match="Story with ID 'test-story-id' not found"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="file:///path/to/code.js",
            relation="implementation"
        )


def test_link_artifact_to_story_model_validation_error(artifact_service, mock_repository):
    """Test artifact linking with model validation error."""
    mock_repository.create_artifact.side_effect = ValueError("Invalid URI format from model")
    
    with pytest.raises(ArtifactValidationError, match="Invalid URI format from model"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="file:///path/to/code.js",
            relation="implementation"
        )


def test_link_artifact_to_story_database_error(artifact_service, mock_repository):
    """Test artifact linking with database error."""
    mock_repository.create_artifact.side_effect = SQLAlchemyError("Database connection failed")
    
    with pytest.raises(DatabaseError, match="Database operation failed"):
        artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri="file:///path/to/code.js",
            relation="implementation"
        )


def test_link_artifact_to_story_strips_whitespace(artifact_service, mock_repository):
    """Test that link_artifact_to_story strips whitespace from inputs."""
    mock_artifact = Artifact(
        id="test-artifact-id",
        uri="file:///path/to/code.js",
        relation="implementation",
        story_id="test-story-id"
    )
    mock_repository.create_artifact.return_value = mock_artifact
    
    artifact_service.link_artifact_to_story(
        story_id="  test-story-id  ",
        uri="  file:///path/to/code.js  ",
        relation="  implementation  "
    )
    
    mock_repository.create_artifact.assert_called_once_with(
        "file:///path/to/code.js",
        "implementation",
        "test-story-id"
    )


def test_get_artifacts_for_story_success(artifact_service, mock_repository):
    """Test successful artifacts retrieval for story."""
    mock_artifacts = [
        Artifact(
            id="artifact-1",
            uri="file:///path/to/implementation.js",
            relation="implementation",
            story_id="test-story-id"
        ),
        Artifact(
            id="artifact-2",
            uri="file:///path/to/design.md",
            relation="design",
            story_id="test-story-id"
        )
    ]
    mock_repository.find_artifacts_by_story_id.return_value = mock_artifacts
    
    result = artifact_service.get_artifacts_for_story("test-story-id")
    
    expected = [
        {
            "id": "artifact-1",
            "uri": "file:///path/to/implementation.js",
            "relation": "implementation",
            "story_id": "test-story-id"
        },
        {
            "id": "artifact-2",
            "uri": "file:///path/to/design.md",
            "relation": "design",
            "story_id": "test-story-id"
        }
    ]
    assert result == expected
    mock_repository.find_artifacts_by_story_id.assert_called_once_with("test-story-id")


def test_get_artifacts_for_story_empty_list(artifact_service, mock_repository):
    """Test artifacts retrieval for story with no artifacts."""
    mock_repository.find_artifacts_by_story_id.return_value = []
    
    result = artifact_service.get_artifacts_for_story("test-story-id")
    
    assert result == []
    mock_repository.find_artifacts_by_story_id.assert_called_once_with("test-story-id")


def test_get_artifacts_for_story_empty_story_id(artifact_service, mock_repository):
    """Test artifacts retrieval with empty story ID."""
    with pytest.raises(ArtifactValidationError, match="Story ID cannot be empty"):
        artifact_service.get_artifacts_for_story("")
    mock_repository.find_artifacts_by_story_id.assert_not_called()


def test_get_artifacts_for_story_whitespace_story_id(artifact_service, mock_repository):
    """Test artifacts retrieval with whitespace-only story ID."""
    with pytest.raises(ArtifactValidationError, match="Story ID cannot be empty"):
        artifact_service.get_artifacts_for_story("   ")
    mock_repository.find_artifacts_by_story_id.assert_not_called()


def test_get_artifacts_for_story_database_error(artifact_service, mock_repository):
    """Test artifacts retrieval with database error."""
    mock_repository.find_artifacts_by_story_id.side_effect = SQLAlchemyError("Database connection failed")
    
    with pytest.raises(DatabaseError, match="Database operation failed while retrieving artifacts"):
        artifact_service.get_artifacts_for_story("test-story-id")


def test_get_artifacts_for_story_strips_whitespace(artifact_service, mock_repository):
    """Test that get_artifacts_for_story strips whitespace from story_id."""
    mock_repository.find_artifacts_by_story_id.return_value = []
    
    artifact_service.get_artifacts_for_story("  test-story-id  ")
    
    mock_repository.find_artifacts_by_story_id.assert_called_once_with("test-story-id")


def test_get_artifact_success(artifact_service, mock_repository):
    """Test successful artifact retrieval."""
    mock_artifact = Artifact(
        id="test-artifact-id",
        uri="file:///path/to/code.js",
        relation="implementation",
        story_id="test-story-id"
    )
    mock_repository.find_artifact_by_id.return_value = mock_artifact
    
    result = artifact_service.get_artifact("test-artifact-id")
    
    expected = {
        "id": "test-artifact-id",
        "uri": "file:///path/to/code.js",
        "relation": "implementation", 
        "story_id": "test-story-id"
    }
    assert result == expected
    mock_repository.find_artifact_by_id.assert_called_once_with("test-artifact-id")


def test_get_artifact_not_found(artifact_service, mock_repository):
    """Test artifact retrieval when artifact doesn't exist."""
    mock_repository.find_artifact_by_id.return_value = None
    
    with pytest.raises(ArtifactNotFoundError, match="Artifact with ID 'non-existent' not found"):
        artifact_service.get_artifact("non-existent")


def test_get_artifact_empty_id(artifact_service, mock_repository):
    """Test artifact retrieval with empty ID."""
    with pytest.raises(ArtifactValidationError, match="Artifact ID cannot be empty"):
        artifact_service.get_artifact("")
    mock_repository.find_artifact_by_id.assert_not_called()


def test_get_artifact_whitespace_id(artifact_service, mock_repository):
    """Test artifact retrieval with whitespace-only ID."""
    with pytest.raises(ArtifactValidationError, match="Artifact ID cannot be empty"):
        artifact_service.get_artifact("   ")
    mock_repository.find_artifact_by_id.assert_not_called()


def test_get_artifact_database_error(artifact_service, mock_repository):
    """Test artifact retrieval with database error."""
    mock_repository.find_artifact_by_id.side_effect = SQLAlchemyError("Database connection failed")
    
    with pytest.raises(DatabaseError, match="Database operation failed while retrieving artifact"):
        artifact_service.get_artifact("test-artifact-id")


def test_get_artifact_strips_whitespace(artifact_service, mock_repository):
    """Test that get_artifact strips whitespace from artifact_id."""
    mock_artifact = Artifact(
        id="test-artifact-id",
        uri="file:///path/to/code.js",
        relation="implementation",
        story_id="test-story-id"
    )
    mock_repository.find_artifact_by_id.return_value = mock_artifact
    
    artifact_service.get_artifact("  test-artifact-id  ")
    
    mock_repository.find_artifact_by_id.assert_called_once_with("test-artifact-id")


def test_link_artifact_to_story_valid_uri_formats(artifact_service, mock_repository):
    """Test artifact linking with various valid URI formats."""
    valid_uris = [
        "file:///path/to/file.js",
        "https://github.com/user/repo/blob/main/file.py",
        "http://example.com/resource",
        "ftp://files.example.com/document.pdf",
        "mailto:user@example.com",
        "custom-scheme://path/to/resource"
    ]
    
    for uri in valid_uris:
        mock_artifact = Artifact(
            id=f"test-artifact-{len(uri)}",
            uri=uri,
            relation="implementation",
            story_id="test-story-id"
        )
        mock_repository.create_artifact.return_value = mock_artifact
        
        result = artifact_service.link_artifact_to_story(
            story_id="test-story-id",
            uri=uri,
            relation="implementation"
        )
        assert result["uri"] == uri


def test_link_artifact_to_story_invalid_uri_formats(artifact_service, mock_repository):
    """Test artifact linking with various invalid URI formats."""
    invalid_uris = [
        "not-a-uri",
        "://missing-scheme", 
        "123://invalid-scheme-start",
        "file:// spaces in uri",
        "http:// multiple spaces"
    ]
    
    for uri in invalid_uris:
        with pytest.raises(ArtifactValidationError):
            artifact_service.link_artifact_to_story(
                story_id="test-story-id",
                uri=uri,
                relation="implementation"
            )
        mock_repository.create_artifact.assert_not_called()