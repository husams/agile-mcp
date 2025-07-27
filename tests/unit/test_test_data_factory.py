"""
Unit tests for TestDataFactory to validate consistent test data creation.
"""

import pytest
from tests.utils.test_data_factory import DataFactory
from src.agile_mcp.models.epic import Epic
from src.agile_mcp.models.story import Story
from src.agile_mcp.models.artifact import Artifact


def test_create_epic(test_session):
    """Test epic creation with TestDataFactory."""
    factory = DataFactory(test_session)
    
    # Test with default values
    epic1 = factory.create_epic()
    assert epic1.id.startswith("test-epic-")
    assert "Test Epic" in epic1.title
    assert "TestDataFactory" in epic1.description
    assert epic1.status == "Ready"
    
    # Test with custom values
    epic2 = factory.create_epic(
        epic_id="custom-epic",
        title="Custom Epic",
        description="Custom description",
        status="Draft"
    )
    assert epic2.id == "custom-epic"
    assert epic2.title == "Custom Epic"
    assert epic2.description == "Custom description"
    assert epic2.status == "Draft"


def test_create_story(test_session):
    """Test story creation with TestDataFactory."""
    factory = DataFactory(test_session)
    
    # Test with auto-created epic
    story1 = factory.create_story()
    assert story1.id.startswith("test-story-")
    assert "Test Story" in story1.title
    assert "TestDataFactory" in story1.description
    assert isinstance(story1.acceptance_criteria, list)
    assert len(story1.acceptance_criteria) > 0
    assert "should work correctly" in story1.acceptance_criteria[0]
    assert story1.status == "ToDo"
    assert story1.epic_id is not None
    
    # Test with existing epic
    epic = factory.create_epic(epic_id="existing-epic")
    test_session.commit()
    
    story2 = factory.create_story(
        story_id="custom-story",
        epic_id="existing-epic",
        title="Custom Story",
        status="Review"
    )
    assert story2.id == "custom-story"
    assert story2.epic_id == "existing-epic"
    assert story2.title == "Custom Story"
    assert story2.status == "Review"


def test_create_artifact(test_session):
    """Test artifact creation with TestDataFactory."""
    factory = DataFactory(test_session)
    
    # Test with auto-created story
    artifact1 = factory.create_artifact()
    assert artifact1.id.startswith("test-artifact-")
    assert artifact1.uri.startswith("file:///test/artifacts/")
    assert artifact1.relation == "implementation"
    assert artifact1.story_id is not None
    
    # Test with existing story
    story = factory.create_story(story_id="existing-story")
    test_session.commit()
    
    artifact2 = factory.create_artifact(
        artifact_id="custom-artifact",
        story_id="existing-story",
        relation="design",
        uri="file:///custom/path.md"
    )
    assert artifact2.id == "custom-artifact"
    assert artifact2.story_id == "existing-story"
    assert artifact2.relation == "design"
    assert artifact2.uri == "file:///custom/path.md"


def test_create_complete_hierarchy(test_session):
    """Test creating complete data hierarchy."""
    factory = DataFactory(test_session)
    
    hierarchy = factory.create_complete_hierarchy(
        epic_count=2,
        stories_per_epic=2,
        artifacts_per_story=1
    )
    
    assert len(hierarchy["epics"]) == 2
    assert len(hierarchy["stories"]) == 4  # 2 epics * 2 stories
    assert len(hierarchy["artifacts"]) == 4  # 4 stories * 1 artifact
    
    # Verify relationships
    for story in hierarchy["stories"]:
        assert story.epic_id in [epic.id for epic in hierarchy["epics"]]
    
    for artifact in hierarchy["artifacts"]:
        assert artifact.story_id in [story.id for story in hierarchy["stories"]]


def test_create_test_scenarios(test_session):
    """Test predefined test scenarios."""
    factory = DataFactory(test_session)
    
    # Test empty scenario
    empty_scenario = factory.create_test_scenario("empty")
    assert empty_scenario["scenario"] == "empty"
    assert len(empty_scenario["objects"]) == 0
    
    # Test single epic scenario
    single_epic = factory.create_test_scenario("single_epic")
    assert single_epic["scenario"] == "single_epic"
    assert isinstance(single_epic["epic"], Epic)
    assert len(single_epic["objects"]) == 1
    
    # Test basic workflow scenario
    workflow = factory.create_test_scenario("basic_workflow")
    assert workflow["scenario"] == "basic_workflow"
    assert isinstance(workflow["epic"], Epic)
    assert len(workflow["stories"]) == 3
    assert workflow["stories"]["todo"].status == "ToDo"
    assert workflow["stories"]["ready"].status == "Review" 
    assert workflow["stories"]["inprogress"].status == "InProgress"
    
    # Test complex scenario
    complex_scenario = factory.create_test_scenario("complex")
    assert len(complex_scenario["epics"]) == 2
    assert len(complex_scenario["stories"]) == 6  # 2 epics * 3 stories
    assert len(complex_scenario["artifacts"]) == 12  # 6 stories * 2 artifacts


def test_factory_tracking(test_session):
    """Test that factory tracks created objects."""
    factory = DataFactory(test_session)
    
    initial_count = len(factory.get_created_objects())
    assert initial_count == 0
    
    # Create objects
    epic = factory.create_epic()
    story = factory.create_story()
    artifact = factory.create_artifact()
    
    # Check tracking - should have multiple objects due to auto-creation chains
    created_objects = factory.get_created_objects()
    assert len(created_objects) >= 5  # At least 5 objects (some auto-created in chains)
    
    # Check counts by type
    counts = factory.count_created_objects()
    assert counts["Epic"] >= 2  # At least 2 epics (1 explicit + auto-created ones)
    assert counts["Story"] >= 2  # At least 2 stories (1 explicit + auto-created ones)  
    assert counts["Artifact"] >= 1  # At least 1 artifact


def test_factory_cleanup(test_session):
    """Test factory cleanup functionality."""
    factory = DataFactory(test_session)
    
    # Create test data
    epic = factory.create_epic(epic_id="cleanup-test-epic")
    story = factory.create_story(story_id="cleanup-test-story")
    test_session.commit()
    
    # Verify data exists
    assert test_session.query(Epic).filter_by(id="cleanup-test-epic").first() is not None
    assert test_session.query(Story).filter_by(id="cleanup-test-story").first() is not None
    
    # Cleanup
    factory.cleanup()
    
    # Verify data is cleaned up
    assert test_session.query(Epic).filter_by(id="cleanup-test-epic").first() is None
    assert test_session.query(Story).filter_by(id="cleanup-test-story").first() is None
    
    # Verify tracking is cleared
    assert len(factory.get_created_objects()) == 0


def test_factory_error_handling(test_session):
    """Test factory error handling."""
    factory = DataFactory(test_session)
    
    # Test unknown scenario
    with pytest.raises(ValueError, match="Unknown scenario"):
        factory.create_test_scenario("unknown_scenario")
    
    # Test with None session (edge case)
    factory_with_none = DataFactory(None)
    with pytest.raises(AttributeError):
        factory_with_none.create_epic()


def test_factory_with_kwargs(test_session):
    """Test factory methods with valid Epic attributes."""
    factory = DataFactory(test_session)
    
    # Test epic with valid Epic attributes
    epic = factory.create_epic(
        epic_id="kwargs-epic",
        title="Custom Title"
    )
    
    # Should work with valid Epic attributes
    assert epic.id == "kwargs-epic"
    assert epic.title == "Custom Title"