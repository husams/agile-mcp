"""
FastMCP tools for Artifact management operations.
"""

import logging
from typing import Dict, Any, List
from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import get_db, create_tables
from ..repositories.artifact_repository import ArtifactRepository  
from ..services.artifact_service import ArtifactService
from ..services.exceptions import (
    ArtifactValidationError, 
    ArtifactNotFoundError, 
    StoryNotFoundError, 
    DatabaseError, 
    InvalidRelationTypeError
)


def register_artifact_tools(mcp: FastMCP) -> None:
    """Register artifact management tools with the FastMCP server."""
    
    logger = logging.getLogger(__name__)
    
    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    @mcp.tool("artifacts.linkToStory")
    def link_artifact_to_story(story_id: str, uri: str, relation: str) -> Dict[str, Any]:
        """
        Links a generated artifact to a user story for traceability.
        
        Args:
            story_id: The unique identifier of the story to link the artifact to
            uri: The Uniform Resource Identifier for the artifact (e.g., file:///path/to/code.js)
            relation: The relationship type between artifact and story ("implementation", "design", "test")
            
        Returns:
            Dict containing the created artifact's id, uri, relation, and story_id
            
        Raises:
            McpError: If validation fails, story not found, or database operation fails
        """
        try:
            db_session = get_db()
            try:
                artifact_repository = ArtifactRepository(db_session)
                artifact_service = ArtifactService(artifact_repository)
                
                artifact_dict = artifact_service.link_artifact_to_story(story_id, uri, relation)
                return artifact_dict
                
            finally:
                db_session.close()
                
        except ArtifactValidationError as e:
            raise McpError(ErrorData(code=-32001, message=f"Artifact validation error: {str(e)}", data={"story_id": story_id, "uri": uri, "relation": relation}))
        except InvalidRelationTypeError as e:
            raise McpError(ErrorData(code=-32001, message=f"Invalid relation type: {str(e)}", data={"story_id": story_id, "uri": uri, "relation": relation}))
        except StoryNotFoundError as e:
            raise McpError(ErrorData(code=-32001, message=f"Story not found: {str(e)}", data={"story_id": story_id, "uri": uri, "relation": relation}))
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}", data={"story_id": story_id, "uri": uri, "relation": relation}))
        except Exception as e:
            raise McpError(ErrorData(code=-32001, message=f"Unexpected error: {str(e)}", data={"story_id": story_id, "uri": uri, "relation": relation}))
    
    @mcp.tool("artifacts.listForStory")
    def list_artifacts_for_story(story_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all artifacts linked to a specific story.
        
        Args:
            story_id: The unique identifier of the story
            
        Returns:
            List of dicts, each containing an artifact's id, uri, relation, and story_id
            
        Raises:
            McpError: If validation fails or database operation fails
        """
        try:
            db_session = get_db()
            try:
                artifact_repository = ArtifactRepository(db_session)
                artifact_service = ArtifactService(artifact_repository)
                
                artifacts_list = artifact_service.get_artifacts_for_story(story_id)
                return artifacts_list
                
            finally:
                db_session.close()
                
        except ArtifactValidationError as e:
            raise McpError(ErrorData(code=-32001, message=f"Artifact validation error: {str(e)}", data={"story_id": story_id}))
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}", data={"story_id": story_id}))
        except Exception as e:
            raise McpError(ErrorData(code=-32001, message=f"Unexpected error: {str(e)}", data={"story_id": story_id}))