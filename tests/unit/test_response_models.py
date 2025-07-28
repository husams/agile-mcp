"""
Unit tests for enhanced Pydantic response models.
"""

import pytest
from pydantic import ValidationError

from src.agile_mcp.models.response import (
    ArtifactResponse,
    DependencyAddResponse,
    DoDChecklistResponse,
    EpicResponse,
    StoryResponse,
    StorySectionResponse,
)


class TestStoryResponse:
    """Test cases for StoryResponse model."""

    def test_story_response_valid_data(self):
        """Test StoryResponse with valid data."""
        data = {
            "id": "story-123",
            "title": "Test Story",
            "description": "A test story description",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "tasks": [],
            "status": "ToDo",
            "priority": 1,
            "created_at": "2025-07-27T10:00:00+00:00",
            "epic_id": "epic-456",
        }

        response = StoryResponse(**data)
        assert response.id == "story-123"
        assert response.title == "Test Story"
        assert response.acceptance_criteria == ["Criterion 1", "Criterion 2"]
        assert response.priority == 1

    def test_story_response_serialization(self):
        """Test StoryResponse JSON serialization."""
        data = {
            "id": "story-123",
            "title": "Test Story",
            "description": "A test story description",
            "acceptance_criteria": ["Criterion 1"],
            "tasks": [],
            "status": "ToDo",
            "priority": 0,
            "created_at": "2025-07-27T10:00:00+00:00",
            "epic_id": "epic-456",
        }

        response = StoryResponse(**data)
        json_data = response.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["id"] == "story-123"
        assert json_data["acceptance_criteria"] == ["Criterion 1"]

        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        assert "story-123" in json_str

    def test_story_response_missing_required_field(self):
        """Test StoryResponse with missing required field."""
        data = {
            "id": "story-123",
            "title": "Test Story",
            # Missing description
            "acceptance_criteria": ["Criterion 1"],
            "status": "ToDo",
            "priority": 0,
            "epic_id": "epic-456",
        }

        with pytest.raises(ValidationError):
            StoryResponse(**data)


class TestEpicResponse:
    """Test cases for EpicResponse model."""

    def test_epic_response_valid_data(self):
        """Test EpicResponse with valid data."""
        data = {
            "id": "epic-123",
            "title": "Test Epic",
            "description": "A test epic description",
            "status": "Draft",
        }

        response = EpicResponse(**data)
        assert response.id == "epic-123"
        assert response.title == "Test Epic"
        assert response.status == "Draft"

    def test_epic_response_serialization(self):
        """Test EpicResponse JSON serialization."""
        data = {
            "id": "epic-123",
            "title": "Test Epic",
            "description": "A test epic description",
            "status": "Ready",
        }

        response = EpicResponse(**data)
        json_data = response.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["status"] == "Ready"


class TestArtifactResponse:
    """Test cases for ArtifactResponse model."""

    def test_artifact_response_valid_data(self):
        """Test ArtifactResponse with valid data."""
        data = {
            "id": "artifact-123",
            "story_id": "story-456",
            "uri": "file:///path/to/code.js",
            "relation": "implementation",
        }

        response = ArtifactResponse(**data)
        assert response.id == "artifact-123"
        assert response.story_id == "story-456"
        assert response.relation == "implementation"

    def test_artifact_response_serialization(self):
        """Test ArtifactResponse JSON serialization."""
        data = {
            "id": "artifact-123",
            "story_id": "story-456",
            "uri": "file:///path/to/test.py",
            "relation": "test",
        }

        response = ArtifactResponse(**data)
        json_data = response.model_dump()
        assert json_data["relation"] == "test"


class TestStorySectionResponse:
    """Test cases for StorySectionResponse model."""

    def test_story_section_response_valid_data(self):
        """Test StorySectionResponse with valid data."""
        data = {
            "story_id": "story-123",
            "section_name": "Acceptance Criteria",
            "content": "Some acceptance criteria content",
        }

        response = StorySectionResponse(**data)
        assert response.section_name == "Acceptance Criteria"
        assert response.content == "Some acceptance criteria content"


class TestDependencyAddResponse:
    """Test cases for DependencyAddResponse model."""

    def test_dependency_add_response_valid_data(self):
        """Test DependencyAddResponse with valid data."""
        data = {
            "status": "success",
            "story_id": "story-123",
            "depends_on_story_id": "story-456",
            "message": "Dependency added successfully",
        }

        response = DependencyAddResponse(**data)
        assert response.status == "success"
        assert "successfully" in response.message


class TestDoDChecklistResponse:
    """Test cases for DoDChecklistResponse model."""

    def test_dod_checklist_response_valid_data(self):
        """Test DoDChecklistResponse with valid data."""
        data = {
            "story_id": "story-123",
            "story_title": "Test Story",
            "story_status": "Done",
            "overall_status": "PASSED",
            "checklist_items": [
                {
                    "id": "code_complete",
                    "name": "Code Complete",
                    "status": "PASSED",
                    "required": True,
                }
            ],
            "summary": {"total_items": 1, "passed_items": 1, "failed_items": 0},
            "recommendations": ["All criteria met"],
            "evaluated_at": "2025-07-27T10:00:00Z",
        }

        response = DoDChecklistResponse(**data)
        assert response.overall_status == "PASSED"
        assert len(response.checklist_items) == 1
        assert response.summary["total_items"] == 1

    def test_dod_checklist_response_serialization(self):
        """Test DoDChecklistResponse JSON serialization."""
        data = {
            "story_id": "story-123",
            "story_title": "Test Story",
            "story_status": "Review",
            "overall_status": "PARTIAL",
            "checklist_items": [],
            "summary": {"total_items": 0},
            "recommendations": [],
            "evaluated_at": "2025-07-27T10:00:00Z",
        }

        response = DoDChecklistResponse(**data)
        json_str = response.model_dump_json()
        assert "PARTIAL" in json_str
        assert "story-123" in json_str
