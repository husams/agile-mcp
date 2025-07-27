"""
Unit tests for Story model.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base, Epic
from src.agile_mcp.models.story import Story


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test epic for foreign key relationships
    epic = Epic(
        id="test-epic-1",
        title="Test Epic",
        description="Test epic for story relationships",
        status="Draft",
    )
    session.add(epic)
    session.commit()

    yield session
    session.close()


def test_story_creation():
    """Test Story model creation with valid data."""
    story = Story(
        id="test-story-1",
        title="Test Story",
        description="As a user, I want to test the story model",
        acceptance_criteria=[
            "Should create successfully",
            "Should have all required fields",
        ],
        epic_id="test-epic-1",
        status="ToDo",
    )

    assert story.id == "test-story-1"
    assert story.title == "Test Story"
    assert story.description == "As a user, I want to test the story model"
    assert story.acceptance_criteria == [
        "Should create successfully",
        "Should have all required fields",
    ]
    assert story.epic_id == "test-epic-1"
    assert story.status == "ToDo"
    assert story.priority == 0  # default priority
    assert isinstance(story.created_at, datetime)


def test_story_default_status():
    """Test Story model uses default status of 'ToDo'."""
    story = Story(
        id="test-story-2",
        title="Test Story 2",
        description="Another test story",
        acceptance_criteria=["Should have default status"],
        epic_id="test-epic-1",
    )

    assert story.status == "ToDo"
    assert story.priority == 0  # default priority
    assert isinstance(story.created_at, datetime)


def test_story_to_dict():
    """Test Story model to_dict method."""
    story = Story(
        id="test-story-3",
        title="Test Story 3",
        description="Third test story",
        acceptance_criteria=["AC1", "AC2", "AC3"],
        epic_id="test-epic-1",
        status="InProgress",
    )

    story_dict = story.to_dict()

    expected = {
        "id": "test-story-3",
        "title": "Test Story 3",
        "description": "Third test story",
        "acceptance_criteria": ["AC1", "AC2", "AC3"],
        "epic_id": "test-epic-1",
        "status": "InProgress",
        "priority": 0,
        "created_at": story.created_at.isoformat(),
    }

    assert story_dict == expected


def test_story_repr():
    """Test Story model string representation."""
    story = Story(
        id="test-story-4",
        title="Test Story 4",
        description="Fourth test story",
        acceptance_criteria=["Should have repr"],
        epic_id="test-epic-1",
        status="Done",
    )

    repr_str = repr(story)
    assert "test-story-4" in repr_str
    assert "Test Story 4" in repr_str
    assert "Done" in repr_str
    assert "test-epic-1" in repr_str


def test_story_database_persistence(in_memory_db):
    """Test Story model database persistence."""
    story = Story(
        id="test-story-5",
        title="Persistent Story",
        description="This story should persist in the database",
        acceptance_criteria=["Should persist", "Should be retrievable"],
        epic_id="test-epic-1",
        status="Review",
    )

    # Save to database
    in_memory_db.add(story)
    in_memory_db.commit()

    # Retrieve from database
    retrieved_story = in_memory_db.query(Story).filter_by(id="test-story-5").first()

    assert retrieved_story is not None
    assert retrieved_story.id == "test-story-5"
    assert retrieved_story.title == "Persistent Story"
    assert retrieved_story.description == "This story should persist in the database"
    assert retrieved_story.acceptance_criteria == [
        "Should persist",
        "Should be retrievable",
    ]
    assert retrieved_story.epic_id == "test-epic-1"
    assert retrieved_story.status == "Review"


def test_story_epic_relationship(in_memory_db):
    """Test Story-Epic relationship."""
    story = Story(
        id="test-story-6",
        title="Related Story",
        description="Story with epic relationship",
        acceptance_criteria=["Should relate to epic"],
        epic_id="test-epic-1",
        status="ToDo",
    )

    # Save to database
    in_memory_db.add(story)
    in_memory_db.commit()

    # Test relationship from story to epic
    retrieved_story = in_memory_db.query(Story).filter_by(id="test-story-6").first()
    assert retrieved_story.epic is not None
    assert retrieved_story.epic.id == "test-epic-1"
    assert retrieved_story.epic.title == "Test Epic"

    # Test relationship from epic to stories
    epic = in_memory_db.query(Epic).filter_by(id="test-epic-1").first()
    story_ids = [s.id for s in epic.stories]
    assert "test-story-6" in story_ids


def test_story_title_validation():
    """Test Story model title validation."""
    # Test empty title
    with pytest.raises(ValueError, match="Story title cannot be empty"):
        Story(
            id="test-story-7",
            title="",
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-1",
        )

    # Test title too long
    long_title = "x" * 201
    with pytest.raises(ValueError, match="Story title cannot exceed 200 characters"):
        Story(
            id="test-story-8",
            title=long_title,
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-1",
        )


def test_story_description_validation():
    """Test Story model description validation."""
    # Test empty description
    with pytest.raises(ValueError, match="Story description cannot be empty"):
        Story(
            id="test-story-9",
            title="Valid title",
            description="",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-1",
        )

    # Test description too long
    long_description = "x" * 2001
    with pytest.raises(
        ValueError, match="Story description cannot exceed 2000 characters"
    ):
        Story(
            id="test-story-10",
            title="Valid title",
            description=long_description,
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-1",
        )


def test_story_acceptance_criteria_validation():
    """Test Story model acceptance criteria validation."""
    # Test empty list
    with pytest.raises(
        ValueError, match="At least one acceptance criterion is required"
    ):
        Story(
            id="test-story-11",
            title="Valid title",
            description="Valid description",
            acceptance_criteria=[],
            epic_id="test-epic-1",
        )

    # Test non-list
    with pytest.raises(
        ValueError, match="Acceptance criteria must be a non-empty list"
    ):
        Story(
            id="test-story-12",
            title="Valid title",
            description="Valid description",
            acceptance_criteria="not a list",
            epic_id="test-epic-1",
        )

    # Test empty string in list
    with pytest.raises(
        ValueError, match="Each acceptance criterion must be a non-empty string"
    ):
        Story(
            id="test-story-13",
            title="Valid title",
            description="Valid description",
            acceptance_criteria=["Valid AC", ""],
            epic_id="test-epic-1",
        )


def test_story_status_validation():
    """Test Story model status validation."""
    # Test invalid status
    with pytest.raises(ValueError, match="Story status must be one of"):
        Story(
            id="test-story-14",
            title="Valid title",
            description="Valid description",
            acceptance_criteria=["Valid AC"],
            epic_id="test-epic-1",
            status="InvalidStatus",
        )


def test_story_priority_field():
    """Test Story model priority field."""
    # Test with custom priority
    story = Story(
        id="test-story-15",
        title="Priority Story",
        description="Story with custom priority",
        acceptance_criteria=["Should have priority"],
        epic_id="test-epic-1",
        priority=5,
    )

    assert story.priority == 5

    # Test default priority
    story_default = Story(
        id="test-story-16",
        title="Default Priority Story",
        description="Story with default priority",
        acceptance_criteria=["Should have default priority"],
        epic_id="test-epic-1",
    )

    assert story_default.priority == 0


def test_story_created_at_field():
    """Test Story model created_at field."""
    # Test with custom created_at
    custom_time = datetime(2023, 1, 1, 12, 0, 0)
    story = Story(
        id="test-story-17",
        title="Custom Time Story",
        description="Story with custom created_at",
        acceptance_criteria=["Should have custom time"],
        epic_id="test-epic-1",
        created_at=custom_time,
    )

    assert story.created_at == custom_time

    # Test default created_at (should be current time)
    before_creation = datetime.now(timezone.utc)
    story_default = Story(
        id="test-story-18",
        title="Default Time Story",
        description="Story with default created_at",
        acceptance_criteria=["Should have default time"],
        epic_id="test-epic-1",
    )
    after_creation = datetime.now(timezone.utc)

    assert before_creation <= story_default.created_at <= after_creation


def test_story_priority_created_at_persistence(in_memory_db):
    """Test Story model priority and created_at persistence in database."""
    custom_time = datetime(2023, 6, 15, 10, 30, 0)
    story = Story(
        id="test-story-19",
        title="Persistent Priority Story",
        description="Story with priority and created_at to persist",
        acceptance_criteria=["Should persist priority", "Should persist created_at"],
        epic_id="test-epic-1",
        priority=10,
        created_at=custom_time,
    )

    # Save to database
    in_memory_db.add(story)
    in_memory_db.commit()

    # Retrieve from database
    retrieved_story = in_memory_db.query(Story).filter_by(id="test-story-19").first()

    assert retrieved_story is not None
    assert retrieved_story.priority == 10
    assert retrieved_story.created_at == custom_time


def test_story_to_dict_with_priority_created_at():
    """Test Story model to_dict method includes priority and created_at."""
    custom_time = datetime(2023, 8, 20, 15, 45, 30)
    story = Story(
        id="test-story-20",
        title="Dict Test Story",
        description="Story for testing to_dict with new fields",
        acceptance_criteria=["Should include priority", "Should include created_at"],
        epic_id="test-epic-1",
        status="Review",
        priority=7,
        created_at=custom_time,
    )

    story_dict = story.to_dict()

    expected = {
        "id": "test-story-20",
        "title": "Dict Test Story",
        "description": "Story for testing to_dict with new fields",
        "acceptance_criteria": ["Should include priority", "Should include created_at"],
        "epic_id": "test-epic-1",
        "status": "Review",
        "priority": 7,
        "created_at": custom_time.isoformat(),
    }

    assert story_dict == expected
