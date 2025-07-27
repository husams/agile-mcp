"""
FastMCP tools for backlog management operations.
"""

import logging
from typing import Dict, Any
from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import get_db, create_tables
from ..repositories.story_repository import StoryRepository
from ..repositories.dependency_repository import DependencyRepository
from ..services.story_service import StoryService
from ..services.dependency_service import DependencyService
from ..services.exceptions import (
    StoryValidationError, StoryNotFoundError, SectionNotFoundError, DatabaseError,
    DependencyValidationError, CircularDependencyError, DuplicateDependencyError
)


def register_backlog_tools(mcp: FastMCP) -> None:
    """Register backlog management tools with the FastMCP server."""
    
    logger = logging.getLogger(__name__)
    
    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    @mcp.tool("backlog.getStorySection")
    def get_story_section(story_id: str, section_name: str) -> Dict[str, Any]:
        """
        Retrieve a specific section from a story by its unique ID and section name.
        
        Args:
            story_id: The unique identifier of the story
            section_name: The name of the section to extract (e.g., "Acceptance Criteria", "Story", "Tasks / Subtasks")
            
        Returns:
            Dict containing the story_id, section_name, and content of the requested section
            
        Raises:
            McpError: If validation fails, story not found, section not found, or file operation fails
        """
        try:
            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)
                
                section_content = story_service.get_story_section(story_id, section_name)
                
                return {
                    "story_id": story_id,
                    "section_name": section_name,
                    "content": section_content
                }
                
            finally:
                db_session.close()
                
        except StoryValidationError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Story validation error: {str(e)}",
                data={"story_id": story_id, "section_name": section_name}
            ))
        except StoryNotFoundError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Story not found: {str(e)}",
                data={"story_id": story_id, "section_name": section_name}
            ))
        except SectionNotFoundError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Section not found: {str(e)}",
                data={"story_id": story_id, "section_name": section_name}
            ))
        except DatabaseError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Database error: {str(e)}",
                data={"story_id": story_id, "section_name": section_name}
            ))
        except Exception as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Unexpected error: {str(e)}",
                data={"story_id": story_id, "section_name": section_name}
            ))
    
    @mcp.tool("backlog.addDependency")
    def add_dependency(story_id: str, depends_on_story_id: str) -> Dict[str, Any]:
        """
        Add a dependency relationship between two stories.
        
        A dependency means that 'depends_on_story_id' must be completed before 'story_id' can be started.
        This tool prevents the creation of circular dependencies (e.g., Story A depends on B, and B depends on A).
        
        Args:
            story_id: The unique identifier of the story that will have the dependency
            depends_on_story_id: The unique identifier of the story that must be completed first
            
        Returns:
            Dict containing success status, story IDs, and confirmation message
            
        Raises:
            McpError: If validation fails, stories not found, circular dependency detected, or database operation fails
        """
        try:
            db_session = get_db()
            try:
                dependency_repository = DependencyRepository(db_session)
                dependency_service = DependencyService(dependency_repository)
                
                result = dependency_service.add_story_dependency(story_id, depends_on_story_id)
                
                return result
                
            finally:
                db_session.close()
                
        except DependencyValidationError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Dependency validation error: {str(e)}",
                data={"story_id": story_id, "depends_on_story_id": depends_on_story_id}
            ))
        except CircularDependencyError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Circular dependency error: {str(e)}",
                data={"story_id": story_id, "depends_on_story_id": depends_on_story_id}
            ))
        except DuplicateDependencyError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Duplicate dependency error: {str(e)}",
                data={"story_id": story_id, "depends_on_story_id": depends_on_story_id}
            ))
        except StoryNotFoundError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Story not found: {str(e)}",
                data={"story_id": story_id, "depends_on_story_id": depends_on_story_id}
            ))
        except DatabaseError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Database error: {str(e)}",
                data={"story_id": story_id, "depends_on_story_id": depends_on_story_id}
            ))
        except Exception as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Unexpected error: {str(e)}",
                data={"story_id": story_id, "depends_on_story_id": depends_on_story_id}
            ))
    
    @mcp.tool("backlog.getNextReadyStory")
    def get_next_ready_story() -> Dict[str, Any]:
        """
        Gets the next story that is ready for implementation.
        Returns the highest-priority ToDo story with no incomplete dependencies.
        Automatically updates the story status to InProgress.
        
        A story is ready if:
        - Status is "ToDo"
        - All stories it depends on have status "Done"
        
        Stories are ordered by:
        1. Priority (highest first)
        2. Created date (earliest first) for same priority
        
        Returns:
            Dict containing the story details if one is found, or empty dict if no stories are ready
            
        Raises:
            McpError: If database operation fails or service error occurs
        """
        try:
            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                dependency_repository = DependencyRepository(db_session)
                story_service = StoryService(story_repository, dependency_repository)
                
                story = story_service.get_next_ready_story()
                
                if story:
                    return story
                else:
                    return {}  # Empty dict when no stories ready
                    
            finally:
                db_session.close()
                
        except StoryValidationError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Story validation error: {str(e)}",
                data={}
            ))
        except DatabaseError as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Database error: {str(e)}",
                data={}
            ))
        except Exception as e:
            raise McpError(ErrorData(
                code=-32001,
                message=f"Unexpected error: {str(e)}",
                data={}
            ))