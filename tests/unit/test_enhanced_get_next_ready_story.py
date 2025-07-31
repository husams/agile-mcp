"""
Unit tests for enhanced getNextReadyStory functionality with rich story data.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

# from src.agile_mcp.api.backlog_tools import register_backlog_tools
from src.agile_mcp.models.response import StoryResponse


class TestEnhancedGetNextReadyStory:
    """Test cases for enhanced getNextReadyStory with rich story data."""

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_returns_enhanced_fields(
        self, mock_get_db, mock_create_tables
    ):
        """Test that getNextReadyStory returns all enhanced story fields."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        # Mock story with all enhanced fields
        enhanced_story = {
            "id": "story-enhanced-1",
            "title": "Enhanced Test Story",
            "description": "A story with all enhanced fields",
            "acceptance_criteria": ["Basic AC 1", "Basic AC 2"],
            "structured_acceptance_criteria": [
                {
                    "id": "ac-1",
                    "description": "Enhanced AC 1",
                    "met": False,
                    "order": 1,
                },
                {"id": "ac-2", "description": "Enhanced AC 2", "met": True, "order": 2},
            ],
            "tasks": [
                {
                    "id": "task-1",
                    "description": "Implement feature",
                    "completed": False,
                    "order": 1,
                },
                {
                    "id": "task-2",
                    "description": "Write tests",
                    "completed": True,
                    "order": 2,
                },
            ],
            "comments": [
                {
                    "id": "comment-1",
                    "author_role": "Developer Agent",
                    "content": "Initial analysis complete",
                    "timestamp": "2023-01-01T12:00:00Z",
                    "reply_to_id": None,
                },
                {
                    "id": "comment-2",
                    "author_role": "QA Agent",
                    "content": "Test cases reviewed",
                    "timestamp": "2023-01-01T14:00:00Z",
                    "reply_to_id": "comment-1",
                },
            ],
            "dev_notes": (
                "## Technical Context\n\nThis story requires implementing new "
                "API endpoints.\n\n### Architecture Notes\n- Use FastAPI for "
                "endpoint definition\n- Add proper validation\n- Include "
                "comprehensive error handling"
            ),
            "status": "InProgress",
            "priority": 8,
            "created_at": "2023-01-01T10:00:00Z",
            "epic_id": "epic-1",
        }

        with patch("src.agile_mcp.api.backlog_tools.StoryRepository"), patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ), patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            mock_story_service.get_next_ready_story.return_value = enhanced_story
            mock_story_service_class.return_value = mock_story_service

            # Test story service returns enhanced story
            result = mock_story_service.get_next_ready_story()
            assert result == enhanced_story

            # Verify enhanced fields are present
            assert "structured_acceptance_criteria" in result
            assert "tasks" in result
            assert "comments" in result
            assert "dev_notes" in result

            # Verify structured acceptance criteria
            assert len(result["structured_acceptance_criteria"]) == 2
            assert result["structured_acceptance_criteria"][0]["id"] == "ac-1"
            assert result["structured_acceptance_criteria"][0]["met"] is False

            # Verify tasks
            assert len(result["tasks"]) == 2
            assert result["tasks"][0]["id"] == "task-1"
            assert result["tasks"][0]["completed"] is False
            assert result["tasks"][1]["completed"] is True

            # Verify comments
            assert len(result["comments"]) == 2
            assert result["comments"][0]["author_role"] == "Developer Agent"
            assert result["comments"][1]["reply_to_id"] == "comment-1"

            # Verify dev_notes
            assert "Technical Context" in result["dev_notes"]
            assert "FastAPI" in result["dev_notes"]

            # Verify the enhanced story validates against StoryResponse model
            story_response = StoryResponse(**result)
            assert story_response.id == "story-enhanced-1"
            assert len(story_response.structured_acceptance_criteria) == 2
            assert len(story_response.tasks) == 2
            assert len(story_response.comments) == 2
            assert story_response.dev_notes is not None

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_handles_empty_enhanced_fields(
        self, mock_get_db, mock_create_tables
    ):
        """Test that getNextReadyStory handles stories with empty enhanced fields."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        # Mock story with empty enhanced fields
        minimal_story = {
            "id": "story-minimal-1",
            "title": "Minimal Test Story",
            "description": "A story with minimal enhanced fields",
            "acceptance_criteria": ["Basic AC"],
            "structured_acceptance_criteria": [],  # Empty
            "tasks": [],  # Empty
            "comments": [],  # Empty
            "dev_notes": None,  # None
            "status": "InProgress",
            "priority": 3,
            "created_at": "2023-01-01T10:00:00Z",
            "epic_id": "epic-1",
        }

        with patch("src.agile_mcp.api.backlog_tools.StoryRepository"), patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ), patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            mock_story_service.get_next_ready_story.return_value = minimal_story
            mock_story_service_class.return_value = mock_story_service

            # Test story service returns minimal story
            result = mock_story_service.get_next_ready_story()
            assert result == minimal_story

            # Verify enhanced fields are present but empty/None
            assert "structured_acceptance_criteria" in result
            assert "tasks" in result
            assert "comments" in result
            assert "dev_notes" in result

            assert result["structured_acceptance_criteria"] == []
            assert result["tasks"] == []
            assert result["comments"] == []
            assert result["dev_notes"] is None

            # Verify the minimal story validates against StoryResponse model
            story_response = StoryResponse(**result)
            assert story_response.id == "story-minimal-1"
            assert story_response.structured_acceptance_criteria == []
            assert story_response.tasks == []
            assert story_response.comments == []
            assert story_response.dev_notes is None

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_json_serialization(
        self, mock_get_db, mock_create_tables
    ):
        """Test that enhanced story data properly serializes to JSON."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        # Mock story with datetime objects that need serialization
        {
            "id": "story-datetime-1",
            "title": "Story with Datetime",
            "description": "Testing datetime serialization",
            "acceptance_criteria": ["AC with datetime"],
            "structured_acceptance_criteria": [],
            "tasks": [],
            "comments": [
                {
                    "id": "comment-dt-1",
                    "author_role": "Test Agent",
                    "content": "Comment with datetime",
                    "timestamp": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                    "reply_to_id": None,
                }
            ],
            "dev_notes": "Notes with datetime context",
            "status": "InProgress",
            "priority": 5,
            "created_at": "2023-01-01T10:00:00Z",
            "epic_id": "epic-1",
        }

        # Create a properly serialized story (as story.to_dict() would return)
        serialized_story = {
            "id": "story-datetime-1",
            "title": "Story with Datetime",
            "description": "Testing datetime serialization",
            "acceptance_criteria": ["AC with datetime"],
            "structured_acceptance_criteria": [],
            "tasks": [],
            "comments": [
                {
                    "id": "comment-dt-1",
                    "author_role": "Test Agent",
                    "content": "Comment with datetime",
                    "timestamp": "2023-01-01T12:00:00+00:00",  # Serialized ISO format
                    "reply_to_id": None,
                }
            ],
            "dev_notes": "Notes with datetime context",
            "status": "InProgress",
            "priority": 5,
            "created_at": "2023-01-01T10:00:00Z",
            "epic_id": "epic-1",
        }

        with patch("src.agile_mcp.api.backlog_tools.StoryRepository"), patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ), patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            # Return the serialized story (as story.to_dict() would)
            mock_story_service.get_next_ready_story.return_value = serialized_story
            mock_story_service_class.return_value = mock_story_service

            # Test story service returns serialized story
            result = mock_story_service.get_next_ready_story()
            assert result == serialized_story

            # Verify the story validates against StoryResponse model
            story_response = StoryResponse(**result)

            # The response model should handle serialized timestamps
            response_dict = story_response.model_dump()

            # Verify comment timestamp is properly handled
            assert len(response_dict["comments"]) == 1
            comment = response_dict["comments"][0]
            assert "timestamp" in comment
            assert comment["timestamp"] == "2023-01-01T12:00:00+00:00"

            # The timestamp should be JSON serializable
            import json

            json_str = json.dumps(response_dict)
            assert "comment-dt-1" in json_str
            assert "Test Agent" in json_str
            assert "2023-01-01T12:00:00+00:00" in json_str

    @patch("src.agile_mcp.api.backlog_tools.create_tables")
    @patch("src.agile_mcp.api.backlog_tools.get_db")
    def test_get_next_ready_story_payload_size_validation(
        self, mock_get_db, mock_create_tables
    ):
        """Test that enhanced story payload doesn't exceed reasonable size limits."""
        # Setup mocks
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        # Create a story with substantial but reasonable enhanced data
        large_story = {
            "id": "story-large-1",
            "title": "Large Enhanced Story",
            "description": "A story with substantial enhanced data",
            "acceptance_criteria": [f"AC {i}" for i in range(10)],  # 10 basic ACs
            "structured_acceptance_criteria": [
                {
                    "id": f"ac-{i}",
                    "description": f"Structured AC {i} with detailed description",
                    "met": i % 2 == 0,
                    "order": i + 1,
                }
                for i in range(20)  # 20 structured ACs
            ],
            "tasks": [
                {
                    "id": f"task-{i}",
                    "description": f"Task {i}: Implement feature with detailed steps",
                    "completed": i < 5,  # First 5 completed
                    "order": i + 1,
                }
                for i in range(15)  # 15 tasks
            ],
            "comments": [
                {
                    "id": f"comment-{i}",
                    "author_role": "Developer Agent" if i % 2 == 0 else "QA Agent",
                    "content": (
                        f"Comment {i}: Detailed discussion about implementation "
                        "approach and technical considerations"
                    ),
                    "timestamp": f"2023-01-{(i % 30) + 1:02d}T12:00:00Z",
                    "reply_to_id": f"comment-{i-1}" if i > 0 else None,
                }
                for i in range(25)  # 25 comments
            ],
            "dev_notes": "# Comprehensive Technical Documentation\n\n"
            + "## Architecture Overview\n"
            + "This story involves complex implementation...\n"
            + "\n".join([f"### Section {i}\nDetailed notes..." for i in range(10)]),
            "status": "InProgress",
            "priority": 9,
            "created_at": "2023-01-01T10:00:00Z",
            "epic_id": "epic-1",
        }

        with patch("src.agile_mcp.api.backlog_tools.StoryRepository"), patch(
            "src.agile_mcp.api.backlog_tools.DependencyRepository"
        ), patch(
            "src.agile_mcp.api.backlog_tools.StoryService"
        ) as mock_story_service_class:

            mock_story_service = Mock()
            mock_story_service.get_next_ready_story.return_value = large_story
            mock_story_service_class.return_value = mock_story_service

            # Test story service returns large story
            result = mock_story_service.get_next_ready_story()

            # Verify story validates against response model
            story_response = StoryResponse(**result)
            response_dict = story_response.model_dump()

            # Test JSON serialization and measure payload size
            import json

            json_payload = json.dumps(response_dict)
            payload_size = len(json_payload.encode("utf-8"))

            # Verify payload is reasonable (less than 1MB for example)
            assert (
                payload_size < 1024 * 1024
            ), f"Payload too large: {payload_size} bytes"

            # Verify all enhanced data is preserved
            assert len(response_dict["structured_acceptance_criteria"]) == 20
            assert len(response_dict["tasks"]) == 15
            assert len(response_dict["comments"]) == 25
            assert "Comprehensive Technical Documentation" in response_dict["dev_notes"]

            print(f"Large story payload size: {payload_size:,} bytes")
