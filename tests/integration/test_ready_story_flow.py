"""
Integration tests for get next ready story complete workflow.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base, Epic
from src.agile_mcp.models.project import Project
from src.agile_mcp.models.story import Story
from src.agile_mcp.repositories.dependency_repository import DependencyRepository
from src.agile_mcp.repositories.story_repository import StoryRepository
from src.agile_mcp.services.story_service import StoryService


@pytest.fixture
def integration_db():
    """Create an in-memory SQLite database for integration testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test project first
    project = Project(
        id="integration-project-1",
        name="Integration Test Project",
        description="Project for integration testing",
    )
    session.add(project)

    # Create a test epic for story relationships
    epic = Epic(
        id="integration-epic-1",
        title="Integration Test Epic",
        description="Epic for integration testing",
        project_id="integration-project-1",
        status="Ready",
    )
    session.add(epic)
    session.commit()

    yield session
    session.close()


@pytest.fixture
def story_repository(integration_db):
    """Create Story repository with integration database."""
    return StoryRepository(integration_db)


@pytest.fixture
def dependency_repository(integration_db):
    """Create Dependency repository with integration database."""
    return DependencyRepository(integration_db)


@pytest.fixture
def story_service(story_repository, dependency_repository):
    """Create Story service with both repositories."""
    return StoryService(story_repository, dependency_repository)


class TestGetNextReadyStoryIntegration:
    """Integration tests for get next ready story workflow."""

    def test_complete_workflow_with_stories_having_dependencies(
        self, integration_db, story_service, dependency_repository
    ):
        """Test complete workflow with stories having dependencies."""
        base_time = datetime(2023, 1, 1, 12, 0, 0)

        # Create stories with different priorities and dependencies
        story_high_priority_blocked = Story(
            id="story-high-blocked",
            title="High Priority Blocked Story",
            description="High priority but blocked by dependencies",
            acceptance_criteria=["Should not be selected due to dependencies"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=10,
            created_at=base_time,
        )

        story_medium_priority_ready = Story(
            id="story-medium-ready",
            title="Medium Priority Ready Story",
            description="Medium priority with no dependencies",
            acceptance_criteria=["Should be selected as it's ready"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=5,
            created_at=base_time + timedelta(hours=1),
        )

        story_low_priority_ready = Story(
            id="story-low-ready",
            title="Low Priority Ready Story",
            description="Low priority with no dependencies",
            acceptance_criteria=["Should not be selected due to lower priority"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=1,
            created_at=base_time,
        )

        story_dependency = Story(
            id="story-dependency",
            title="Dependency Story",
            description="Story that others depend on",
            acceptance_criteria=["Should be a dependency"],
            epic_id="integration-epic-1",
            status="ToDo",  # Not done yet
            priority=1,
            created_at=base_time,
        )

        # Add all stories to database
        integration_db.add(story_high_priority_blocked)
        integration_db.add(story_medium_priority_ready)
        integration_db.add(story_low_priority_ready)
        integration_db.add(story_dependency)
        integration_db.commit()

        # Add dependency: high priority story depends on story_dependency
        dependency_repository.add_dependency("story-high-blocked", "story-dependency")

        # Test: Get next ready story
        result = story_service.get_next_ready_story()

        # Should return medium priority story (highest priority without dependencies)
        assert result is not None
        assert result["id"] == "story-medium-ready"
        assert result["status"] == "InProgress"  # Status should be updated
        assert result["priority"] == 5

        # Verify the story status was updated in database
        updated_story = (
            integration_db.query(Story).filter(Story.id == "story-medium-ready").first()
        )
        assert updated_story.status == "InProgress"

        # Verify other stories remain ToDo
        high_priority_story = (
            integration_db.query(Story).filter(Story.id == "story-high-blocked").first()
        )
        low_priority_story = (
            integration_db.query(Story).filter(Story.id == "story-low-ready").first()
        )
        dependency_story = (
            integration_db.query(Story).filter(Story.id == "story-dependency").first()
        )

        assert high_priority_story.status == "ToDo"
        assert low_priority_story.status == "ToDo"
        assert dependency_story.status == "ToDo"

    def test_priority_ordering_when_multiple_stories_ready(
        self, integration_db, story_service
    ):
        """Test priority ordering when multiple stories are ready."""
        base_time = datetime(2023, 6, 15, 10, 0, 0)

        # Create multiple stories with different priorities, all ready
        stories = [
            Story(
                id="priority-story-low",
                title="Low Priority Story",
                description="Priority 2",
                acceptance_criteria=["Low priority"],
                epic_id="integration-epic-1",
                status="ToDo",
                priority=2,
                created_at=base_time,
            ),
            Story(
                id="priority-story-high",
                title="High Priority Story",
                description="Priority 8",
                acceptance_criteria=["High priority"],
                epic_id="integration-epic-1",
                status="ToDo",
                priority=8,
                created_at=base_time + timedelta(hours=2),  # Later creation
            ),
            Story(
                id="priority-story-medium",
                title="Medium Priority Story",
                description="Priority 5",
                acceptance_criteria=["Medium priority"],
                epic_id="integration-epic-1",
                status="ToDo",
                priority=5,
                created_at=base_time + timedelta(hours=1),
            ),
        ]

        for story in stories:
            integration_db.add(story)
        integration_db.commit()

        # Get next ready story - should be highest priority
        result = story_service.get_next_ready_story()

        assert result is not None
        assert result["id"] == "priority-story-high"
        assert result["priority"] == 8
        assert result["status"] == "InProgress"

    def test_creation_date_ordering_for_same_priority(
        self, integration_db, story_service
    ):
        """Test creation date ordering for stories with same priority."""
        base_time = datetime(2023, 8, 20, 14, 0, 0)

        # Create stories with same priority but different creation times
        early_story = Story(
            id="same-priority-early",
            title="Early Created Story",
            description="Created first",
            acceptance_criteria=["Earlier creation"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=3,
            created_at=base_time,  # Earliest
        )

        late_story = Story(
            id="same-priority-late",
            title="Late Created Story",
            description="Created last",
            acceptance_criteria=["Later creation"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=3,
            created_at=base_time + timedelta(hours=3),  # Latest
        )

        middle_story = Story(
            id="same-priority-middle",
            title="Middle Created Story",
            description="Created in middle",
            acceptance_criteria=["Middle creation"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=3,
            created_at=base_time + timedelta(hours=1),  # Middle
        )

        # Add in different order
        integration_db.add(late_story)
        integration_db.add(early_story)
        integration_db.add(middle_story)
        integration_db.commit()

        # Should return earliest created story
        result = story_service.get_next_ready_story()

        assert result is not None
        assert result["id"] == "same-priority-early"
        assert result["status"] == "InProgress"

    def test_automatic_status_update_to_inprogress(self, integration_db, story_service):
        """Test automatic status update to InProgress."""
        story = Story(
            id="status-update-story",
            title="Status Update Story",
            description="Should change from ToDo to InProgress",
            acceptance_criteria=["Status should update"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=1,
            created_at=datetime(2023, 10, 1, 9, 0, 0),
        )

        integration_db.add(story)
        integration_db.commit()

        # Verify initial status
        assert story.status == "ToDo"

        # Get next ready story
        result = story_service.get_next_ready_story()

        # Verify result
        assert result is not None
        assert result["id"] == "status-update-story"
        assert result["status"] == "InProgress"

        # Verify database was updated
        updated_story = (
            integration_db.query(Story)
            .filter(Story.id == "status-update-story")
            .first()
        )
        assert updated_story.status == "InProgress"

    def test_empty_response_when_no_stories_ready(
        self, integration_db, story_service, dependency_repository
    ):
        """Test empty response when no stories are ready."""
        # Create stories but all have incomplete dependencies
        story_with_deps = Story(
            id="story-with-deps",
            title="Story With Dependencies",
            description="Has incomplete dependencies",
            acceptance_criteria=["Should not be ready"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=5,
            created_at=datetime(2023, 12, 1, 10, 0, 0),
        )

        dependency_story = Story(
            id="incomplete-dependency",
            title="Incomplete Dependency",
            description="Not done yet",
            acceptance_criteria=["Dependency not complete"],
            epic_id="integration-epic-1",
            status="InProgress",  # Not Done
            priority=1,
            created_at=datetime(2023, 12, 1, 9, 0, 0),
        )

        integration_db.add(story_with_deps)
        integration_db.add(dependency_story)
        integration_db.commit()

        # Add dependency
        dependency_repository.add_dependency("story-with-deps", "incomplete-dependency")

        # Should return None since no stories are ready
        result = story_service.get_next_ready_story()
        assert result is None

    def test_dependency_resolution_when_dependency_becomes_done(
        self, integration_db, story_service, dependency_repository, story_repository
    ):
        """Test that stories become ready when their dependencies are completed."""
        # Create story with dependency
        blocked_story = Story(
            id="blocked-story",
            title="Blocked Story",
            description="Initially blocked by dependency",
            acceptance_criteria=["Should become ready when dependency is done"],
            epic_id="integration-epic-1",
            status="ToDo",
            priority=7,
            created_at=datetime(2023, 11, 15, 11, 0, 0),
        )

        dependency_story = Story(
            id="blocking-dependency",
            title="Blocking Dependency",
            description="Blocks other story",
            acceptance_criteria=["Must be completed first"],
            epic_id="integration-epic-1",
            status="InProgress",  # Not done initially
            priority=1,
            created_at=datetime(2023, 11, 15, 10, 0, 0),
        )

        integration_db.add(blocked_story)
        integration_db.add(dependency_story)
        integration_db.commit()

        # Add dependency
        dependency_repository.add_dependency("blocked-story", "blocking-dependency")

        # Initially, no story should be ready
        result = story_service.get_next_ready_story()
        assert result is None

        # Complete the dependency
        story_repository.update_story_status("blocking-dependency", "Done")

        # Now the blocked story should become ready
        result = story_service.get_next_ready_story()
        assert result is not None
        assert result["id"] == "blocked-story"
        assert result["status"] == "InProgress"
        assert result["priority"] == 7
