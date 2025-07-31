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
        "structured_acceptance_criteria": [],
        "tasks": [],
        "comments": [],
        "dev_notes": None,
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
        "structured_acceptance_criteria": [],
        "tasks": [],
        "comments": [],
        "dev_notes": None,
        "epic_id": "test-epic-1",
        "status": "Review",
        "priority": 7,
        "created_at": custom_time.isoformat(),
    }

    assert story_dict == expected


def test_story_with_empty_tasks():
    """Test Story model creation with empty tasks list."""
    story = Story(
        id="test-story-21",
        title="Empty Tasks Story",
        description="Story with empty tasks list",
        acceptance_criteria=["Should have empty tasks"],
        epic_id="test-epic-1",
    )

    assert story.tasks == []
    assert isinstance(story.tasks, list)


def test_story_with_tasks():
    """Test Story model creation with tasks."""
    tasks = [
        {"id": "task-1", "description": "First task", "completed": False, "order": 1},
        {"id": "task-2", "description": "Second task", "completed": True, "order": 2},
    ]

    story = Story(
        id="test-story-22",
        title="Tasks Story",
        description="Story with tasks",
        acceptance_criteria=["Should have tasks"],
        epic_id="test-epic-1",
        tasks=tasks,
    )

    assert len(story.tasks) == 2
    assert story.tasks[0]["id"] == "task-1"
    assert story.tasks[0]["description"] == "First task"
    assert story.tasks[0]["completed"] is False
    assert story.tasks[0]["order"] == 1
    assert story.tasks[1]["completed"] is True


def test_story_to_dict_with_tasks():
    """Test Story model to_dict method includes tasks."""
    tasks = [
        {"id": "task-1", "description": "Test task", "completed": False, "order": 1}
    ]

    story = Story(
        id="test-story-23",
        title="Dict Tasks Story",
        description="Story for testing to_dict with tasks",
        acceptance_criteria=["Should include tasks"],
        epic_id="test-epic-1",
        tasks=tasks,
    )

    story_dict = story.to_dict()

    assert "tasks" in story_dict
    assert story_dict["tasks"] == tasks
    assert len(story_dict["tasks"]) == 1
    assert story_dict["tasks"][0]["id"] == "task-1"


def test_story_tasks_validation_empty_list():
    """Test Story model tasks validation with empty list."""
    story = Story(
        id="test-story-24",
        title="Valid Empty Tasks",
        description="Story with valid empty tasks",
        acceptance_criteria=["Should accept empty tasks"],
        epic_id="test-epic-1",
        tasks=[],
    )

    assert story.tasks == []


def test_story_tasks_validation_invalid_type():
    """Test Story model tasks validation with invalid type."""
    with pytest.raises(ValueError, match="Tasks must be a list"):
        Story(
            id="test-story-25",
            title="Invalid Tasks Type",
            description="Story with invalid tasks type",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            tasks="not a list",
        )


def test_story_tasks_validation_invalid_task_structure():
    """Test Story model tasks validation with invalid task structure."""
    # Missing required fields
    with pytest.raises(ValueError, match="missing required fields"):
        Story(
            id="test-story-26",
            title="Invalid Task Structure",
            description="Story with invalid task structure",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            tasks=[{"id": "task-1", "description": "Missing fields"}],
        )

    # Empty description
    with pytest.raises(ValueError, match="must have a non-empty string description"):
        Story(
            id="test-story-27",
            title="Empty Task Description",
            description="Story with empty task description",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            tasks=[{"id": "task-1", "description": "", "completed": False, "order": 1}],
        )

    # Invalid completed type
    with pytest.raises(ValueError, match="completed field must be a boolean"):
        Story(
            id="test-story-28",
            title="Invalid Completed Type",
            description="Story with invalid completed type",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            tasks=[
                {
                    "id": "task-1",
                    "description": "Valid description",
                    "completed": "not a boolean",
                    "order": 1,
                }
            ],
        )

    # Invalid order type
    with pytest.raises(ValueError, match="order field must be an integer"):
        Story(
            id="test-story-29",
            title="Invalid Order Type",
            description="Story with invalid order type",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            tasks=[
                {
                    "id": "task-1",
                    "description": "Valid description",
                    "completed": False,
                    "order": "not an integer",
                }
            ],
        )


def test_story_tasks_validation_duplicate_ids():
    """Test Story model tasks validation with duplicate task IDs."""
    with pytest.raises(ValueError, match="Task id 'task-1' is not unique"):
        Story(
            id="test-story-30",
            title="Duplicate Task IDs",
            description="Story with duplicate task IDs",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            tasks=[
                {
                    "id": "task-1",
                    "description": "First task",
                    "completed": False,
                    "order": 1,
                },
                {
                    "id": "task-1",
                    "description": "Duplicate ID task",
                    "completed": False,
                    "order": 2,
                },
            ],
        )


def test_story_tasks_validation_duplicate_orders():
    """Test Story model tasks validation with duplicate task orders."""
    with pytest.raises(ValueError, match="Task order 1 is not unique"):
        Story(
            id="test-story-31",
            title="Duplicate Task Orders",
            description="Story with duplicate task orders",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            tasks=[
                {
                    "id": "task-1",
                    "description": "First task",
                    "completed": False,
                    "order": 1,
                },
                {
                    "id": "task-2",
                    "description": "Duplicate order task",
                    "completed": False,
                    "order": 1,
                },
            ],
        )


def test_story_tasks_database_persistence(in_memory_db):
    """Test Story model tasks persistence in database."""
    tasks = [
        {
            "id": "task-1",
            "description": "Persistent task",
            "completed": True,
            "order": 1,
        }
    ]

    story = Story(
        id="test-story-32",
        title="Persistent Tasks Story",
        description="Story with tasks to persist",
        acceptance_criteria=["Should persist tasks"],
        epic_id="test-epic-1",
        tasks=tasks,
    )

    # Save to database
    in_memory_db.add(story)
    in_memory_db.commit()

    # Retrieve from database
    retrieved_story = in_memory_db.query(Story).filter_by(id="test-story-32").first()

    assert retrieved_story is not None
    assert len(retrieved_story.tasks) == 1
    assert retrieved_story.tasks[0]["id"] == "task-1"
    assert retrieved_story.tasks[0]["description"] == "Persistent task"
    assert retrieved_story.tasks[0]["completed"] is True
    assert retrieved_story.tasks[0]["order"] == 1


def test_story_structured_acceptance_criteria_validation():
    """Test Story model structured acceptance criteria validation."""
    valid_criteria = [
        {
            "id": "ac-1",
            "description": "First acceptance criterion",
            "met": False,
            "order": 1,
        },
        {
            "id": "ac-2",
            "description": "Second acceptance criterion",
            "met": True,
            "order": 2,
        },
    ]

    story = Story(
        id="test-story-100",
        title="AC Test Story",
        description="Story with structured acceptance criteria",
        acceptance_criteria=["Traditional criterion"],
        structured_acceptance_criteria=valid_criteria,
        epic_id="test-epic-1",
    )

    assert story.structured_acceptance_criteria == valid_criteria
    assert len(story.structured_acceptance_criteria) == 2
    assert story.structured_acceptance_criteria[0]["id"] == "ac-1"
    assert story.structured_acceptance_criteria[1]["met"] is True


def test_story_structured_acceptance_criteria_empty_list():
    """Test Story model with empty structured acceptance criteria list."""
    story = Story(
        id="test-story-101",
        title="Empty AC Test Story",
        description="Story with empty structured acceptance criteria",
        acceptance_criteria=["Traditional criterion"],
        structured_acceptance_criteria=[],
        epic_id="test-epic-1",
    )

    assert story.structured_acceptance_criteria == []


def test_story_structured_acceptance_criteria_invalid_format():
    """Test Story model validation with invalid structured acceptance criteria."""
    with pytest.raises(
        ValueError, match="Acceptance criterion at index 0 must be a dictionary"
    ):
        Story(
            id="test-story-102",
            title="Invalid AC Format Story",
            description="Story with invalid structured acceptance criteria",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=["invalid-string"],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_missing_required_fields():
    """Test Story model validation with missing required fields in acceptance
    criteria."""
    with pytest.raises(ValueError, match="missing required fields"):
        Story(
            id="test-story-103",
            title="Missing Fields AC Story",
            description="Story with missing required fields in acceptance criteria",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=[
                {
                    "id": "ac-1",
                    "description": "Missing met and order fields",
                }
            ],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_invalid_id():
    """Test Story model validation with invalid acceptance criterion ID."""
    with pytest.raises(ValueError, match="must have a non-empty string id"):
        Story(
            id="test-story-104",
            title="Invalid ID AC Story",
            description="Story with invalid acceptance criterion ID",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=[
                {
                    "id": "",
                    "description": "Empty ID criterion",
                    "met": False,
                    "order": 1,
                }
            ],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_duplicate_id():
    """Test Story model validation with duplicate acceptance criterion IDs."""
    with pytest.raises(ValueError, match="is not unique"):
        Story(
            id="test-story-105",
            title="Duplicate ID AC Story",
            description="Story with duplicate acceptance criterion IDs",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=[
                {
                    "id": "ac-1",
                    "description": "First criterion",
                    "met": False,
                    "order": 1,
                },
                {
                    "id": "ac-1",
                    "description": "Duplicate ID criterion",
                    "met": False,
                    "order": 2,
                },
            ],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_invalid_description():
    """Test Story model validation with invalid acceptance criterion description."""
    with pytest.raises(ValueError, match="must have a non-empty string description"):
        Story(
            id="test-story-106",
            title="Invalid Description AC Story",
            description="Story with invalid acceptance criterion description",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=[
                {
                    "id": "ac-1",
                    "description": "",
                    "met": False,
                    "order": 1,
                }
            ],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_invalid_met_field():
    """Test Story model validation with invalid met field."""
    with pytest.raises(ValueError, match="met field must be a boolean"):
        Story(
            id="test-story-107",
            title="Invalid Met Field AC Story",
            description="Story with invalid met field in acceptance criteria",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=[
                {
                    "id": "ac-1",
                    "description": "Invalid met field criterion",
                    "met": "invalid",
                    "order": 1,
                }
            ],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_invalid_order_field():
    """Test Story model validation with invalid order field."""
    with pytest.raises(ValueError, match="order field must be an integer"):
        Story(
            id="test-story-108",
            title="Invalid Order Field AC Story",
            description="Story with invalid order field in acceptance criteria",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=[
                {
                    "id": "ac-1",
                    "description": "Invalid order field criterion",
                    "met": False,
                    "order": "invalid",
                }
            ],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_duplicate_order():
    """Test Story model validation with duplicate acceptance criterion orders."""
    with pytest.raises(ValueError, match="order.*is not unique"):
        Story(
            id="test-story-109",
            title="Duplicate Order AC Story",
            description="Story with duplicate acceptance criterion orders",
            acceptance_criteria=["Traditional criterion"],
            structured_acceptance_criteria=[
                {
                    "id": "ac-1",
                    "description": "First criterion",
                    "met": False,
                    "order": 1,
                },
                {
                    "id": "ac-2",
                    "description": "Duplicate order criterion",
                    "met": False,
                    "order": 1,
                },
            ],
            epic_id="test-epic-1",
        )


def test_story_structured_acceptance_criteria_database_persistence(in_memory_db):
    """Test Story model structured acceptance criteria persistence in database."""
    criteria = [
        {
            "id": "ac-1",
            "description": "Persistent acceptance criterion",
            "met": True,
            "order": 1,
        },
        {
            "id": "ac-2",
            "description": "Second persistent criterion",
            "met": False,
            "order": 2,
        },
    ]

    story = Story(
        id="test-story-110",
        title="Persistent AC Story",
        description="Story with structured acceptance criteria to persist",
        acceptance_criteria=["Should persist criteria"],
        structured_acceptance_criteria=criteria,
        epic_id="test-epic-1",
    )

    # Save to database
    in_memory_db.add(story)
    in_memory_db.commit()

    # Retrieve from database
    retrieved_story = in_memory_db.query(Story).filter_by(id="test-story-110").first()

    assert retrieved_story is not None
    assert len(retrieved_story.structured_acceptance_criteria) == 2
    assert retrieved_story.structured_acceptance_criteria[0]["id"] == "ac-1"
    assert (
        retrieved_story.structured_acceptance_criteria[0]["description"]
        == "Persistent acceptance criterion"
    )
    assert retrieved_story.structured_acceptance_criteria[0]["met"] is True
    assert retrieved_story.structured_acceptance_criteria[0]["order"] == 1
    assert retrieved_story.structured_acceptance_criteria[1]["id"] == "ac-2"
    assert retrieved_story.structured_acceptance_criteria[1]["met"] is False


def test_story_to_dict_includes_structured_acceptance_criteria():
    """Test that Story.to_dict() includes structured acceptance criteria."""
    criteria = [
        {
            "id": "ac-1",
            "description": "Test criterion",
            "met": False,
            "order": 1,
        }
    ]

    story = Story(
        id="test-story-111",
        title="To Dict Test Story",
        description="Story for testing to_dict method",
        acceptance_criteria=["Traditional criterion"],
        structured_acceptance_criteria=criteria,
        epic_id="test-epic-1",
    )

    story_dict = story.to_dict()

    assert "structured_acceptance_criteria" in story_dict
    assert story_dict["structured_acceptance_criteria"] == criteria
    assert len(story_dict["structured_acceptance_criteria"]) == 1
    assert story_dict["structured_acceptance_criteria"][0]["id"] == "ac-1"


def test_story_dev_notes_validation():
    """Test Story model dev_notes field validation."""
    # Test with valid dev_notes
    story = Story(
        id="test-story-dev-notes",
        title="Dev Notes Test Story",
        description="Story for testing dev_notes field",
        acceptance_criteria=["Should accept valid dev_notes"],
        epic_id="test-epic-1",
        dev_notes="This is a test dev note with technical context",
    )
    assert story.dev_notes == "This is a test dev note with technical context"

    # Test with None dev_notes (should be allowed)
    story_none = Story(
        id="test-story-dev-notes-none",
        title="Dev Notes None Test Story",
        description="Story for testing None dev_notes",
        acceptance_criteria=["Should accept None dev_notes"],
        epic_id="test-epic-1",
        dev_notes=None,
    )
    assert story_none.dev_notes is None

    # Test validation error for non-string dev_notes
    with pytest.raises(ValueError, match="Dev notes must be a string"):
        Story(
            id="test-story-dev-notes-invalid",
            title="Invalid Dev Notes Test Story",
            description="Story for testing invalid dev_notes",
            acceptance_criteria=["Should reject non-string dev_notes"],
            epic_id="test-epic-1",
            dev_notes=123,  # Invalid: not a string
        )

    # Test validation error for dev_notes that are too long
    long_dev_notes = "x" * 10001  # Exceeds 10000 character limit
    with pytest.raises(ValueError, match="Dev notes cannot exceed 10000 characters"):
        Story(
            id="test-story-dev-notes-too-long",
            title="Long Dev Notes Test Story",
            description="Story for testing overly long dev_notes",
            acceptance_criteria=["Should reject dev_notes that are too long"],
            epic_id="test-epic-1",
            dev_notes=long_dev_notes,
        )


def test_story_to_dict_includes_dev_notes():
    """Test Story model to_dict method includes dev_notes field."""
    dev_notes_content = "Technical context: Use JWT tokens with Redis session storage"
    story = Story(
        id="test-story-dev-notes-dict",
        title="Dev Notes Dict Test Story",
        description="Story for testing dev_notes in to_dict",
        acceptance_criteria=["Should include dev_notes in dict"],
        epic_id="test-epic-1",
        dev_notes=dev_notes_content,
    )

    story_dict = story.to_dict()

    assert "dev_notes" in story_dict
    assert story_dict["dev_notes"] == dev_notes_content


def test_story_comments_validation_empty_list():
    """Test Story model comments validation with empty list."""
    story = Story(
        id="test-story-comments-1",
        title="Valid Empty Comments",
        description="Story with valid empty comments",
        acceptance_criteria=["Should accept empty comments"],
        epic_id="test-epic-1",
        comments=[],
    )

    assert story.comments == []


def test_story_comments_validation_invalid_type():
    """Test Story model comments validation with invalid type."""
    with pytest.raises(ValueError, match="Comments must be a list"):
        Story(
            id="test-story-comments-2",
            title="Invalid Comments Type",
            description="Story with invalid comments type",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments="not a list",
        )


def test_story_comments_validation_valid_comment():
    """Test Story model comments validation with valid comment."""
    valid_comment = {
        "id": "comment-1",
        "author_role": "Developer Agent",
        "content": "This is a test comment",
        "timestamp": datetime.now(timezone.utc),
        "reply_to_id": None,
    }

    story = Story(
        id="test-story-comments-3",
        title="Valid Comments",
        description="Story with valid comments",
        acceptance_criteria=["Should accept valid comments"],
        epic_id="test-epic-1",
        comments=[valid_comment],
    )

    assert len(story.comments) == 1
    assert story.comments[0]["id"] == "comment-1"
    assert story.comments[0]["author_role"] == "Developer Agent"
    assert story.comments[0]["content"] == "This is a test comment"


def test_story_comments_validation_missing_required_fields():
    """Test Story model comments validation with missing required fields."""
    # Missing author_role
    invalid_comment = {
        "id": "comment-1",
        "content": "This is a test comment",
        "timestamp": datetime.now(timezone.utc),
        "reply_to_id": None,
    }

    with pytest.raises(ValueError, match="Comment at index 0 missing required fields"):
        Story(
            id="test-story-comments-4",
            title="Invalid Comments",
            description="Story with invalid comments",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments=[invalid_comment],
        )


def test_story_comments_validation_invalid_comment_structure():
    """Test Story model comments validation with invalid comment structure."""
    # Invalid comment structure - not a dict
    with pytest.raises(ValueError, match="Comment at index 0 must be a dictionary"):
        Story(
            id="test-story-comments-5",
            title="Invalid Comments Structure",
            description="Story with invalid comments structure",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments=["not a dict"],
        )


def test_story_comments_validation_duplicate_ids():
    """Test Story model comments validation with duplicate comment IDs."""
    duplicate_comments = [
        {
            "id": "comment-1",
            "author_role": "Developer Agent",
            "content": "First comment",
            "timestamp": datetime.now(timezone.utc),
            "reply_to_id": None,
        },
        {
            "id": "comment-1",  # Duplicate ID
            "author_role": "QA Agent",
            "content": "Second comment",
            "timestamp": datetime.now(timezone.utc),
            "reply_to_id": None,
        },
    ]

    with pytest.raises(ValueError, match="Comment id 'comment-1' is not unique"):
        Story(
            id="test-story-comments-6",
            title="Duplicate Comment IDs",
            description="Story with duplicate comment IDs",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments=duplicate_comments,
        )


def test_story_comments_validation_invalid_timestamp():
    """Test Story model comments validation with invalid timestamp."""
    invalid_comment = {
        "id": "comment-1",
        "author_role": "Developer Agent",
        "content": "This is a test comment",
        "timestamp": "not a datetime",  # Invalid timestamp
        "reply_to_id": None,
    }

    with pytest.raises(
        ValueError,
        match="Comment at index 0 timestamp string must be in valid ISO format",
    ):
        Story(
            id="test-story-comments-7",
            title="Invalid Timestamp",
            description="Story with invalid timestamp in comment",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments=[invalid_comment],
        )


def test_story_comments_validation_invalid_timestamp_type():
    """Test Story model comments validation with non-string/non-datetime timestamp."""
    invalid_comment = {
        "id": "comment-1",
        "author_role": "Developer Agent",
        "content": "This is a test comment",
        "timestamp": 12345,  # Invalid timestamp type (integer)
        "reply_to_id": None,
    }

    with pytest.raises(
        ValueError,
        match=(
            "Comment at index 0 timestamp field must be a datetime object "
            "or ISO format string"
        ),
    ):
        Story(
            id="test-story-comments-type",
            title="Invalid Timestamp Type",
            description="Story with invalid timestamp type in comment",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments=[invalid_comment],
        )


def test_story_comments_validation_invalid_reply_to_id():
    """Test Story model comments validation with invalid reply_to_id."""
    invalid_comment = {
        "id": "comment-1",
        "author_role": "Developer Agent",
        "content": "This is a test comment",
        "timestamp": datetime.now(timezone.utc),
        "reply_to_id": "",  # Empty string instead of None or valid ID
    }

    with pytest.raises(
        ValueError,
        match="Comment at index 0 reply_to_id must be None or a non-empty string",
    ):
        Story(
            id="test-story-comments-8",
            title="Invalid Reply To ID",
            description="Story with invalid reply_to_id in comment",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments=[invalid_comment],
        )


def test_story_comments_validation_with_reply_to_id():
    """Test Story model comments validation with valid reply_to_id."""
    valid_comments = [
        {
            "id": "comment-1",
            "author_role": "Developer Agent",
            "content": "Original comment",
            "timestamp": datetime.now(timezone.utc),
            "reply_to_id": None,
        },
        {
            "id": "comment-2",
            "author_role": "QA Agent",
            "content": "Reply to original comment",
            "timestamp": datetime.now(timezone.utc),
            "reply_to_id": "comment-1",
        },
    ]

    story = Story(
        id="test-story-comments-9",
        title="Valid Reply Comments",
        description="Story with valid reply comments",
        acceptance_criteria=["Should accept valid reply comments"],
        epic_id="test-epic-1",
        comments=valid_comments,
    )

    assert len(story.comments) == 2
    assert story.comments[0]["reply_to_id"] is None
    assert story.comments[1]["reply_to_id"] == "comment-1"


def test_story_comments_validation_unexpected_fields():
    """Test Story model comments validation with unexpected fields."""
    invalid_comment = {
        "id": "comment-1",
        "author_role": "Developer Agent",
        "content": "This is a test comment",
        "timestamp": datetime.now(timezone.utc),
        "reply_to_id": None,
        "unexpected_field": "unexpected_value",  # Unexpected field
    }

    with pytest.raises(ValueError, match="Comment at index 0 has unexpected fields"):
        Story(
            id="test-story-comments-10",
            title="Unexpected Fields",
            description="Story with unexpected fields in comment",
            acceptance_criteria=["Should fail validation"],
            epic_id="test-epic-1",
            comments=[invalid_comment],
        )


def test_story_to_dict_includes_comments():
    """Test Story model to_dict includes comments with proper serialization."""
    test_timestamp = datetime.now(timezone.utc)
    valid_comment = {
        "id": "comment-1",
        "author_role": "Developer Agent",
        "content": "This is a test comment",
        "timestamp": test_timestamp,
        "reply_to_id": None,
    }

    story = Story(
        id="test-story-comments-11",
        title="Test to_dict Comments",
        description="Story to test to_dict with comments",
        acceptance_criteria=["Should include comments in to_dict"],
        epic_id="test-epic-1",
        comments=[valid_comment],
    )

    story_dict = story.to_dict()

    assert "comments" in story_dict
    assert len(story_dict["comments"]) == 1
    assert story_dict["comments"][0]["id"] == "comment-1"
    assert story_dict["comments"][0]["author_role"] == "Developer Agent"
    assert story_dict["comments"][0]["content"] == "This is a test comment"
    # Check timestamp is serialized as ISO format
    assert story_dict["comments"][0]["timestamp"] == test_timestamp.isoformat()
    assert story_dict["comments"][0]["reply_to_id"] is None
