"""
End-to-end tests for backlog.getNextReadyStory via MCP JSON-RPC.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Epic, Base
from src.agile_mcp.models.story import Story
from src.agile_mcp.api.backlog_tools import register_backlog_tools
from src.agile_mcp.database import get_db, create_tables
from unittest.mock import patch, Mock


@pytest.fixture
def temp_database():
    """Create a temporary database file for E2E testing."""
    # Create a temporary file for the database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)  # Close the file descriptor
    
    # Create engine and session directly with the temp database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)  # This ensures all new columns are created
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Create test epic
        epic = Epic(
            id="e2e-epic-1",
            title="E2E Test Epic",
            description="Epic for E2E testing",
            status="Ready"
        )
        session.add(epic)
        session.commit()
        
        yield session, db_path
        
    finally:
        session.close()
    
    # Clean up the temporary file
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing tool registration."""
    mock_server = Mock()
    
    # Store registered tools
    mock_server.registered_tools = {}
    
    def mock_tool_decorator(tool_name):
        def decorator(func):
            mock_server.registered_tools[tool_name] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    
    return mock_server


class TestGetNextReadyStoryE2E:
    """End-to-end tests for getNextReadyStory tool."""
    
    def test_e2e_get_next_ready_story_with_complex_dependency_scenarios(
        self, temp_database, mock_mcp_server
    ):
        """Test complete E2E workflow with complex dependency scenarios."""
        session, db_path = temp_database
        
        base_time = datetime(2023, 1, 1, 12, 0, 0)
        
        # Create complex story hierarchy with dependencies
        # Story A (high priority) depends on Story B
        # Story B (medium priority) depends on Story C  
        # Story C (low priority) is ready
        # Story D (highest priority) is ready but should come after C->B->A chain
        
        story_a = Story(
            id="story-a-high-blocked",
            title="Story A - High Priority Blocked",
            description="High priority but blocked by Story B",
            acceptance_criteria=["Depends on Story B"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=8,
            created_at=base_time
        )
        
        story_b = Story(
            id="story-b-medium-blocked",
            title="Story B - Medium Priority Blocked", 
            description="Medium priority but blocked by Story C",
            acceptance_criteria=["Depends on Story C"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=5,
            created_at=base_time + timedelta(minutes=10)
        )
        
        story_c = Story(
            id="story-c-low-ready",
            title="Story C - Low Priority Ready",
            description="Low priority but ready to go",
            acceptance_criteria=["No dependencies"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=2,
            created_at=base_time + timedelta(minutes=20)
        )
        
        story_d = Story(
            id="story-d-highest-ready",
            title="Story D - Highest Priority Ready",
            description="Highest priority and ready",
            acceptance_criteria=["No dependencies, highest priority"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=10,
            created_at=base_time + timedelta(minutes=30)
        )
        
        # Add stories to database
        for story in [story_a, story_b, story_c, story_d]:
            session.add(story)
        session.commit()
        
        # Add dependencies using SQLAlchemy to ensure proper execution
        from src.agile_mcp.models.story_dependency import story_dependencies
        
        session.execute(
            story_dependencies.insert().values(
                story_id="story-a-high-blocked", 
                depends_on_story_id="story-b-medium-blocked"
            )
        )
        session.execute(
            story_dependencies.insert().values(
                story_id="story-b-medium-blocked", 
                depends_on_story_id="story-c-low-ready"
            )
        )
        session.commit()
        
        # Register tools with mock server
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            register_backlog_tools(mock_mcp_server)
        
        # Get the registered getNextReadyStory function
        get_next_ready_story_func = mock_mcp_server.registered_tools["backlog.getNextReadyStory"]
        assert get_next_ready_story_func is not None
        
        # Test 1: Should return Story D (highest priority, no dependencies)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result is not None
        assert result["id"] == "story-d-highest-ready"
        assert result["status"] == "InProgress"
        assert result["priority"] == 10
        
        # Test 2: Mark Story D as Done and get next ready story
        story_d_db = session.query(Story).filter(Story.id == "story-d-highest-ready").first()
        story_d_db.status = "Done"
        session.commit()
        
        # Should now return Story C (ready, no incomplete dependencies)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result is not None
        assert result["id"] == "story-c-low-ready"
        assert result["status"] == "InProgress"
        assert result["priority"] == 2
        
        # Test 3: Mark Story C as Done, now Story B should become ready
        story_c_db = session.query(Story).filter(Story.id == "story-c-low-ready").first()
        story_c_db.status = "Done"
        session.commit()
        
        # Should now return Story B (its dependency C is done)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result is not None
        assert result["id"] == "story-b-medium-blocked"
        assert result["status"] == "InProgress"
        assert result["priority"] == 5
        
        # Test 4: Mark Story B as Done, now Story A should become ready
        story_b_db = session.query(Story).filter(Story.id == "story-b-medium-blocked").first()
        story_b_db.status = "Done"
        session.commit()
        
        # Should now return Story A (its dependency B is done)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result is not None
        assert result["id"] == "story-a-high-blocked"
        assert result["status"] == "InProgress"
        assert result["priority"] == 8
        
        # Test 5: Mark Story A as Done, should return empty
        story_a_db = session.query(Story).filter(Story.id == "story-a-high-blocked").first()
        story_a_db.status = "Done"
        session.commit()
        
        # Should now return empty dict (no more stories)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result == {}
    
    def test_e2e_status_update_persistence(self, temp_database, mock_mcp_server):
        """Test that status updates are properly persisted in the database."""
        session, db_path = temp_database
        
        # Create a simple story
        story = Story(
            id="persistence-test-story",
            title="Persistence Test Story",
            description="Test status update persistence",
            acceptance_criteria=["Status should persist"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=1,
            created_at=datetime(2023, 5, 1, 10, 0, 0)
        )
        
        session.add(story)
        session.commit()
        
        # Register tools
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            register_backlog_tools(mock_mcp_server)
        
        get_next_ready_story_func = mock_mcp_server.registered_tools["backlog.getNextReadyStory"]
        
        # Call the tool
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        # Verify result
        assert result is not None
        assert result["id"] == "persistence-test-story"
        assert result["status"] == "InProgress"
        
        # Verify persistence by querying database directly
        persisted_story = session.query(Story).filter(Story.id == "persistence-test-story").first()
        assert persisted_story.status == "InProgress"
        
        # Verify that calling again returns empty (story is no longer ToDo)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result2 = get_next_ready_story_func()
        
        assert result2 == {}
    
    def test_e2e_interaction_with_existing_dependency_tools(
        self, temp_database, mock_mcp_server
    ):
        """Test interaction with existing dependency and story tools."""
        session, db_path = temp_database
        
        # Create stories
        base_time = datetime(2023, 7, 1, 14, 0, 0)
        
        story_1 = Story(
            id="interaction-story-1",
            title="Interaction Story 1",
            description="First story for interaction test",
            acceptance_criteria=["Should work with dependency tools"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=3,
            created_at=base_time
        )
        
        story_2 = Story(
            id="interaction-story-2",
            title="Interaction Story 2",
            description="Second story for interaction test",
            acceptance_criteria=["Should be blocked initially"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=5,
            created_at=base_time + timedelta(minutes=5)
        )
        
        session.add(story_1)
        session.add(story_2)
        session.commit()
        
        # Register tools
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            register_backlog_tools(mock_mcp_server)
        
        get_next_ready_story_func = mock_mcp_server.registered_tools["backlog.getNextReadyStory"]
        add_dependency_func = mock_mcp_server.registered_tools["backlog.addDependency"]
        
        # Initially, story 2 should be returned (higher priority)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result is not None
        assert result["id"] == "interaction-story-2"
        assert result["priority"] == 5
        
        # Reset story 2 to ToDo for dependency test
        story_2_db = session.query(Story).filter(Story.id == "interaction-story-2").first()
        story_2_db.status = "ToDo"
        session.commit()
        
        # Add dependency: story 2 depends on story 1
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            dep_result = add_dependency_func("interaction-story-2", "interaction-story-1")
        
        assert dep_result["status"] == "success"
        
        # Now story 1 should be returned instead (story 2 is blocked)
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result is not None
        assert result["id"] == "interaction-story-1"
        assert result["priority"] == 3
        
        # Complete story 1
        story_1_db = session.query(Story).filter(Story.id == "interaction-story-1").first()
        story_1_db.status = "Done"
        session.commit()
        
        # Now story 2 should become available
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result is not None
        assert result["id"] == "interaction-story-2"
        assert result["priority"] == 5
    
    def test_e2e_empty_response_handling(self, temp_database, mock_mcp_server):
        """Test E2E empty response when no stories are ready."""
        session, db_path = temp_database
        
        # Don't create any stories
        
        # Register tools
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            register_backlog_tools(mock_mcp_server)
        
        get_next_ready_story_func = mock_mcp_server.registered_tools["backlog.getNextReadyStory"]
        
        # Should return empty dict
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        assert result == {}
    
    def test_e2e_tool_response_format(self, temp_database, mock_mcp_server):
        """Test that the tool returns correctly formatted response."""
        session, db_path = temp_database
        
        # Create a story with all fields
        story = Story(
            id="format-test-story",
            title="Format Test Story",
            description="Test response format",
            acceptance_criteria=["Should return all fields", "Should be properly formatted"],
            epic_id="e2e-epic-1",
            status="ToDo",
            priority=7,
            created_at=datetime(2023, 9, 1, 16, 30, 0)
        )
        
        session.add(story)
        session.commit()
        
        # Register tools
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            register_backlog_tools(mock_mcp_server)
        
        get_next_ready_story_func = mock_mcp_server.registered_tools["backlog.getNextReadyStory"]
        
        # Call the tool
        with patch('src.agile_mcp.api.backlog_tools.get_db', return_value=session):
            result = get_next_ready_story_func()
        
        # Verify complete response format
        assert isinstance(result, dict)
        assert "id" in result
        assert "title" in result
        assert "description" in result
        assert "acceptance_criteria" in result
        assert "status" in result
        assert "priority" in result
        assert "created_at" in result
        assert "epic_id" in result
        
        # Verify specific values
        assert result["id"] == "format-test-story"
        assert result["title"] == "Format Test Story"
        assert result["description"] == "Test response format"
        assert result["acceptance_criteria"] == ["Should return all fields", "Should be properly formatted"]
        assert result["status"] == "InProgress"  # Should be updated
        assert result["priority"] == 7
        assert result["epic_id"] == "e2e-epic-1"
        assert isinstance(result["created_at"], str)  # Should be ISO format