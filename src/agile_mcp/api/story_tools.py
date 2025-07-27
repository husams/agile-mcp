"""
FastMCP tools for Story management operations.
"""

import logging
from typing import Dict, Any, List
from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import get_db, create_tables
from ..repositories.story_repository import StoryRepository
from ..services.story_service import StoryService
from ..services.exceptions import StoryValidationError, StoryNotFoundError, EpicNotFoundError, DatabaseError, InvalidStoryStatusError


def register_story_tools(mcp: FastMCP) -> None:
    """Register story management tools with the FastMCP server."""
    
    logger = logging.getLogger(__name__)
    
    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    @mcp.tool("backlog.createStory")
    def create_story(epic_id: str, title: str, description: str, acceptance_criteria: List[str]) -> Dict[str, Any]:
        """
        Create a new user story within a specific epic.
        
        Args:
            epic_id: The unique identifier of the parent epic
            title: A short, descriptive title (max 200 characters)
            description: The full user story text (max 2000 characters)
            acceptance_criteria: A list of conditions that must be met for the story to be considered complete
            
        Returns:
            Dict containing the created story's id, title, description, acceptance_criteria, status, and epic_id
            
        Raises:
            McpError: If validation fails, epic not found, or database operation fails
        """
        try:
            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)
                
                story_dict = story_service.create_story(title, description, acceptance_criteria, epic_id)
                return story_dict
                
            finally:
                db_session.close()
                
        except StoryValidationError as e:
            raise McpError(ErrorData(code=-32001, message=f"Story validation error: {str(e)}"))
        except EpicNotFoundError as e:
            raise McpError(ErrorData(code=-32001, message=f"Epic not found: {str(e)}"))
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            raise McpError(ErrorData(code=-32001, message=f"Unexpected error: {str(e)}"))
    
    @mcp.tool("backlog.getStory")
    def get_story(story_id: str) -> Dict[str, Any]:
        """
        Retrieve the full, self-contained details of a specified story.
        
        Args:
            story_id: The unique identifier of the story
            
        Returns:
            Dict containing the story's id, title, description, acceptance_criteria, status, and epic_id
            
        Raises:
            McpError: If story not found or database operation fails
        """
        try:
            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)
                
                story_dict = story_service.get_story(story_id)
                return story_dict
                
            finally:
                db_session.close()
                
        except StoryValidationError as e:
            raise McpError(ErrorData(code=-32001, message=f"Story validation error: {str(e)}"))
        except StoryNotFoundError as e:
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}", data={"story_id": story_id}))
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            raise McpError(ErrorData(code=-32001, message=f"Unexpected error: {str(e)}"))
    
    @mcp.tool("backlog.updateStoryStatus")
    def update_story_status(story_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of a user story to reflect current work state.
        
        Args:
            story_id: The unique identifier of the story
            status: The new status value ("ToDo", "InProgress", "Review", "Done")
            
        Returns:
            Dict containing the updated story's id, title, description, acceptance_criteria, status, and epic_id
            
        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        try:
            db_session = get_db()
            try:
                story_repository = StoryRepository(db_session)
                story_service = StoryService(story_repository)
                
                story_dict = story_service.update_story_status(story_id, status)
                return story_dict
                
            finally:
                db_session.close()
                
        except StoryValidationError as e:
            raise McpError(ErrorData(code=-32001, message=f"Story validation error: {str(e)}", data={"story_id": story_id, "status": status}))
        except InvalidStoryStatusError as e:
            raise McpError(ErrorData(code=-32001, message=f"Invalid status error: {str(e)}", data={"story_id": story_id, "status": status}))
        except StoryNotFoundError as e:
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}", data={"story_id": story_id, "status": status}))
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}", data={"story_id": story_id, "status": status}))
        except Exception as e:
            raise McpError(ErrorData(code=-32001, message=f"Unexpected error: {str(e)}", data={"story_id": story_id, "status": status}))