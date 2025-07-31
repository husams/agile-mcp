"""
Integration tests for enhanced getNextReadyStory functionality.

These tests use real database operations to verify the complete workflow
of creating stories with enhanced fields and retrieving them via getNextReadyStory.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.agile_mcp.models.epic import Base
from src.agile_mcp.repositories.dependency_repository import DependencyRepository
from src.agile_mcp.repositories.epic_repository import EpicRepository
from src.agile_mcp.repositories.project_repository import ProjectRepository
from src.agile_mcp.repositories.story_repository import StoryRepository
from src.agile_mcp.services.dependency_service import DependencyService
from src.agile_mcp.services.epic_service import EpicService
from src.agile_mcp.services.project_service import ProjectService
from src.agile_mcp.services.story_service import StoryService


@pytest.fixture
def integration_db():
    """Create a temporary database for integration testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Set up database URL
    db_url = f"sqlite:///{db_path}"

    # Create engine and tables
    from sqlalchemy import create_engine as sa_create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = sa_create_engine(
        db_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield SessionLocal

    # Cleanup
    engine.dispose()
    Path(db_path).unlink(missing_ok=True)


class TestEnhancedGetNextReadyStoryIntegration:
    """Integration tests for enhanced getNextReadyStory functionality."""

    def test_create_and_retrieve_enhanced_story(self, integration_db):
        """Test creating a story with enhanced fields and retrieving it via
        getNextReadyStory."""
        db_session = integration_db()

        try:
            # Create repositories and services
            project_repository = ProjectRepository(db_session)
            epic_repository = EpicRepository(db_session)
            story_repository = StoryRepository(db_session)
            dependency_repository = DependencyRepository(db_session)

            project_service = ProjectService(project_repository)
            epic_service = EpicService(epic_repository)
            story_service = StoryService(story_repository, dependency_repository)

            # Create a test project
            project = project_service.create_project(
                "Integration Test Project", "Project for integration testing"
            )
            project_id = project["id"]

            # Create a test epic
            epic = epic_service.create_epic(
                "Integration Test Epic", "Epic for integration testing", project_id
            )
            epic_id = epic["id"]

            # Create enhanced story data
            tasks = [
                {
                    "id": "task-1",
                    "description": "Implement feature X",
                    "completed": False,
                    "order": 1,
                },
                {
                    "id": "task-2",
                    "description": "Write comprehensive tests",
                    "completed": False,
                    "order": 2,
                },
            ]

            structured_ac = [
                {
                    "id": "ac-1",
                    "description": "Feature X must handle edge cases",
                    "met": False,
                    "order": 1,
                },
                {
                    "id": "ac-2",
                    "description": "Performance must be under 100ms",
                    "met": False,
                    "order": 2,
                },
            ]

            comments = [
                {
                    "id": "comment-1",
                    "author_role": "Product Owner",
                    "content": "This is a high-priority feature for Q1",
                    "timestamp": "2023-01-01T10:00:00+00:00",  # ISO format string
                    "reply_to_id": None,
                }
            ]

            dev_notes = """# Technical Implementation Guide

## Architecture Overview
This story requires implementing a new API endpoint with the following characteristics:
- RESTful design following existing patterns
- Input validation using Pydantic models
- Proper error handling and logging
- Database operations via SQLAlchemy

## Performance Requirements
- Response time < 100ms for typical requests
- Handle up to 1000 concurrent requests
- Efficient database queries with proper indexing

## Testing Strategy
- Unit tests for all business logic
- Integration tests for database operations
- E2E tests for API endpoints
- Performance tests for load requirements

## Implementation Notes
Ready for development with complete technical context.
"""

            # Create enhanced story
            story = story_service.create_story(
                title="Enhanced Integration Test Story",
                description="A story with all enhanced fields for integration testing",
                acceptance_criteria=["Basic AC 1", "Basic AC 2"],
                epic_id=epic_id,
                tasks=tasks,
                structured_acceptance_criteria=structured_ac,
                comments=comments,
                dev_notes=dev_notes,
                priority=9,
            )

            story_id = story["id"]
            assert story_id is not None

            # Verify enhanced fields were stored
            assert len(story["tasks"]) == 2
            assert len(story["structured_acceptance_criteria"]) == 2
            assert len(story["comments"]) == 1
            assert "Technical Implementation Guide" in story["dev_notes"]

            # Test getNextReadyStory returns the enhanced story
            next_story = story_service.get_next_ready_story()
            assert next_story is not None
            assert next_story["id"] == story_id
            assert next_story["status"] == "InProgress"  # Updated by getNextReadyStory

            # Verify all enhanced fields are included in response
            assert "structured_acceptance_criteria" in next_story
            assert "tasks" in next_story
            assert "comments" in next_story
            assert "dev_notes" in next_story

            # Verify enhanced field contents
            assert len(next_story["structured_acceptance_criteria"]) == 2
            assert next_story["structured_acceptance_criteria"][0]["id"] == "ac-1"
            assert (
                next_story["structured_acceptance_criteria"][0]["description"]
                == "Feature X must handle edge cases"
            )

            assert len(next_story["tasks"]) == 2
            assert next_story["tasks"][0]["id"] == "task-1"
            assert next_story["tasks"][0]["description"] == "Implement feature X"

            assert len(next_story["comments"]) == 1
            assert next_story["comments"][0]["author_role"] == "Product Owner"
            assert (
                next_story["comments"][0]["content"]
                == "This is a high-priority feature for Q1"
            )
            # Verify timestamp is in ISO format
            assert isinstance(next_story["comments"][0]["timestamp"], str)
            assert next_story["comments"][0]["timestamp"] == "2023-01-01T10:00:00+00:00"

            assert "Technical Implementation Guide" in next_story["dev_notes"]
            assert "Performance Requirements" in next_story["dev_notes"]

        finally:
            db_session.rollback()
            db_session.close()

    def test_enhanced_story_with_dependencies(self, integration_db):
        """Test that dependency logic works correctly with enhanced stories."""
        db_session = integration_db()

        try:
            # Create repositories and services
            project_repository = ProjectRepository(db_session)
            epic_repository = EpicRepository(db_session)
            story_repository = StoryRepository(db_session)
            dependency_repository = DependencyRepository(db_session)

            project_service = ProjectService(project_repository)
            epic_service = EpicService(epic_repository)
            story_service = StoryService(story_repository, dependency_repository)
            dependency_service = DependencyService(dependency_repository)

            # Create test project
            project = project_service.create_project(
                "Dependency Test Project", "Project for dependency testing"
            )
            project_id = project["id"]

            # Create test epic
            epic = epic_service.create_epic(
                "Dependency Test Epic", "Epic for dependency testing", project_id
            )
            epic_id = epic["id"]

            # Create foundation story (no dependencies)
            foundation_tasks = [
                {
                    "id": "foundation-task-1",
                    "description": "Set up base architecture",
                    "completed": False,
                    "order": 1,
                }
            ]
            foundation_ac = [
                {
                    "id": "foundation-ac-1",
                    "description": "Architecture must be scalable",
                    "met": False,
                    "order": 1,
                }
            ]

            foundation_story = story_service.create_story(
                title="Foundation Story",
                description="Foundation story that others depend on",
                acceptance_criteria=["Foundation AC"],
                epic_id=epic_id,
                tasks=foundation_tasks,
                structured_acceptance_criteria=foundation_ac,
                comments=[],
                dev_notes="Foundation implementation notes",
                priority=10,  # Highest priority
            )

            # Create dependent story
            dependent_tasks = [
                {
                    "id": "dependent-task-1",
                    "description": "Build on foundation",
                    "completed": False,
                    "order": 1,
                }
            ]
            dependent_ac = [
                {
                    "id": "dependent-ac-1",
                    "description": "Must integrate with foundation",
                    "met": False,
                    "order": 1,
                }
            ]

            dependent_story = story_service.create_story(
                title="Dependent Story",
                description="Story that depends on foundation",
                acceptance_criteria=["Dependent AC"],
                epic_id=epic_id,
                tasks=dependent_tasks,
                structured_acceptance_criteria=dependent_ac,
                comments=[],
                dev_notes="Dependent implementation notes",
                priority=8,
            )

            # Add dependency: dependent_story depends on foundation_story
            dependency_service.add_story_dependency(
                dependent_story["id"], foundation_story["id"]
            )

            # Test getNextReadyStory returns foundation story (no dependencies)
            next_story = story_service.get_next_ready_story()
            assert next_story is not None
            assert next_story["id"] == foundation_story["id"]
            assert next_story["title"] == "Foundation Story"
            assert next_story["status"] == "InProgress"

            # Verify enhanced fields are included
            assert len(next_story["tasks"]) == 1
            assert next_story["tasks"][0]["id"] == "foundation-task-1"
            assert len(next_story["structured_acceptance_criteria"]) == 1
            assert (
                next_story["structured_acceptance_criteria"][0]["id"]
                == "foundation-ac-1"
            )
            assert "Foundation implementation notes" in next_story["dev_notes"]

            # Complete the foundation story
            story_service.update_story_status(foundation_story["id"], "Done")

            # Now getNextReadyStory should return the dependent story
            next_story = story_service.get_next_ready_story()
            assert next_story is not None
            assert next_story["id"] == dependent_story["id"]
            assert next_story["title"] == "Dependent Story"
            assert next_story["status"] == "InProgress"

            # Verify enhanced fields for dependent story
            assert len(next_story["tasks"]) == 1
            assert next_story["tasks"][0]["id"] == "dependent-task-1"
            assert len(next_story["structured_acceptance_criteria"]) == 1
            assert (
                next_story["structured_acceptance_criteria"][0]["id"]
                == "dependent-ac-1"
            )
            assert "Dependent implementation notes" in next_story["dev_notes"]

        finally:
            db_session.rollback()
            db_session.close()

    def test_enhanced_story_json_serialization_integration(self, integration_db):
        """Test JSON serialization of enhanced stories in integration environment."""
        db_session = integration_db()

        try:
            # Create repositories and services
            project_repository = ProjectRepository(db_session)
            epic_repository = EpicRepository(db_session)
            story_repository = StoryRepository(db_session)
            dependency_repository = DependencyRepository(db_session)

            project_service = ProjectService(project_repository)
            epic_service = EpicService(epic_repository)
            story_service = StoryService(story_repository, dependency_repository)

            # Create test project
            project = project_service.create_project(
                "JSON Test Project", "Project for JSON serialization testing"
            )
            project_id = project["id"]

            # Create test epic
            epic = epic_service.create_epic(
                "JSON Test Epic", "Epic for JSON serialization testing", project_id
            )
            epic_id = epic["id"]

            # Create story with complex enhanced data
            complex_tasks = [
                {
                    "id": f"task-{i}",
                    "description": (
                        f"Task {i}: Complex implementation with special chars: "
                        "àáâã & <>&\"'"
                    ),
                    "completed": i % 2 == 0,
                    "order": i + 1,
                }
                for i in range(5)
            ]

            complex_ac = [
                {
                    "id": f"ac-{i}",
                    "description": f"AC {i}: Verify special handling of unicode: àáâã",
                    "met": False,
                    "order": i + 1,
                }
                for i in range(3)
            ]

            complex_comments = [
                {
                    "id": "comment-unicode",
                    "author_role": "Developer Agent",
                    "content": "Unicode test: àáâã ñöüß 中文 🚀 emoji test",
                    "timestamp": "2023-01-15T12:00:00+00:00",  # ISO format string
                    "reply_to_id": None,
                }
            ]

            complex_dev_notes = """# Complex Implementation Notes

## Unicode Handling
This implementation must properly handle unicode characters: àáâã ñöüß 中文

## Special Characters
- HTML entities: &lt; &gt; &amp; &quot; &#x27;
- JSON special chars: {} [] " \\ / \b \f \n \r \t
- Emoji support: 🚀 💻 ✅ ❌

## Code Examples
```python
def handle_unicode(text: str) -> str:
    return text.encode('utf-8').decode('utf-8')
```

## Summary
Implementation complete within 10KB dev_notes limit.
"""

            # Create story with complex data
            story_service.create_story(
                title="Unicode & JSON Test Story àáâã",
                description=(
                    "Story testing unicode and JSON serialization àáâã ñöüß 中文 🚀"
                ),
                acceptance_criteria=[
                    "Must handle unicode: àáâã",
                    'Must serialize JSON properly: {} [] " \\',
                ],
                epic_id=epic_id,
                tasks=complex_tasks,
                structured_acceptance_criteria=complex_ac,
                comments=complex_comments,
                dev_notes=complex_dev_notes,
                priority=7,
            )

            # Get story via getNextReadyStory
            next_story = story_service.get_next_ready_story()
            assert next_story is not None

            # Test JSON serialization
            json_str = json.dumps(next_story, ensure_ascii=False)

            # Verify JSON can be parsed back
            parsed_story = json.loads(json_str)

            # Verify unicode is preserved
            assert "àáâã" in parsed_story["title"]
            assert "àáâã ñöüß 中文 🚀" in parsed_story["description"]
            assert "🚀 emoji test" in parsed_story["comments"][0]["content"]
            assert "àáâã ñöüß 中文" in parsed_story["dev_notes"]

            # Verify structure is preserved
            assert len(parsed_story["tasks"]) == 5
            assert len(parsed_story["structured_acceptance_criteria"]) == 3
            assert len(parsed_story["comments"]) == 1

            # Verify special characters in tasks
            task_descriptions = [task["description"] for task in parsed_story["tasks"]]
            assert any("àáâã & <>&\"'" in desc for desc in task_descriptions)

        finally:
            db_session.rollback()
            db_session.close()

    def test_enhanced_story_payload_performance(self, integration_db):
        """Test performance and payload size with large enhanced stories."""
        db_session = integration_db()

        try:
            # Create repositories and services
            project_repository = ProjectRepository(db_session)
            epic_repository = EpicRepository(db_session)
            story_repository = StoryRepository(db_session)
            dependency_repository = DependencyRepository(db_session)

            project_service = ProjectService(project_repository)
            epic_service = EpicService(epic_repository)
            story_service = StoryService(story_repository, dependency_repository)

            # Create test project
            project = project_service.create_project(
                "Performance Test Project", "Project for performance testing"
            )
            project_id = project["id"]

            # Create test epic
            epic = epic_service.create_epic(
                "Performance Test Epic", "Epic for performance testing", project_id
            )
            epic_id = epic["id"]

            # Create large enhanced data
            large_tasks = [
                {
                    "id": f"perf-task-{i}",
                    "description": f"Performance task {i}: "
                    + "x" * 100,  # 100 char description
                    "completed": i < 10,  # First 10 completed
                    "order": i + 1,
                }
                for i in range(50)  # 50 tasks
            ]

            large_ac = [
                {
                    "id": f"perf-ac-{i}",
                    "description": f"Performance AC {i}: "
                    + "y" * 200,  # 200 char description
                    "met": i < 5,  # First 5 met
                    "order": i + 1,
                }
                for i in range(30)  # 30 acceptance criteria
            ]

            large_comments = [
                {
                    "id": f"perf-comment-{i}",
                    "author_role": "Performance Agent" if i % 2 == 0 else "Load Tester",
                    "content": f"Performance comment {i}: "
                    + "z" * 500,  # 500 char content
                    "timestamp": (
                        f"2023-01-{(i % 28) + 1:02d}T12:00:00+00:00"
                    ),  # ISO format string
                    "reply_to_id": f"perf-comment-{i-1}" if i > 0 else None,
                }
                for i in range(20)  # 20 comments
            ]

            large_dev_notes = "# Performance Implementation\n\n" + "\n".join(
                [
                    f"## Section {i}\n" + "Performance notes " + ("x" * 200)
                    for i in range(10)
                ]
            )  # ~3KB of dev notes (within 10KB limit)

            # Measure creation time
            import time

            start_time = time.time()

            story_service.create_story(
                title="Large Performance Test Story",
                description=("Story with large enhanced data for performance testing"),
                acceptance_criteria=[f"Perf AC {i}" for i in range(10)],
                epic_id=epic_id,
                tasks=large_tasks,
                structured_acceptance_criteria=large_ac,
                comments=large_comments,
                dev_notes=large_dev_notes,
                priority=9,
            )

            creation_time = time.time() - start_time
            print(f"Story creation time: {creation_time:.3f}s")

            # Measure retrieval time
            start_time = time.time()
            next_story = story_service.get_next_ready_story()
            retrieval_time = time.time() - start_time
            print(f"Story retrieval time: {retrieval_time:.3f}s")

            assert next_story is not None

            # Measure JSON serialization time and size
            start_time = time.time()
            json_str = json.dumps(next_story)
            serialization_time = time.time() - start_time
            payload_size = len(json_str.encode("utf-8"))

            print(f"JSON serialization time: {serialization_time:.3f}s")
            print(
                f"Payload size: {payload_size:,} bytes " f"({payload_size/1024:.1f} KB)"
            )

            # Performance assertions (reasonable limits)
            assert creation_time < 5.0, f"Story creation too slow: {creation_time:.3f}s"
            assert (
                retrieval_time < 2.0
            ), f"Story retrieval too slow: {retrieval_time:.3f}s"
            assert (
                serialization_time < 1.0
            ), f"JSON serialization too slow: {serialization_time:.3f}s"
            assert (
                payload_size < 2 * 1024 * 1024
            ), f"Payload too large: {payload_size:,} bytes"  # < 2MB

            # Verify data integrity
            assert len(next_story["tasks"]) == 50
            assert len(next_story["structured_acceptance_criteria"]) == 30
            assert len(next_story["comments"]) == 20
            assert len(next_story["dev_notes"]) > 2000  # ~2KB+

        finally:
            db_session.rollback()
            db_session.close()
