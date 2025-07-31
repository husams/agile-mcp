"""
Unit tests for Project API/Tool layer.
"""

from unittest.mock import Mock

import pytest

from src.agile_mcp.services.exceptions import DatabaseError, ProjectValidationError
from src.agile_mcp.services.project_service import ProjectService


def test_project_service_integration_create():
    """Test project service layer with mocked repository for create."""
    # Create mock repository
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Setup mock project
    from src.agile_mcp.models.project import Project

    mock_project = Project(
        id="test-id", name="Test Project", description="Test description"
    )
    mock_repository.create_project.return_value = mock_project

    # Test successful creation
    result = service.create_project("Test Project", "Test description")

    expected = {
        "id": "test-id",
        "name": "Test Project",
        "description": "Test description",
    }
    assert result == expected
    mock_repository.create_project.assert_called_once_with(
        "Test Project", "Test description"
    )


def test_project_service_create_validation_error():
    """Test project service with validation error."""
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Test empty name validation
    with pytest.raises(ProjectValidationError, match="Project name cannot be empty"):
        service.create_project("", "Valid description")

    # Test empty description validation
    with pytest.raises(
        ProjectValidationError, match="Project description cannot be empty"
    ):
        service.create_project("Valid name", "")


def test_project_service_create_database_error():
    """Test project service with database error."""
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Setup mock to raise database error
    from sqlalchemy.exc import SQLAlchemyError

    mock_repository.create_project.side_effect = SQLAlchemyError(
        "Database connection failed"
    )

    # Test database error handling
    with pytest.raises(DatabaseError, match="Database operation failed"):
        service.create_project("Valid name", "Valid description")


def test_project_service_find_projects():
    """Test project service layer with mocked repository for find."""
    # Create mock repository
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Setup mock projects
    from src.agile_mcp.models.project import Project

    mock_projects = [
        Project(id="1", name="Project 1", description="Description 1"),
        Project(id="2", name="Project 2", description="Description 2"),
    ]
    mock_repository.find_all_projects.return_value = mock_projects

    # Test successful retrieval
    result = service.find_projects()

    expected = [
        {"id": "1", "name": "Project 1", "description": "Description 1"},
        {"id": "2", "name": "Project 2", "description": "Description 2"},
    ]
    assert result == expected
    mock_repository.find_all_projects.assert_called_once()


def test_project_service_find_projects_empty():
    """Test project service when no projects exist."""
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Setup mock to return empty list
    mock_repository.find_all_projects.return_value = []

    # Test empty result
    result = service.find_projects()
    assert result == []
    mock_repository.find_all_projects.assert_called_once()


def test_project_service_find_projects_database_error():
    """Test project service find with database error."""
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Setup mock to raise database error
    from sqlalchemy.exc import SQLAlchemyError

    mock_repository.find_all_projects.side_effect = SQLAlchemyError("Connection lost")

    # Test database error handling
    with pytest.raises(
        DatabaseError, match="Database operation failed while retrieving projects"
    ):
        service.find_projects()


def test_project_service_whitespace_handling():
    """Test project service handles whitespace correctly."""
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Setup mock project
    from src.agile_mcp.models.project import Project

    mock_project = Project(
        id="test-id", name="Test Project", description="Test description"
    )
    mock_repository.create_project.return_value = mock_project

    # Test with whitespace inputs
    service.create_project("  Test Project  ", "  Test description  ")

    # Verify whitespace was stripped
    mock_repository.create_project.assert_called_once_with(
        "Test Project", "Test description"
    )


def test_project_service_length_validation():
    """Test project service length validation."""
    mock_repository = Mock()
    service = ProjectService(mock_repository)

    # Test name too long
    long_name = "x" * 201  # Exceeds 200 character limit
    with pytest.raises(
        ProjectValidationError, match="Project name cannot exceed 200 characters"
    ):
        service.create_project(long_name, "Valid description")

    # Test description too long
    long_description = "x" * 2001  # Exceeds 2000 character limit
    with pytest.raises(
        ProjectValidationError,
        match="Project description cannot exceed 2000 characters",
    ):
        service.create_project("Valid name", long_description)
