"""
TestDataFactory - Consistent test data creation across all test types.

Provides factory methods for creating epics, stories, and artifacts with proper relationships,
ensuring consistent test data setup for unit, integration, and E2E tests.
"""

import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from src.agile_mcp.models.epic import Epic
from src.agile_mcp.models.story import Story  
from src.agile_mcp.models.artifact import Artifact


class TestDataFactory:
    """Factory class for creating consistent test data across all test types."""
    
    def __init__(self, session: Session):
        """
        Initialize the test data factory.
        
        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session
        self._created_objects = []  # Track created objects for cleanup
    
    def create_epic(
        self,
        epic_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "Ready",
        **kwargs
    ) -> Epic:
        """
        Create a test epic with consistent defaults.
        
        Args:
            epic_id: Epic ID (generates UUID if not provided)
            title: Epic title (generates default if not provided)
            description: Epic description (generates default if not provided)
            status: Epic status (default: "Ready")
            **kwargs: Additional epic attributes
            
        Returns:
            Created Epic instance
        """
        if epic_id is None:
            epic_id = f"test-epic-{uuid.uuid4().hex[:8]}"
        
        if title is None:
            title = f"Test Epic {epic_id[-8:]}"
            
        if description is None:
            description = f"Test epic created by TestDataFactory for {epic_id}"
        
        epic = Epic(
            id=epic_id,
            title=title,
            description=description,
            status=status,
            **kwargs
        )
        
        self.session.add(epic)
        self._created_objects.append(epic)
        
        return epic
    
    def create_story(
        self,
        story_id: Optional[str] = None,
        epic_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        acceptance_criteria: Optional[List[str]] = None,
        status: str = "ToDo",
        **kwargs
    ) -> Story:
        """
        Create a test story with consistent defaults.
        
        Args:
            story_id: Story ID (generates UUID if not provided)
            epic_id: Epic ID to associate with (creates epic if not provided)
            title: Story title (generates default if not provided)
            description: Story description (generates default if not provided)
            acceptance_criteria: Acceptance criteria (generates default if not provided)
            status: Story status (default: "ToDo")
            **kwargs: Additional story attributes
            
        Returns:
            Created Story instance
        """
        if story_id is None:
            story_id = f"test-story-{uuid.uuid4().hex[:8]}"
        
        if epic_id is None:
            # Create a default epic if none provided
            epic = self.create_epic()
            self.session.commit()  # Commit epic before creating story
            epic_id = epic.id
        
        if title is None:
            title = f"Test Story {story_id[-8:]}"
            
        if description is None:
            description = f"Test story created by TestDataFactory for {story_id}"
            
        if acceptance_criteria is None:
            acceptance_criteria = [f"Story {story_id} should work correctly and meet test requirements"]
        
        story = Story(
            id=story_id,
            epic_id=epic_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            status=status,
            **kwargs
        )
        
        self.session.add(story)
        self._created_objects.append(story)
        
        return story
    
    def create_artifact(
        self,
        artifact_id: Optional[str] = None,
        story_id: Optional[str] = None,
        relation: str = "implementation",
        uri: Optional[str] = None,
        **kwargs
    ) -> Artifact:
        """
        Create a test artifact with consistent defaults.
        
        Args:
            artifact_id: Artifact ID (generates UUID if not provided)
            story_id: Story ID to associate with (creates story if not provided)
            relation: Artifact relation type (default: "implementation")
            uri: Artifact URI (generates default if not provided)
            **kwargs: Additional artifact attributes
            
        Returns:
            Created Artifact instance
        """
        if artifact_id is None:
            artifact_id = f"test-artifact-{uuid.uuid4().hex[:8]}"
        
        if story_id is None:
            # Create a default story if none provided
            story = self.create_story()
            self.session.commit()  # Commit story before creating artifact
            story_id = story.id
        
        if uri is None:
            uri = f"file:///test/artifacts/{artifact_id}.py"
        
        artifact = Artifact(
            id=artifact_id,
            story_id=story_id,
            relation=relation,
            uri=uri,
            **kwargs
        )
        
        self.session.add(artifact)
        self._created_objects.append(artifact)
        
        return artifact
    
    def create_complete_hierarchy(
        self,
        epic_count: int = 1,
        stories_per_epic: int = 2,
        artifacts_per_story: int = 1
    ) -> Dict[str, List[Any]]:
        """
        Create a complete test data hierarchy with epics, stories, and artifacts.
        
        Args:
            epic_count: Number of epics to create
            stories_per_epic: Number of stories per epic
            artifacts_per_story: Number of artifacts per story
            
        Returns:
            Dictionary with created objects organized by type
        """
        hierarchy = {
            "epics": [],
            "stories": [],
            "artifacts": []
        }
        
        for epic_idx in range(epic_count):
            epic = self.create_epic(
                epic_id=f"hierarchy-epic-{epic_idx}",
                title=f"Hierarchy Epic {epic_idx + 1}",
                description=f"Epic {epic_idx + 1} in test hierarchy"
            )
            hierarchy["epics"].append(epic)
            self.session.commit()  # Commit epic before creating stories
            
            for story_idx in range(stories_per_epic):
                story = self.create_story(
                    story_id=f"hierarchy-story-{epic_idx}-{story_idx}",
                    epic_id=epic.id,
                    title=f"Story {story_idx + 1} for Epic {epic_idx + 1}",
                    description=f"Story {story_idx + 1} in epic {epic_idx + 1}"
                )
                hierarchy["stories"].append(story)
                self.session.commit()  # Commit story before creating artifacts
                
                for artifact_idx in range(artifacts_per_story):
                    artifact = self.create_artifact(
                        artifact_id=f"hierarchy-artifact-{epic_idx}-{story_idx}-{artifact_idx}",
                        story_id=story.id,
                        uri=f"file:///hierarchy/epic{epic_idx}/story{story_idx}/artifact{artifact_idx}.py"
                    )
                    hierarchy["artifacts"].append(artifact)
        
        # Final commit for all artifacts
        self.session.commit()
        
        return hierarchy
    
    def create_test_scenario(self, scenario: str) -> Dict[str, Any]:
        """
        Create predefined test scenarios for common testing patterns.
        
        Args:
            scenario: Scenario name ("empty", "single_epic", "basic_workflow", "complex")
            
        Returns:
            Dictionary with scenario data and created objects
        """
        if scenario == "empty":
            return {"scenario": "empty", "objects": []}
        
        elif scenario == "single_epic":
            # Use unique ID to avoid conflicts in shared databases
            unique_suffix = uuid.uuid4().hex[:8]
            epic = self.create_epic(
                epic_id=f"single-epic-scenario-{unique_suffix}",
                title="Single Epic Scenario",
                description="Scenario with a single epic for testing"
            )
            self.session.commit()
            return {
                "scenario": "single_epic",
                "epic": epic,
                "objects": [epic]
            }
        
        elif scenario == "basic_workflow":
            # Use unique IDs to avoid conflicts in shared databases
            unique_suffix = uuid.uuid4().hex[:8]
            
            epic = self.create_epic(
                epic_id=f"workflow-epic-{unique_suffix}",
                title="Basic Workflow Epic",
                description="Epic for basic workflow testing"
            )
            self.session.commit()
            
            todo_story = self.create_story(
                story_id=f"workflow-todo-story-{unique_suffix}",
                epic_id=epic.id,
                title="ToDo Story",
                status="ToDo"
            )
            
            ready_story = self.create_story(
                story_id=f"workflow-ready-story-{unique_suffix}", 
                epic_id=epic.id,
                title="Review Story",
                status="Review"
            )
            
            inprogress_story = self.create_story(
                story_id=f"workflow-inprogress-story-{unique_suffix}",
                epic_id=epic.id,
                title="In Progress Story",
                status="InProgress"
            )
            
            self.session.commit()
            
            return {
                "scenario": "basic_workflow",
                "epic": epic,
                "stories": {
                    "todo": todo_story,
                    "ready": ready_story,
                    "inprogress": inprogress_story
                },
                "objects": [epic, todo_story, ready_story, inprogress_story]
            }
        
        elif scenario == "complex":
            return self.create_complete_hierarchy(
                epic_count=2,
                stories_per_epic=3,
                artifacts_per_story=2
            )
        
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
    
    def cleanup(self):
        """Clean up all created test objects."""
        # Delete in reverse order to handle foreign key constraints
        for obj in reversed(self._created_objects):
            try:
                self.session.delete(obj)
            except Exception:
                # Object may already be deleted or session may be closed
                pass
        
        try:
            self.session.commit()
        except Exception:
            # Session may be closed or in error state
            pass
        
        self._created_objects.clear()
    
    def get_created_objects(self) -> List[Any]:
        """
        Get list of all objects created by this factory.
        
        Returns:
            List of created database objects
        """
        return self._created_objects.copy()
    
    def count_created_objects(self) -> Dict[str, int]:
        """
        Get count of created objects by type.
        
        Returns:
            Dictionary with counts by object type
        """
        counts = {"Epic": 0, "Story": 0, "Artifact": 0}
        
        for obj in self._created_objects:
            if isinstance(obj, Epic):
                counts["Epic"] += 1
            elif isinstance(obj, Story):
                counts["Story"] += 1
            elif isinstance(obj, Artifact):
                counts["Artifact"] += 1
        
        return counts