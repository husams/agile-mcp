"""
Unit tests for Project service layer.
"""

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.agile_mcp.models.project import Project
from src.agile_mcp.services.exceptions import (
    DatabaseError,
    ProjectValidationError,
)
from src.agile_mcp.services.project_service import ProjectService


@pytest.fixture
def mock_repository():
    """Create a mock Project repository."""
    return Mock()


@pytest.fixture
def project_service(mock_repository):
    """Create Project service with mock repository."""
    return ProjectService(mock_repository)


def test_create_project_success(project_service, mock_repository):
    """Test successful project creation."""
    # Setup mock
    mock_project = Project(
        id="test-id", name="Test Project", description="Test description"
    )
    mock_repository.create_project.return_value = mock_project

    # Call service method
    result = project_service.create_project("Test Project", "Test description")

    # Verify result
    expected = {
        "id": "test-id",
        "name": "Test Project",
        "description": "Test description",
    }
    assert result == expected
    mock_repository.create_project.assert_called_once_with(
        "Test Project", "Test description"
    )


def test_create_project_empty_name(project_service):
    """Test project creation with empty name."""
    with pytest.raises(ProjectValidationError, match="Project name cannot be empty"):
        project_service.create_project("", "Valid description")

    with pytest.raises(ProjectValidationError, match="Project name cannot be empty"):
        project_service.create_project("   ", "Valid description")


def test_create_project_empty_description(project_service):
    """Test project creation with empty description."""
    with pytest.raises(
        ProjectValidationError, match="Project description cannot be empty"
    ):
        project_service.create_project("Valid name", "")

    with pytest.raises(
        ProjectValidationError, match="Project description cannot be empty"
    ):
        project_service.create_project("Valid name", "   ")


def test_create_project_name_too_long(project_service):
    """Test project creation with name too long."""
    long_name = "x" * 201  # Exceeds 200 character limit

    with pytest.raises(
        ProjectValidationError, match="Project name cannot exceed 200 characters"
    ):
        project_service.create_project(long_name, "Valid description")


def test_create_project_description_too_long(project_service):
    """Test project creation with description too long."""
    long_description = "x" * 2001  # Exceeds 2000 character limit

    with pytest.raises(
        ProjectValidationError,
        match="Project description cannot exceed 2000 characters",
    ):
        project_service.create_project("Valid name", long_description)


def test_create_project_database_error(project_service, mock_repository):
    """Test project creation with database error."""
    # Setup mock to raise SQLAlchemy error
    mock_repository.create_project.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    with pytest.raises(
        DatabaseError, match="Database operation failed: Database connection failed"
    ):
        project_service.create_project("Valid name", "Valid description")


def test_create_project_strips_whitespace(project_service, mock_repository):
    """Test that project creation strips whitespace from inputs."""
    mock_project = Project(
        id="test-id", name="Test Project", description="Test description"
    )
    mock_repository.create_project.return_value = mock_project

    project_service.create_project("  Test Project  ", "  Test description  ")

    mock_repository.create_project.assert_called_once_with(
        "Test Project", "Test description"
    )


def test_find_projects_success(project_service, mock_repository):
    """Test successful project retrieval."""
    # Setup mock
    mock_projects = [
        Project(id="1", name="Project 1", description="Desc 1"),
        Project(id="2", name="Project 2", description="Desc 2"),
    ]
    mock_repository.find_all_projects.return_value = mock_projects

    # Call service method
    result = project_service.find_projects()

    # Verify result
    expected = [
        {"id": "1", "name": "Project 1", "description": "Desc 1"},
        {"id": "2", "name": "Project 2", "description": "Desc 2"},
    ]
    assert result == expected
    mock_repository.find_all_projects.assert_called_once()


def test_find_projects_empty(project_service, mock_repository):
    """Test project retrieval when no projects exist."""
    mock_repository.find_all_projects.return_value = []

    result = project_service.find_projects()

    assert result == []
    mock_repository.find_all_projects.assert_called_once()


def test_find_projects_database_error(project_service, mock_repository):
    """Test project retrieval with database error."""
    mock_repository.find_all_projects.side_effect = SQLAlchemyError("Connection lost")

    with pytest.raises(
        DatabaseError,
        match="Database operation failed while retrieving projects: Connection lost",
    ):
        project_service.find_projects()


def test_create_project_model_validation_error(project_service, mock_repository):
    """Test project creation with model validation error."""
    mock_repository.create_project.side_effect = ValueError("Invalid name value")

    with pytest.raises(ProjectValidationError, match="Invalid name value"):
        project_service.create_project("Valid name", "Valid description")
